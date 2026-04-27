# Microbiology LIMS POC — Ingestion & Retrieval Architecture

Companion to `microbio_lims_ingestion_retrieval.drawio` (two pages: Ingestion · Retrieval). Open in [app.diagrams.net](https://app.diagrams.net/) or the VS Code drawio extension; export to PNG/PDF/SVG for slides.

---

## Why this design

Clinical SOPs punish naive retrieval. They contain ICD/CPT/LOINC/SNOMED codes, organism names, regulatory citations, and frequent negation — content where pure dense (semantic) embeddings miss exact tokens, get fooled by `not` / `if` qualifiers, and confuse adjacent codes (e.g. `C50.911` vs `C50.912`). The architecture is built around three principles:

1. **Hybrid retrieval, not semantic-only.** BM25 (exact tokens, codes, citations) + Dense (paraphrase, intent) fused via Reciprocal Rank Fusion, with a cross-encoder reranker for precision.
2. **Theme-aware structure.** The 8 Cytology epic themes act as a *soft prior* through three vectors: a system-prompt taxonomy, an output-schema label, and per-theme retrieval slots that compose the final context.
3. **Grounded, cited generation.** Every retrieved chunk carries a citation back to its S3 source doc + section + version, so the generator's output is auditable.

---

## Page 1 — Ingestion Pipeline

### 1. Sources (S3)
SOPs, call scripts, transcripts, Cyto/Histo Jira exports, regulatory & standards docs all live in S3. New disciplines (Histology next, others later) plug in here without architectural change.

### 2. Trigger
S3 `PutObject` → SQS ingest queue (decouples bursts, enables retry). DLQ catches parse/OCR/embed failures. A separate manual re-index path supports config refreshes (e.g. theme definition changes) without re-uploading docs.

### 3. Parse
Format detection routes each doc to the right parser:
- **PDF (text layer)** — direct extract
- **Textract OCR (scanned)** — with code-OCR validation: any extracted ICD/CPT/LOINC/SNOMED code is checked against the canonical dictionary; mismatches are flagged rather than silently indexed
- **DOCX / DOC** — including comments and accepted track-changes
- **Transcripts** — TXT, VTT, SRT (timestamps preserved as metadata)
- **CSV / XLSX** — structured loading for Jira exports

### 4. Document processing (Haiku-assisted)
Each document gets:
- **Type & discipline classifier** — `{SOP, transcript, jira_export, regulatory, …}` × `{Cytology, Microbiology, Histology, …}`. Ambiguous cases route to human review rather than guessing.
- **Version & supersession** — content-hash dedupe; new versions of the same doc form a chain (old marked inactive, retained for audit, never hard-deleted).
- **SOP section parser** — Purpose, Scope, Procedure, Acceptance Criteria, QC, References. Section name becomes chunk metadata, enabling section-aware retrieval later (e.g. "give me ACs for X" preferentially pulls AC sections).
- **Metadata extraction** — date, source path, author, effective date.

### 5. Chunk
Structure-aware: chunks are bounded by section, split at semantic boundaries (sentence/paragraph), tables are kept whole when possible, and numbered procedure steps are not separated. Each chunk inherits its parent doc and section as metadata.

### 6. Enrich (parallel)
- **Code expansion** — `C50.911` is indexed alongside its expanded form *malignant neoplasm of nipple and areola, right female breast*. Both raw and enriched forms are indexed, so exact-code queries hit the literal token via BM25, and natural-language queries hit the expanded form via dense.
- **Clinical NER** — AWS Comprehend Medical extracts organisms, drugs, specimens, instruments, regulatory references; stored as faceted metadata for hard filtering (e.g. "must mention organism X").
- **PHI detection & redaction** — SOPs shouldn't carry PHI but transcripts can. Detected PHI is redacted before indexing; restricted-route option for stricter handling.
- **Theme tagger** — rules pre-filter (keyword patterns per theme); ambiguous chunks go to a small Haiku call for multi-label theme classification with confidence. Low-confidence chunks tagged `unclassified` for SME review rather than mis-bucketed.

### 7. Embed
- **Dense** — Bedrock Titan v2 or Cohere embed (general-purpose, hybrid stack carries the precision so we don't need a clinical-tuned embedder for v1).
- **Sparse (BM25)** — both raw and code-expanded text indexed.

### 8. Store
- **Vector index** (OpenSearch k-NN)
- **Sparse index** (OpenSearch BM25)
- **Chunk metadata** (DynamoDB) — entities, theme tags, section, version, confidence
- **Doc registry** (DynamoDB) — supersession chain, effective date, status
- **Original docs** (S3) — source of truth, citation target

### Config / Priors (right sidebar)
Refreshable independently of the corpus:
- **8 theme definitions + Micro direction + exemplar phrases** — drives theme tagging at ingestion *and* centroid-based intent decode at retrieval
- **Code dictionaries** (UMLS, ICD-10, CPT, LOINC, SNOMED, organism / drug lexicons)
- **SOP section taxonomy** — canonical section names + regex patterns
- **8 theme centroid embeddings** — precomputed once, consumed by retrieval

### Cross-cutting
KMS at-rest + in-transit encryption · DLQ for failure handling · IAM scoping + VPC endpoints · CloudWatch metrics & alarms · CloudTrail audit log.

---

## Page 2 — Retrieval Pipeline (per query)

### 1. Input
User query + session state (artifacts, drafts, refs the user can mention by index like "epic 3"). The diagram also shows ingestion-side configs that retrieval consumes (theme centroids, theme defs, code dictionary).

### 2. Pre-process
Normalize, language detect, extract embedded references (`@SOP-MICRO-005`, `epic 3`, `the previous one`).

### 3. Intent decode
Three parallel components:
- **Centroid similarity** — embed the query, cosine against the 8 theme centroids → soft theme distribution. Cheap, no LLM call. Acts as a prior/sanity check.
- **Haiku structured classifier** — returns `{action, themes[], discipline, granularity, refs, confidence}`. Sees the centroid distribution as a hint to reduce drift on out-of-distribution phrasing.
- **Co-reference resolver** — turns `epic 3` / `the previous one` into concrete session-state ids.

A **decision gate** (yellow) routes:
- **Proceed** — confidence ≥ τ AND action ∈ {generate, expand, compare, ask, edit} → continue to expansion + retrieval
- **Clarify** — low confidence → ask user a disambiguating question, do not retrieve
- **Session-only** — `recall` / `edit on draft` → bypass corpus retrieval, hit session store directly

### 4. Expand
- **Paraphrase + synonym expansion** — UMLS-aware, multi-query
- **Code & entity expansion** — codes in the query are expanded the same way they were at ingestion, so both views match

### 5. Multi-slot retrieval
The architectural lever that turns "RAG" into structured reasoning over a typed corpus. Each slot runs hybrid retrieval (BM25 + Dense → RRF) with its own filter:

| Slot | Filter | Top-K | Conditional |
|---|---|---|---|
| **1 — In-theme target** | discipline = Micro, theme ∈ active | 20 | always |
| **2 — Cyto analogy** | discipline = Cyto, theme ∈ active | 10 | always — "adapt, don't copy" |
| **3 — Adjacent themes** | discipline = Micro, theme ∈ neighbors-by-centroid | 10 | always |
| **4 — Jira exemplars** | doc_type = jira_export | 5 | only when action=generate ∧ granularity=epic |
| **5 — Regulatory** | doc_type = regulatory | 3 | only when active themes ∈ {G5 Quality / Compliance} |

Each slot's chunks enter the prompt with a *role label* (PRIMARY · ANALOGY · ADJACENT · EXEMPLAR · REG), so the model knows what each chunk is *for* — Cyto chunks aren't mistaken for Micro source-of-truth.

### 6. Rerank
Cross-encoder reranker (Cohere Rerank or Claude Haiku as a reranker) per slot → top-K trimmed. A **low-score gate** catches the case where every slot's top scores are below threshold θ — instead of producing ungrounded output, the system flags "no relevant content," broadens & retries, or refuses. This is the antidote to confident-sounding hallucination on out-of-corpus queries.

### 7. Assemble
- **Dedupe** — same chunk hit by multiple slots → keep highest score, note multi-slot membership
- **Token-budget trim** — drop lowest-priority slot first (slot 5, then 4, then 3) before trimming within slots
- **Role-labeled context** — slot labels carry into the prompt
- **Prepend** — 8-theme prior, session context, output schema (epic / story shape)

### 8. Output
- **→ Generation layer** — LLM call with structured-output schema; citations resolve to S3 doc + section + version
- **→ Telemetry** — query, intent decode, slot scores, final context, latency. This is the eval signal that lets us improve retrieval over time without flying blind.

---

## Key edge cases the architecture handles

| Edge case | Where it's handled |
|---|---|
| Encrypted / corrupt PDF | Parse stage → DLQ |
| OCR-corrupted clinical code | Parse → code-OCR validation → flag |
| Ambiguous discipline classification | Doc processing → human review queue |
| New version of an existing SOP | Doc processing → supersession chain (soft-delete prior) |
| Chunk spans multiple themes | Theme tagger → multi-label with confidence |
| Chunk has no clear theme | Theme tagger → `unclassified` for SME review |
| PHI in transcript | Enrich → detection + redaction (or restricted route) |
| Empty / chitchat query | Pre-process / intent decode → canned response |
| Low-confidence intent | Decision gate → clarifying question |
| "Epic 3" / "the previous one" | Co-reference resolver → session id |
| Code-only query | Expand → sparse-only path |
| All slots return weak chunks | Rerank low-score gate → "no relevant content" / retry / refuse |
| Token budget exceeded | Assemble → drop lowest-priority slot first |
| Theme imbalance in generation (e.g. all output is G8 Platform) | Generator runs theme-decomposed loop (downstream — not in this diagram) |

---

## Decisions to ratify with stakeholders

1. **Reranker yes/no for v1** — adds ~200ms latency and modest cost, but is the single biggest precision lever for negation-sensitive clinical content. Recommend yes.
2. **Theme tagging at ingest — rules vs. Haiku vs. hybrid.** Hybrid (rules first, Haiku for ambiguous) — best precision/cost balance. Re-classify only when theme definitions change.
3. **Multi-slot shape** — 5 slots with conditional 4 and 5. Could compress to 3 for v1 if simplicity is preferred; recommend keeping 5 because cross-discipline analogy (Slot 2) is what makes this a *Cyto-anchored* generator rather than a generic SOP-to-Jira tool.
4. **Confidence thresholds τ (intent) and θ (rerank)** — tunable; recommend instrumenting telemetry from day 1 so we can pick from data rather than guess.
5. **PHI handling policy** — redact-and-index vs. restricted-route vs. refuse. Needs a compliance call before code is written.

---

## Open questions for the next session

- Concrete component diagram on AWS (Bedrock Knowledge Bases vs. roll-our-own OpenSearch + ingestion Lambdas)
- Generation layer design — theme-decomposed planning loop, structured output schema for epic/story
- SME feedback capture surface — thumbs / edit / reject signal flowing back into retrieval & prompt iteration
- Eval harness — golden query set, retrieval-quality metrics (recall@K by slot, citation faithfulness)

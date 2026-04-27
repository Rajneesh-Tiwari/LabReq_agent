# Microbiology LIMS POC — Glossary & Examples

Companion to `microbio_lims_ingestion_retrieval.drawio`. Every term and block in the diagrams is defined here in plain language with a Microbiology / Labcorp example.

---

## Part A — Foundational concepts that recur throughout

These are the building blocks. Read this section first; the per-stage definitions below assume you know these.

### A.1 Embedding (a.k.a. "vector representation")
A way of turning a piece of text into a list of numbers (typically 1024 of them) such that texts with similar meaning end up with similar numbers. You can then compare two texts by comparing their number lists. There are two flavors that matter for us:

- **Dense embedding** — the number list is small (1024-ish) and every position has a non-zero value. Good at *meaning* similarity. *"What gets bounced at intake?"* and *"specimen rejection criteria"* end up with similar dense embeddings even though they share no words.
- **Sparse embedding** — the number list is huge (one position per word in the vocabulary) but mostly zero. Good at *exact-token* similarity. The classic algorithm is **BM25** (see below). It's what catches `C50.911` and `Mycobacterium tuberculosis` exactly.

We use **both** ("hybrid retrieval") because each catches what the other misses.

### A.2 BM25
A scoring formula that ranks documents by how many of the query's exact words appear, weighted by how rare each word is. It's the same idea search engines used before deep learning. We use it because clinical codes like `C50.911`, organism names like `Mycobacterium tuberculosis`, and regulatory citations like `CLIA §493.1252` need to match *exactly* — and BM25 is excellent at that.

### A.3 Vector index / k-NN
A specialized database that stores dense embeddings and answers the question *"give me the K stored items whose embeddings are most similar to this query embedding."* "k-NN" = k-nearest neighbors. AWS OpenSearch supports this natively.

### A.4 Cosine similarity
A way of measuring how similar two embeddings are: 1.0 = identical, 0 = unrelated. It's the standard yardstick for dense embeddings.

### A.5 RRF — Reciprocal Rank Fusion
A simple, robust way of combining rankings from two different rankers (here: BM25 and dense). Instead of trying to make BM25 scores and dense scores comparable (they aren't), RRF just looks at *what rank each item got* in each list and combines those. If a chunk is rank 2 in BM25 and rank 3 in dense, RRF scores it as 1/(60+2) + 1/(60+3) and ranks accordingly. Why we use it: it works without tuning, and it doesn't get fooled by one ranker producing wildly different score scales.

### A.6 Cross-encoder reranker
A second pass that looks at the query and one candidate chunk *together*, and scores how relevant the chunk is to that specific query. It's slower than the first-pass retrieval (you can't precompute it; it has to run per query × per candidate), but much more accurate — and crucially, it's the one component that handles negation well. We run it on the top-50 from first-pass and trim to top-8. AWS supports Cohere Rerank natively, or we can use Claude Haiku as a reranker.

### A.7 Centroid (in embedding space)
The "center of mass" of a group of embeddings. If we embed the description of theme G1 (Pre-Analytic / Specimen Management) plus a few example phrases for that theme, then average those embeddings, we get one vector that *represents* G1. Doing this for all 8 themes gives us 8 centroids. Now any query can be cosine-compared against those 8 centroids, and we instantly know which theme(s) the query is closest to — no LLM call needed.

### A.8 RAG — Retrieval-Augmented Generation
The pattern: when the LLM is asked a question, first *retrieve* relevant snippets from a corpus, *augment* the prompt with them, then *generate* the answer. It grounds the LLM in real source material instead of its parametric memory. Our entire system is RAG, with Cytology + Microbiology corpora as the retrieval source and Jira-shaped output as the generation target.

### A.9 Chunk / chunking
Documents are too long to fit in a prompt or embed as a single unit. We split them into "chunks" (typically 200–500 tokens each) and treat each chunk as an indexable unit. *Structure-aware* chunking means we respect document boundaries (sections, table rows, numbered procedure steps) instead of cutting arbitrarily every N characters.

### A.10 Multi-label classification
Most classifiers pick one label per item. Multi-label means each item can have several labels with confidence scores. A chunk about "automated analyzer QC run" legitimately belongs to both **G5 Quality** and **G7 Instrumentation** — multi-label captures that.

### A.11 DLQ — Dead-Letter Queue
A holding pen for messages that failed to process even after retries. Doesn't crash the pipeline; flagged for human review. Standard AWS pattern.

### A.12 Idempotent
"Doing it twice has the same effect as doing it once." A common bug: re-uploading the same SOP creates duplicate chunks. We make ingestion idempotent by hashing the file content — the second upload is detected and skipped.

### A.13 AWS services that appear in the diagram
| Service | What it is |
|---|---|
| **S3** | Object storage — where the SOPs and original docs live |
| **SQS** | Managed message queue — buffers ingestion work between S3 events and the processing workers |
| **DynamoDB** | Managed NoSQL database — fast key-value / document storage; we use it for chunk and doc metadata |
| **OpenSearch** | Search engine that supports both BM25 and k-NN vector search natively |
| **Bedrock** | AWS's managed access to LLMs including Claude and Titan embeddings — IAM-authed, stays in your AWS account |
| **Comprehend Medical** | AWS managed clinical NER + PHI detection — pre-trained on medical text |
| **Textract** | AWS managed OCR for scanned PDFs and forms |
| **Lambda** | Run small chunks of code in response to events (e.g., S3 PutObject) without managing servers |
| **IAM** | Access control — which service / user can do what |
| **KMS** | Key Management Service — encryption keys for at-rest data |
| **VPC** | Virtual Private Cloud — network isolation; "VPC endpoints" let services talk to Bedrock / S3 without traffic leaving the AWS network |
| **CloudWatch** | Metrics, logs, alarms |
| **CloudTrail** | Audit log of every API call made in the AWS account |

---

## Part B — Ingestion Pipeline (page 1)

### Stage 1 — Sources (S3)

The corpus that feeds the system. Everything starts here; new docs landing in these S3 buckets trigger the rest of the pipeline.

| Block | What it is | Example |
|---|---|---|
| **SOPs · workflow docs** | Standard Operating Procedures — Labcorp's authoritative documents for how a lab process is performed. Workflow docs describe the end-to-end flow across systems and people. | `SOP-MICRO-014_Gram-Stain_v3.docx` — defines slide preparation, staining steps, QC, acceptance criteria, escalation |
| **Call scripts** | Scripts customer service / client-services use when handling phone inquiries (e.g., what to say when a physician calls about a flagged result). Often capture rules that aren't written down anywhere else. | "If caller asks about MRSA susceptibility, confirm specimen ID, look up CLSI breakpoints…" |
| **Transcripts** | Recorded-and-transcribed conversations — training calls, internal meetings, SME interviews. Rich source of tribal knowledge. | Transcript of a microbiology lead explaining why Mycobacterium cultures need a 6-week incubation window |
| **Jira exports (Cyto / Histo)** | The existing Cytology and Histology Jira: the 71 Cyto epics and their stories/tasks, plus Histo if available. This is what gives the generator a sense of *shape* — what an epic looks like, how stories decompose. | A CSV row: `epic="Specimen Rejection Workflow", description="...", labels=["G1","Cytology"], stories=[...]` |
| **Regulatory & standards** | External documents the SOPs reference — CLIA, CAP, CLSI breakpoint tables, ICD-10 official guidance. | CLSI M100 *Performance Standards for Antimicrobial Susceptibility Testing* — the reference for AST breakpoints |

### Stage 2 — Trigger

| Term | Plain English |
|---|---|
| **S3 PutObject event** | When a new file is uploaded to S3, AWS automatically fires a notification. We catch this notification — it's how the pipeline knows a doc arrived without polling. |
| **SQS ingest queue** | A queue that buffers doc-arrival events. Decouples bursts (someone uploads 50 SOPs at once) from steady processing capacity. Also gives us retry logic for free. |
| **Retry · DLQ on retry exhaust** | If a doc fails to process, SQS retries 3× automatically. After that, it goes to the DLQ for human inspection. We don't lose work, we don't crash the system. |
| **Idempotent via content-hash** | We compute a hash of the file content and check if we've already processed an identical file. If yes, skip. Prevents duplicate indexing. |

### Stage 3 — Parse

Turning whatever format the doc arrived in into clean text we can work with.

| Block | What it does | Example |
|---|---|---|
| **Format detection & router** | Looks at the file (extension + content sniffing) and picks the right parser. PDF text vs. scanned image vs. DOCX vs. spreadsheet are all handled differently. | Sees `.pdf`, peeks inside — has a text layer? → PDF parser. No text layer? → OCR. |
| **PDF (text layer)** | Most PDFs have actual text underneath. We extract it directly — fast and accurate. | Pulls "Procedure: 1. Apply specimen…" verbatim from a digital SOP |
| **Textract OCR (scanned)** | Some SOPs are scans of printed-and-signed paper. AWS Textract reads the pixels and produces text. | `MICRO-009_Bench_Form_scanned.pdf` → recognized text, including the table layout |
| **Code-OCR validation** | OCR sometimes garbles codes — `C50.911` becomes `C5O.91l` (letter O for zero, letter l for one). We check every extracted code against the canonical dictionary; mismatches are flagged for human review instead of silently indexed wrong. | Sees `C5O.91l`, no such code exists → flagged |
| **DOCX / DOC** | Microsoft Word format. We extract paragraphs, headings, tables, comments, and accepted track-changes. | Pulls the section structure cleanly because Word stores headings as styled |
| **Transcripts (TXT / VTT / SRT)** | Plain text or subtitle formats. VTT/SRT carry timestamps which we preserve as metadata. | `interview_2024-08-14.vtt` → text + timestamps so we can cite "speaker said X at 14:32" |
| **CSV / XLSX (Jira)** | Structured tabular data, often Jira exports. Each row = one epic or story. | Reads the Jira CSV column-by-column, treats each row as one ingestible record |

### Stage 4 — Doc Processing (Haiku-assisted)

Once we have clean text, we extract document-level information.

| Term | Plain English | Example |
|---|---|---|
| **Type + discipline classifier** | Decides what kind of doc this is and which lab discipline it belongs to. Uses Claude Haiku (small, fast LLM) to read the first ~1k tokens and classify. Falls back to "human review" when ambiguous. | First page mentions "Microbiology" + "Gram stain" + numbered procedure → `{type: SOP, discipline: Microbiology}` |
| **Version & supersession** | Detects that this is a newer version of a doc we've already indexed (e.g., `SOP-MICRO-014_v3` superseding `_v2`). Marks the old version as inactive but keeps it for audit. | New `_v3` arrives → registry links it as the successor of `_v2`; retrieval defaults to v3 but auditors can still see v2 |
| **Content-hash dedupe** | Same doc renamed and re-uploaded? Same hash → we skip the duplicate. | `SOP-MICRO-014_FINAL.docx` and `SOP-MICRO-014_FINAL_copy.docx` have identical content → second one is detected and ignored |
| **SOP section parser** | Identifies standard SOP sections by their headings + regex patterns. Each section is preserved as metadata so retrieval can later prefer "Procedure" sections for workflow questions and "Acceptance Criteria" for AC questions. | Detects: `Purpose`, `Scope`, `Responsibilities`, `Procedure (steps 1–14)`, `Acceptance Criteria`, `Quality Control`, `References` |
| **Metadata extraction** | Author, effective date, document number, source S3 path. Stored alongside the doc so we can cite and filter. | `{doc_no: SOP-MICRO-014, effective: 2024-08-15, author: J. Smith, path: s3://lab-sops/micro/...}` |

### Stage 5 — Chunk

| Term | Plain English | Why it matters |
|---|---|---|
| **Structure-aware chunker** | Splits the doc into ~200–500 token pieces, but respecting document structure rather than cutting at arbitrary character counts. | A naive chunker might cut step 4 of a procedure off from step 5; structure-aware keeps numbered steps together |
| **Section-bounded** | A chunk never crosses a section boundary. The "Procedure" section's chunks are tagged Procedure; the "Acceptance Criteria" section's are tagged AC. | Lets retrieval prefer AC chunks when the user asks for acceptance criteria |
| **Semantic boundaries** | Within a section, we split at sentence/paragraph boundaries, not mid-sentence. | Prevents a chunk from starting "…and then incubate at 35°C." with no context |
| **Tables preserved** | A table is kept whole when it fits, or split row-group-by-row-group with the header repeated. SOP tables (e.g., specimen rejection criteria) carry critical info that's destroyed if you chunk naively. | The "Specimen Rejection Reasons" table stays as one unit so retrieval surfaces all reasons together |
| **Procedure steps grouped** | Numbered procedure steps stay together up to the chunk-size limit, with a header repeated when split. | Steps 1–7 in one chunk; if step 8–14 spill, the chunk gets a "Procedure (continued)" header |

### Stage 6 — Enrich (parallel)

Each chunk passes through four parallel processes that add information.

| Block | Plain English | Example |
|---|---|---|
| **Code expansion (ICD · CPT · LOINC · SNOMED)** | Detects clinical codes in the chunk and looks up their human-readable description. Both forms — the raw code AND the expanded text — are indexed. So `C50.911` (code) and *malignant neoplasm of nipple and areola, right female breast* (description) both retrieve the same chunk. | Chunk contains `Order: 87186` → indexed as `87186` AND `87186 (Susceptibility studies, antimicrobial agent; minimum inhibitory concentration, Kirby-Bauer)` |
| **UMLS lookup** | UMLS = Unified Medical Language System — the NIH's master dictionary of clinical codes and terminology. We use it to map codes to descriptions and find synonyms. | Looks up `87186` in UMLS → returns canonical name + synonyms |
| **Raw + enriched indexed** | Every chunk is stored twice in the sparse index: once with raw text (for exact-code matching), once with code expansions inline (for natural-language matching). | Both `C50.911` and "right female breast malignancy" find the chunk |
| **Clinical NER (Comprehend Medical)** | NER = Named Entity Recognition. AWS Comprehend Medical reads the chunk and extracts structured entities: organisms, drugs, specimens, instruments, regulatory citations. These become *facets* on the chunk — searchable filters. | Chunk → `{organisms: ["Mycobacterium tuberculosis"], drugs: ["isoniazid","rifampin"], specimens: ["sputum"], instruments: ["MGIT 960"], regs: ["CLIA §493.1252"]}` |
| **Faceted metadata** | Structured fields stored alongside each chunk that can be used as hard filters. "Show me only chunks that mention organism X." | Filter `organisms contains "Mycobacterium tuberculosis"` returns just the relevant chunks |
| **PHI detection & redaction** | PHI = Protected Health Information. AWS Comprehend Medical can detect names, MRNs, dates of birth, etc. We redact them before indexing — replace with `[NAME]`, `[MRN]`. SOPs shouldn't contain PHI but transcripts can. | "Patient John Smith, MRN 123456, was seen…" → "Patient [NAME], MRN [MRN], was seen…" |
| **Theme tagger (rules → Haiku fallback)** | Tags the chunk with which of the 8 themes it relates to. Tries cheap keyword rules first (e.g., G7 keywords: "analyzer", "calibration", "interface"); if rules are weak/conflicting, asks Claude Haiku to classify. Multi-label, with confidence. | Chunk about "automated MIC analyzer QC run procedure" → `{themes: [{G5: 0.85}, {G7: 0.72}], method: haiku}` |
| **Multi-label · confidence · G1–G8 (+ unclassified)** | Each chunk can carry multiple themes with confidence scores. Chunks the tagger isn't sure about go to `unclassified` for SME review rather than being mis-bucketed. | Below-threshold confidence → `theme: unclassified, review_queue: true` |

### Stage 7 — Embed

| Term | Plain English |
|---|---|
| **Hybrid embedding** | Compute *both* a dense embedding and a sparse representation for each chunk. We store both and use them together. |
| **Dense (Bedrock Titan v2 / Cohere embed)** | The chunk's text is sent to a Bedrock-hosted embedding model that returns a 1024-dimensional vector capturing meaning. Titan is AWS-native; Cohere embed-v3 is also available on Bedrock. |
| **Sparse tokenizer (BM25, raw + enriched)** | The chunk's text is tokenized for BM25 indexing — broken into words, stemmed, stop-words handled. We do this on both the raw text and the code-expanded version. |

### Stage 8 — Store

| Block | Plain English | What it holds |
|---|---|---|
| **Vector index (OpenSearch k-NN)** | Stores dense embeddings; answers "which chunks have embeddings nearest to this query embedding?" | One row per chunk: `{chunk_id, embedding_vector, doc_id, theme, ...}` |
| **Sparse index (OpenSearch BM25)** | Stores the BM25-tokenized text; answers "which chunks contain these exact words?" | One row per chunk: tokenized text + scoring statistics |
| **Chunk metadata (DynamoDB)** | The structured side-info per chunk that's used for filtering and citation. | `{chunk_id, doc_id, section, version, theme_tags, entities (organisms/drugs/specimens), phi_status, confidence}` |
| **Doc registry (DynamoDB)** | Document-level info — which SOP, which version, when effective, what it superseded, status (active/inactive). | `{doc_id, type, discipline, version, effective_date, supersedes, status}` |
| **Original docs (S3)** | The source-of-truth files. Citations from generated epics resolve back to here so an SME can read the original. | `s3://lab-sops/micro/SOP-MICRO-014_v3.pdf` |

### Config / Priors sidebar

These are *configuration inputs* to ingestion, not outputs. They shape how ingestion behaves and can be refreshed without re-uploading any docs.

| Block | Plain English | Used by |
|---|---|---|
| **8 theme definitions + Micro direction + exemplar phrases** | The 8 Cytology themes you identified, plus your "expands 4–5x", "shrinks to 15%" hints per theme, plus a few example phrases per theme that a chunk in that theme tends to contain. | Theme tagger (stage 6) |
| **Code dictionaries (UMLS · ICD · CPT · LOINC · SNOMED)** | The reference tables of clinical codes. ICD-10 = diagnosis codes. CPT = procedure codes. LOINC = lab test codes. SNOMED = clinical terminology. UMLS bundles many of these together. | Code expansion (stage 6) |
| **Organism / drug lexicons** | Curated lists of organism names and drug names so the NER + sparse index recognize them as named entities even when novel. | Clinical NER (stage 6) |
| **SOP section taxonomy** | The canonical list of SOP section names ("Purpose", "Procedure", "Acceptance Criteria" …) plus regex patterns to detect them. | Section parser (stage 4) |
| **8 theme centroid embeddings** | The pre-computed centroid for each theme, in the same embedding space as our chunks and queries. Computed once from the theme definitions + exemplars. | **Retrieval** — intent decode (centroid similarity) |

### Cross-cutting (footer)

| Block | What it does |
|---|---|
| **KMS encryption (at rest + in transit)** | All data in S3 / OpenSearch / DynamoDB is encrypted with keys we control via KMS. Network traffic uses TLS. |
| **DLQ (parse / OCR / embed failures)** | Holding pen for documents that failed processing — for human inspection. |
| **IAM scoping · VPC endpoints** | Only authorized services / users can read or write each store. VPC endpoints keep traffic private (e.g., Bedrock calls don't traverse the public internet). |
| **CloudWatch metrics & alarms** | Dashboard + alerts. "We've been seeing OCR failures spike since 9am" → page someone. |
| **CloudTrail audit log** | Records every API call, every read/write, with who and when. Required for compliance and auditability. |

---

## Part C — Retrieval Pipeline (page 2)

### Stage 1 — Input

| Block | Plain English | Example |
|---|---|---|
| **User query** | What the SME typed in chat. | "Generate epics for specimen rejection in microbiology" |
| **Session state (artifacts · drafts · refs)** | What the system remembers from earlier turns in this chat session — already-generated epics, drafts the user is editing, references the user might mention by index ("epic 3"). | `{drafts: [{id:1, title:"Specimen Rejection Workflow"}, {id:2, ...}, {id:3, title:"AST Workflow"}]}` |
| **Consumed config (theme centroids · theme defs · code dict)** | Configuration computed during ingestion that retrieval re-uses. Mainly the 8 theme centroid embeddings used to score query→theme similarity. | The 8 vectors representing G1–G8 in embedding space |

### Stage 2 — Pre-process

| Term | Plain English |
|---|---|
| **Normalize** | Trim whitespace, fix Unicode, etc. — make the query into a consistent form. |
| **Language detect** | Confirm the query is English. (POC scope is English-only — non-English would be flagged.) |
| **Ref extraction** | Detect references to session artifacts (`"epic 3"`, `"the previous one"`) or to specific docs (`@SOP-MICRO-005`). These references will be resolved later by the co-reference resolver. |

### Stage 3 — Intent decode

The system has to figure out what the user wants — not just *what topic*, but *what kind of action*. Three things run in parallel:

| Component | Plain English | Output |
|---|---|---|
| **Centroid similarity → soft theme distribution** | Embed the user's query, then cosine-compare it against the 8 theme centroids. Get a percentage per theme. Cheap (no LLM call) and gives a fast prior on which themes the query touches. | Query "specimen rejection criteria" → `{G1: 0.78, G5: 0.21, others: <0.05}` |
| **Haiku structured classifier** | A small Claude Haiku call that reads the query (with the centroid distribution as a hint) and returns a structured intent: *what action, which themes, which discipline, what granularity, what session refs, with what confidence*. | `{action: "generate", themes: ["G1"], discipline: "Microbiology", granularity: "epic", refs: [], confidence: 0.91}` |
| **{action, themes, discipline, granularity, refs, confidence}** | The five things we extract from every query. **Action** = generate / expand / compare / ask / edit / recall. **Themes** = which of G1–G8 (multi-label). **Discipline** = Micro / Cyto / cross. **Granularity** = epic / story / AC. **Refs** = which session artifacts the user mentioned. **Confidence** = how sure the classifier is. | Drives every downstream routing decision. |
| **Co-reference resolver → session refs** | Turns phrases like *"epic 3"* / *"the previous one"* / *"that AST one"* into concrete session-state IDs. Without this, the system can't act on follow-up turns. | "expand epic 3" → looks up session draft id 3 → `{target: draft_3}` |

#### Decision (yellow diamond)
The decision gate routes the query based on the intent decode:

| Branch | When | What happens |
|---|---|---|
| **proceed** | Confidence ≥ τ AND action ∈ corpus actions | Continue to expand → retrieve → rerank → assemble → output |
| **low confidence (clarify)** | Confidence < τ, or action ambiguous | Don't retrieve. Ask the user a disambiguating question. Saves us from generating confidently-wrong output on misunderstood queries. |
| **recall / edit** | Action = recall (asking about prior session state) or edit-on-existing-draft | Bypass corpus retrieval entirely. Hit the session store. The query "what did we generate so far?" doesn't need the SOP corpus. |

**τ (tau)** is a tunable confidence threshold; we'd start around 0.7 and tune from telemetry.

### Stage 4 — Expand

Two complementary expansions, both feeding the retriever:

| Block | Plain English | Example |
|---|---|---|
| **Paraphrase + UMLS synonyms** | Generate a few alternative phrasings of the query so retrieval doesn't miss chunks that say the same thing differently. UMLS gives us clinical-term synonyms specifically. | "specimen rejection" → also try "rejection criteria", "unacceptable specimens", "specimen integrity failures" |
| **Code & entity expansion** | If the query contains a clinical code (`87186`), expand it to its description so retrieval also matches chunks that don't mention the code by number but describe the test. | Query "for 87186 SOP" → also search "Kirby-Bauer susceptibility studies SOP" |

### Stage 5 — Retrieve (multi-slot hybrid)

The core retrieval. Five slots, each running its own filtered hybrid search:

| Term | Plain English |
|---|---|
| **Multi-slot** | Instead of one big "give me relevant chunks" query, we run *five* targeted queries with different filters. Each slot has a defined role in the final prompt. The model later sees chunks labeled by their slot, so it knows what each chunk is *for*. |
| **BM25 + Dense → RRF fusion** | Each slot does both sparse (BM25) and dense retrieval against the index, then merges the two ranked lists via RRF. This is the hybrid retrieval primitive. |
| **Top-K** | We keep the top K candidates per slot to feed into rerank. K varies per slot (slot 1 = 20, slot 2 = 10, etc.). |

| Slot | Filter | What it brings | Example |
|---|---|---|---|
| **SLOT 1 — In-theme target** | discipline=Micro AND theme ∈ active themes | The actual source-of-truth chunks for Microbiology on the active topic. The primary evidence the generator should ground in. | For "specimen rejection in micro," pulls Micro SOP sections about rejection criteria |
| **SLOT 2 — Cyto analogy** | discipline=Cyto AND theme ∈ active themes | The Cytology equivalent — *here's how it was solved in the prior discipline.* The generator is told "adapt, don't copy" so the Micro output isn't just Cyto with the word swapped. This is what makes the system *Cyto-anchored*. | Pulls the Cytology specimen-rejection SOP and the Cyto Jira epic that addressed it |
| **SLOT 3 — Adjacent themes** | discipline=Micro AND theme ∈ neighbors-by-centroid | Themes that aren't the active one but are *close* in centroid space, in case the query straddles. Catches relevant context the strict-theme filter misses. | Specimen rejection (G1) often touches Quality (G5) — slot 3 brings G5 chunks if the query lands at the boundary |
| **SLOT 4 (conditional) — Jira exemplars** | doc_type=jira_export — *only when* action=generate AND granularity=epic | Examples of how an epic *is shaped* — fields, level of detail, story decomposition. Helps the generator produce outputs that look like real Jira epics, not loose prose. | Pulls 5 Cyto epics on similar themes as structural exemplars |
| **SLOT 5 (conditional) — Regulatory / standards** | doc_type=regulatory — *only when* active themes ∈ {G5 Quality / Compliance} | Brings in CLIA, CAP, CLSI references when generating compliance-relevant artifacts. | For an AST-related epic, pulls CLSI M100 breakpoint requirements |

**Why split into slots instead of one big retrieval?** Because the chunks have different *roles*. Cyto chunks are not Micro source-of-truth — they're analogies. Reg chunks are not free-form context — they're standards to comply with. Role-labeling in the final prompt is what stops the generator from confusing a Cyto epic for a Micro requirement.

### Stage 6 — Rerank

| Term | Plain English |
|---|---|
| **Cross-encoder reranker per slot** | After first-pass retrieval gives us top-K candidates per slot, a more accurate (slower) model re-scores each candidate against the query. We keep the new top-K. The cross-encoder is the one component that actually handles negation well — critical for SOPs full of "if not refrigerated within 4 hours…" rules. |
| **Cohere Rerank or Claude Haiku** | Two viable implementations. Cohere Rerank is purpose-built and AWS-available. Claude Haiku as a reranker is also viable and stays within the Anthropic stack. |
| **Low-score gate (θ)** | If *every* slot's top scores are below threshold θ, the corpus doesn't actually have a good answer. Instead of letting the generator hallucinate, the system flags "no relevant content" → broaden & retry, or refuse. **θ (theta)** is tunable from telemetry. |

### Stage 7 — Assemble

The retrieved-and-reranked chunks have to be packaged into a final prompt for the generator.

| Step | Plain English |
|---|---|
| **Dedupe across slots** | A single chunk might be retrieved by multiple slots. Keep one copy with the best score, but remember it scored in multiple slots (useful signal). |
| **Token-budget trim (drop low-priority slot first)** | Even after rerank, the chunks may exceed the LLM's prompt budget. We trim by *slot priority* first — drop slot 5, then 4, then 3 — before we trim within slots. Preserves the most important evidence. |
| **Role-labeled context (PRIMARY · ANALOGY · ADJACENT · EXEMPLAR · REG)** | The chunks enter the prompt with their slot label visible to the model. The system prompt explains what each role means: *PRIMARY = ground truth for this discipline; ANALOGY = similar-problem prior, adapt; EXEMPLAR = output shape reference; REG = compliance constraint; ADJACENT = breadth context.* |
| **+ 8-theme prior** | The 8 theme definitions and Micro direction notes are loaded into the system prompt so the model knows the taxonomy when emitting epics. |
| **+ session context** | Existing drafts and prior turns are included so follow-up queries make sense ("expand epic 3" works because the prompt sees epic 3). |
| **+ output schema (epic / story)** | The generator is constrained to produce JSON of a specific shape — `{title, description, theme_tag, acceptance_criteria, stories[]}`. Makes the output parseable, importable to Jira, and auditable. |

### Stage 8 — Output

| Block | Plain English |
|---|---|
| **→ Generation layer (LLM call · structured output · citations resolved to S3 doc + section + version)** | The assembled prompt goes to Claude (Bedrock) which produces the structured epic/story JSON. Each generated artifact carries citations back to the chunks that justified it; chunk → source doc + section + version → S3 path. SMEs can click through to the originating SOP. |
| **→ Telemetry (query · intent · slot scores · final context · latency)** | Everything that happened on this turn is logged: the query, the intent decode, what each slot retrieved, the rerank scores, what made the final cut, and how long each stage took. This is the eval signal — without it, we can't improve retrieval over time. |

---

## Part D — A worked example

**User query:** *"Generate epics for specimen rejection in microbiology."*

1. **Pre-process** — clean text, no session refs detected, language=English.
2. **Centroid similarity** — query embeds closest to G1 (0.81), then G5 (0.18). Most weight on G1 Pre-Analytic / Specimen Management.
3. **Haiku classifier** — `{action: "generate", themes: ["G1","G5"], discipline: "Microbiology", granularity: "epic", confidence: 0.91}`.
4. **Decision** — confidence > τ, action is in corpus actions → proceed.
5. **Expand** — adds paraphrases: "rejection criteria", "specimen integrity failures", "unacceptable samples".
6. **Multi-slot retrieve:**
   - SLOT 1 (Micro / G1+G5): Micro SOP sections on specimen handling, rejection criteria, transport requirements.
   - SLOT 2 (Cyto / G1+G5): the Cyto specimen-rejection SOP and the corresponding Cyto Jira epic.
   - SLOT 3 (Micro / adjacent themes): G2 chunks if the query straddles into specimen *processing*.
   - SLOT 4: Jira-export exemplars (action=generate ∧ granularity=epic) — 5 sample Cyto epics for shape.
   - SLOT 5: G5 active → reg/standards on specimen integrity (CLSI M22, CLIA §493.1252).
7. **Rerank** — cross-encoder narrows each slot. Top scores healthy → proceed (low-score gate not triggered).
8. **Assemble** — dedupe, fit to budget, label by role, add 8-theme prior, add output schema.
9. **Generate** — Claude returns structured JSON: 2–4 candidate epics in G1, each with stories, each story carrying citations like `{ref: s3://lab-sops/micro/SOP-MICRO-007_v2.pdf#section=AcceptanceCriteria}`.
10. **Telemetry** — logged for later eval.

The SME reviews, accepts/edits, and the next turn (*"add a story to epic 2 for AST specimens"*) goes through the same pipeline but with action=expand, granularity=story, target=session-draft-2.

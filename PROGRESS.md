# Progress Log

## Current state

**Phase:** Architecture design — v3.2 (Conditioned Discovery) draft spec consolidated; v3.2-only canonical deliverables (`microbio_lims_architecture_v32.{docx,drawio,md}`) shipped as the team-shareable single source, separate from the v3.1+v3.2 walkthrough that retains evolution-framing. v3.3 iteration in progress (user editing Word doc directly). Next: SME ratification of v3.2 spec → calibration of τ_match / ε_novelty on the first conditioned Epic Extractor run over the Micro POC SOPs.

**Latest framing (v3.2):** Conditioned Discovery — warm-start (don't cold-start) at both theme and epic levels. A new pre-flight **Theme Discovery agent** classifies a new discipline's SOPs against the prior theme catalog (e.g. `cyto_v1`) at threshold `τ_match`, clusters only the residual at minimum size `ε_novelty`, and routes novel candidates through SME ratification. The **Epic Extractor runs in conditioned mode** — drafts are matched against the prior epic catalog (`cyto_epic_v1`) before any clustering; matched drafts inherit `epic_analog` by construction. Catalogs are versioned config-as-data (`<discipline>_v<N>` for themes, `<discipline>_epic_v<N>` for epics). Cross-discipline links live in an explicit **ANALOGY map** artifact (typed: identical / partial / discarded_in_target / novel_in_target). G0/E0 unclassified buckets are first-class with a 5% alarm threshold. The 5-agent main pipeline (Epic Extractor → Story Extractor → Validator → Cross-SOP Synthesis → Validator → Dependency Resolver) is unchanged in shape.

**v3.1 framing (preserved unchanged):** Agent-based extraction from SOPs to dev-actionable Jira artifacts. The agent's deliverable is **Epics + Stories** (Tasks are out-of-scope, dev-authored). Stories come in **four shapes** (capability, workflow-stage-split, configuration-instance, cleanup) — the agent replicates the shape mix observed in Cyto's existing Jira backlog rather than normalizing to a single abstraction level. A **cross-SOP synthesis pass** lifts recurring patterns into capability stories that coexist alongside the per-SOP concrete stories. Cyto data continues to function as a **teaching corpus**.

**Story bar established:** Stories must pass the *"dev team picks it up Monday morning and codes against it without coming back to ask"* test — but the bar is now **shape-aware** (a configuration-instance story is "actionable" by precision of values; a capability story is "actionable" by MUST/SHALL clarity). See `DECISIONS.md` D7 + D10 for the type-aware Validator rubrics.

**Platform:** Labcorp's LIMS platform is named **Connect**. Cyto runs on Connect today; Micro is being built on Connect (greenfield assumption for the POC; v2 extension-mode where the agent diffs against existing Connect capabilities is deferred).

## Completed

- ✅ Initial architecture: ingestion + retrieval pipelines (8 drawio pages — Ingestion, Retrieval, Concepts & AWS, Detail × 2, I/O × 2, Query Taxonomy)
- ✅ Glossary doc explaining every term + AWS service
- ✅ End-to-end stage explainer doc
- ✅ Established 4 explicit policy decisions for query routing (default discipline, out-of-corpus, vague query, confidence thresholds τ=0.7 / θ=0.5)
- ✅ Conceptual reframe: agent's deliverable scope = SOP → Epic → Story (collapsed from 4-layer model — D6); the platform's full Jira hierarchy is Epic → Story → Task with Tasks dev-authored
- ✅ Established the story-actionability bar with concrete examples (vague vs actionable — D7)
- ✅ Public GitHub repo published (`Rajneesh-Tiwari/LabReq_agent`)
- ✅ Reviewed real Cyto Jira evidence (Epics, Stories, Tasks) → confirmed 3-level Jira hierarchy and discovered that Cyto Stories are not at a single abstraction level
- ✅ v3.1 spec consolidated: 4 story shapes, per-SOP replicates Cyto mix, cross-SOP synthesis adds abstraction layer, Tasks out-of-scope, type-aware Validator
- ✅ Drawio pages 9–12 added (Working Model, Agent Pipeline, Validator Rubrics, Cross-SOP Synthesis & Exemplar Corpus); deck reordered into a 10-page reading flow as `microbio_lims_architecture.drawio`
- ✅ **Walkthrough deliverables built** (2026-04-29):
  - `microbio_lims_architecture_walkthrough.pdf` — terse 2-page text-only reference
  - `microbio_lims_architecture_walkthrough_visual.{tex,pdf}` — 7-page visual reference with TikZ block diagrams (agent pipeline, story shapes, cross-SOP synthesis, ingestion, retrieval, validator flow, plus two graph views — Story DAG and Cyto→Micro lineage)
  - `microbio_lims_architecture_walkthrough.docx` — client-facing Word version with the 8 diagrams embedded as PNGs (built via pandoc; default Calibri/Cambria styling; preferred deliverable per `memory/feedback_delivery_format.md`)
  - `diagrams/` — 8 standalone PNGs corresponding to the inline TikZ figures
- ✅ Schema deep-dive added to walkthrough: per-field tables for Epic, Story, Cluster (intermediate), and Validator output schemas. Glossary section at the top defines shape, theme, intent, τ/θ, batch wait.
- ✅ YAML profile structure fully specified with worked example (`cultures/urine.yaml`): partitioned into pre_analytic / analytic / post_analytic; every value typed with units + SOP citation; `related_story_acs` back-references the Stories whose AC consumes the profile.
- ✅ 5-pass QC of the Word doc completed; 5 issues found and fixed (broken cross-ref to "agent 3a", missing verdict enum in Validator schema, theme/themes singular-vs-array mismatch, undocumented draft-vs-Jira ID convention, missing YAML stage lead-ins).
- ✅ **v3.2 spec drafted** (2026-04-29, `V3_2_SPEC.md`) — Conditioned Discovery as warm-start at theme + epic levels. Two-pass classify-then-cluster algorithm with `τ_match` (0.65) and `ε_novelty` (3) as the bias knobs. Versioned catalog naming: `<discipline>_v<N>` for themes, `<discipline>_epic_v<N>` for epics. G0/E0 first-class with 5% alarm. Explicit ANALOGY map artifact. Proposed decisions D16–D19.
- ✅ **3 new v3.2 drawio pages** (2026-04-29) appended to `microbio_lims_architecture.drawio` — Theme Discovery (4-pass flow + knobs/alarm panels + worked Histo example), Conditioned Epic Extractor (v3.1-vs-v3.2 contrast + match-or-cluster branching + prior/output YAML), ANALOGY Map (cyto_v1 ↔ histo_v1 graph view + full schema). Deck now 13 pages. v3.1 Working Model and Agent Pipeline pages annotated with v3.2-update pointers.
- ✅ **5-pass QC of v3.2 spec + drawio** (2026-04-29); 18 issues found and fixed in commit `4bd9e12` — naming convention (`cyto_v1` themes vs `cyto_epic_v1` epics), `epic_analog` struct, `theme_catalog_version` rename, ANALOGY map G7 deduplication, §7 worked-example math fix (7/11 ≈ 64%, not 7/12 = 58%), Pass 4 chunk re-classification semantics, ce_dec rhombus color mismatch, etc.
- ✅ **v3.2 deliverables rebuilt** (2026-04-30):
  - `microbio_lims_architecture_walkthrough.{tex,pdf}` — text walkthrough updated to v3.2 (3 pages now, was 2). Adds the Conditioned Discovery section with τ_match / ε_novelty, worked Histology example, and Micro POC migration steps.
  - `microbio_lims_architecture_walkthrough_visual.{tex,pdf}` — visual walkthrough updated to v3.2 (12 pages now, was 7). Adds Theme Discovery + Conditioned Epic Extractor TikZ figures, ANALOGY Map graph view (cyto_v1 ↔ histo_v1), three new schema subsections (theme catalog, epic catalog, ANALOGY map), and v3.2 glossary terms.
  - `microbio_lims_architecture_walkthrough.{md,docx}` — client-facing Word version rebuilt via markdown→pandoc; markdown source now committed to repo as the canonical authoring surface. 11 PNGs embedded (8 v3.1 + 3 v3.2). Default Calibri/Cambria styling preserved (per `memory/feedback_delivery_format.md`).
  - `diagrams/09_theme_discovery.png`, `10_conditioned_epic_extractor.png`, `11_analogy_map.png` — three new standalone-TikZ → Ghostscript PNGs at 200 DPI.
- ✅ **v3.2-only canonical deliverables** (2026-04-30) — separate clean track parallel to the v3.1+v3.2 walkthrough, intended for sharing with the dev team without dragging evolution-framing along:
  - `microbio_lims_architecture_v32.docx` (and `.md` source) — the canonical narrative reference. Single coherent story, no "v3.1 vs v3.2" contrast, no version markers on schema headings, no "v3.2 addition" callouts. Output A/B promoted to A/B/C with the catalog artifacts (theme catalog, epic catalog, ANALOGY map) as a first-class third output. 11 PNG diagrams embedded. Built via markdown → pandoc with default Calibri/Cambria styling.
  - `microbio_lims_architecture_v32.drawio` — 13-page deck reordered to follow execution order (Working Model → Theme Discovery (pre-flight) → Agent Pipeline → Epic Extractor (conditioned) → Validator Rubrics → Cross-SOP Synthesis → ANALOGY Map → ingestion / retrieval / query taxonomy / AWS pages). v3.2-update annotation boxes removed from v3.1 pages; v3.1-vs-v3.2 contrast block in Conditioned Epic Extractor page replaced with neutral principle callout; "v3.2" prefix dropped from all page titles.
- ✅ **5-pass QC of v3.2-only deliverables** (2026-04-30); 14 issues found and fixed in commit `3e51227` — Working Model Epic schema upgraded from v3.1 to v3.2 fields, Output C promised in §1 finally delivered in "What ships" section, EPIC-MICRO-001 / EPIC-CYTO-007 vs EPIC-CYTO-014 contradiction resolved, Specimen Receipt vs Specimen Receiving title alignment, section reorder so Theme Discovery precedes Agent Pipeline (matches drawio), Glossary "Theme (G1–G8)" generalized to "Theme (G*, H*, …)" since v3.2 admits new themes, Cyto → Micro lineage table `epic_analog` row updated from v3.1 framing ("Just an ID reference for SME traceability") to v3.2 framing (struct, populated by construction), depersonalized "User's stated motive" → "Design intent: bias toward reuse" in both files.
- ✅ **"Open questions — what's still TBD" section added to v3.2-only docx** (2026-04-30) — ~12 deliberately-unresolved items grouped into four buckets: (a) conditioned-discovery calibration (τ_match, ε_novelty defaults, Pass-1 scoring backend, G0/E0 alarm window — all need first-run telemetry); (b) operational decisions before deployment (SME ratification UX, re-tagging policy, cross-version querying); (c) implementation choices (Jira integration mechanism, per-culture profile granularity for multi-variant SOPs, story-shape classifier training, 4-shape escape hatch); (d) stakeholder/SME inputs the dev team can't decide alone (PHI handling, sample artifact access, Cyto SME availability). Each item shows current default/lean and what has to happen to move it out of TBD. Drawio left unchanged — TBD lists belong in the narrative artifact, not the visual deck.
- ✅ **`microbio_lims_architecture_v33.docx`** (2026-04-30) — user-edited iteration of the architecture Word doc; pushed alongside the v32 canonical version without overwriting it.

## In progress

- 🔄 SME pairing for first exemplar curation (one tuple per shape — capability, stage-split, config-instance, cleanup)
- 🔄 Light edits to existing pages 1–8 to re-label retrieval primitives as exemplar-retrieval consumers in the new pipeline (cosmetic, not blocking)

## Planned next

See `NEXT_STEPS.md` for concrete actions.

## Architecture evolution

| Version | Framing | Output unit | Cyto's role |
|---|---|---|---|
| **v1** | Chat → RAG → epic | Epic (loose) | Source for retrieval |
| **v2** | Layered: SOP → Capability → Requirement → Configuration | Capability map + delta (REUSE/ADAPT/NEW) | Anchor registry to match against |
| **v3** | Agent pipeline learns from Cyto exemplars | Single-shape Story (with AC) | Teaching corpus / few-shot exemplars |
| **v3.1 (current)** | Same agent pipeline + 4 story shapes + cross-SOP synthesis | Multi-shape Stories + capability stories from synthesis + per-culture configuration profile | Teaching corpus, with shape mix as a learned dimension |

## What carries through every version

These primitives have remained valid across all reframes:

- Hybrid retrieval (BM25 + Dense + RRF)
- Cross-encoder reranking
- Multi-slot retrieval with role labels
- 8-theme prior as soft constraint
- Code expansion / clinical NER / PHI redaction at ingest
- AWS substrate (S3 · SQS · DynamoDB · OpenSearch · Bedrock · Comprehend Medical · Textract · Lambda)

What's *changed* in v3 / v3.1 is the consumer — retrieval primitives now serve **exemplar retrieval for the agents**, not direct query→answer.

## Key v3.1 insights worth remembering

- **Cyto's existing Jira is heterogeneous.** Real stories sit across four shapes (capability / workflow-stage-split / configuration-instance / cleanup). Forcing one abstraction level would not match how the dev team actually consumes the backlog.
- **The agent does not invent abstraction from a single SOP.** Capability stories only emerge from cross-SOP recurrence. This protects against the agent fabricating capability boundaries that aren't grounded in evidence.
- **Tasks are not the agent's job.** They reference test IDs, lib versions, internal validators — implementation-detail the agent can't responsibly fabricate. The handoff is at Story level; dev team owns task decomposition.
- **Cyto → Micro information flows three ways**, not one. (a) `epic_analog` — Cyto Epic ID recorded on Micro Epic for traceability (D13). (b) `exemplar_of` — Cyto (excerpt → Story) pair lands in the Story Extractor's few-shot prompt. (c) `retrieval_analogy` — Cyto chunks populate the ANALOGY slot at chat time. The same Cyto material thus serves three roles: curated few-shot teaching set, indexed corpus for live retrieval, structural reference at the Epic level.
- **Themes are load-bearing config, not decoration.** G1–G8 are precoditions for the theme tagger, the 8 centroid embeddings, the intent-decode classifier, the ADJACENT retrieval slot, and the Epic schema. Cold-starting a new discipline (Histology, Hematology) without prior taxonomy is **not a config swap** — it would need a theme-discovery agent we haven't designed yet. See OPEN_QUESTIONS for v3.2 framing.

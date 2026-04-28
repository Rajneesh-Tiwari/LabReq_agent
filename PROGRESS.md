# Progress Log

## Current state

**Phase:** Architecture design — v3.1 spec consolidated, drawio pages 9–12 next.

**Latest framing (v3.1):** Agent-based extraction from SOPs to dev-actionable Jira artifacts. The agent's deliverable is **Epics + Stories** (Tasks are out-of-scope, dev-authored). Stories come in **four shapes** (capability, workflow-stage-split, configuration-instance, cleanup) — the agent replicates the shape mix observed in Cyto's existing Jira backlog rather than normalizing to a single abstraction level. A **cross-SOP synthesis pass** lifts recurring patterns into capability stories that coexist alongside the per-SOP concrete stories. Cyto data continues to function as a **teaching corpus**.

**Story bar established:** Stories must pass the *"dev team picks it up Monday morning and codes against it without coming back to ask"* test — but the bar is now **shape-aware** (a configuration-instance story is "actionable" by precision of values; a capability story is "actionable" by MUST/SHALL clarity). See `DECISIONS.md` D7 + D10 for the type-aware Validator rubrics.

**Platform:** Labcorp's LIMS platform is named **Connect**. Cyto runs on Connect today; Micro is being built on Connect (greenfield assumption for the POC; v2 extension-mode where the agent diffs against existing Connect capabilities is deferred).

## Completed

- ✅ Initial architecture: ingestion + retrieval pipelines (8 drawio pages — Ingestion, Retrieval, Concepts & AWS, Detail × 2, I/O × 2, Query Taxonomy)
- ✅ Glossary doc explaining every term + AWS service
- ✅ End-to-end stage explainer doc
- ✅ Established 4 explicit policy decisions for query routing (default discipline, out-of-corpus, vague query, confidence thresholds τ=0.7 / θ=0.5)
- ✅ Conceptual reframe: SOP → Epic → Story (collapsed from 4-layer model — D6)
- ✅ Established the story-actionability bar with concrete examples (vague vs actionable — D7)
- ✅ Public GitHub repo published (`Rajneesh-Tiwari/LabReq_agent`)
- ✅ Reviewed real Cyto Jira evidence (Epics, Stories, Tasks) → confirmed 3-level Jira hierarchy and discovered that Cyto Stories are not at a single abstraction level
- ✅ v3.1 spec consolidated: 4 story shapes, per-SOP replicates Cyto mix, cross-SOP synthesis adds abstraction layer, Tasks out-of-scope, type-aware Validator

## In progress

- 🔄 New drawio pages (9–12) reflecting v3.1:
  - **Page 9:** Working Model — 3-level Cyto hierarchy, agent's scope boundary (Epic + Story), 4 story shapes with examples per shape
  - **Page 10:** Agent Pipeline — 5 agents (Epic Extractor → Story Extractor → Validator → Cross-SOP Synthesis → Dependency Resolver)
  - **Page 11:** Validator Rubrics — 4 type-aware sub-rubrics + revise/escalate logic
  - **Page 12:** Cross-SOP Synthesis & Exemplar Corpus — synthesis trigger logic, exemplar curation, growth loop
- 🔄 Light edits to existing pages 1–8 to re-label retrieval primitives as exemplar-retrieval consumers in the new pipeline

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

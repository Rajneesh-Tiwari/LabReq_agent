# Progress Log

## Current state

**Phase:** Architecture design — iterating on conceptual model.

**Latest framing:** Agent-based extraction from SOPs to dev-actionable Jira stories. Cyto data serves as a *teaching corpus* (curated exemplars), not as a registry to match against.

**Story bar established:** Stories must pass the *"dev team picks it up Monday morning and codes against it without coming back to ask"* test. See `DECISIONS.md` (D7) for the validator rubric.

## Completed

- ✅ Initial architecture: ingestion + retrieval pipelines (8 drawio pages)
  - **Page 1:** Ingestion (main flow)
  - **Page 2:** Retrieval (main flow)
  - **Page 3:** Concepts & AWS (jargon glossary)
  - **Page 4:** Ingestion Detail (per-stage breakdown)
  - **Page 5:** Retrieval Detail (per-stage breakdown)
  - **Page 6:** Ingestion I/O (concrete data examples per stage)
  - **Page 7:** Retrieval I/O (concrete data examples per stage)
  - **Page 8:** Query Taxonomy (6 query shapes + 4 explicit policies)
- ✅ Glossary doc explaining every term + AWS service
- ✅ End-to-end stage explainer doc
- ✅ Established 4 explicit policy decisions (default discipline, out-of-corpus, vague query, confidence thresholds τ=0.7 / θ=0.5)
- ✅ Conceptual reframe: SOP → Epic → Story (collapsed from 4-layer model)
- ✅ Established the story-actionability bar with concrete examples (vague vs actionable)
- ✅ Public GitHub repo published (Rajneesh-Tiwari/LabReq_agent)

## In progress

- 🔄 New drawio pages reflecting the agent-based architecture (planned: 4 pages — Working Model, Agent Pipeline, Validator Rubric, Cyto Exemplar Corpus)
- 🔄 Light edits to existing pages 1–8 to re-label retrieval primitive use in the new pipeline

## Planned next

See `NEXT_STEPS.md` for concrete actions.

## Architecture evolution

| Version | Framing | Output unit | Cyto's role |
|---|---|---|---|
| **v1** | Chat → RAG → epic | Epic (loose) | Source for retrieval |
| **v2** | Layered: SOP → Capability → Requirement → Configuration | Capability map + delta (REUSE/ADAPT/NEW) | Anchor registry to match against |
| **v3 (current)** | Agent pipeline learns from Cyto exemplars | Dev-actionable Story (with AC) | Teaching corpus / few-shot exemplars |

## What carries through every version

These primitives have remained valid across all reframes and are still the foundation:

- Hybrid retrieval (BM25 + Dense + RRF)
- Cross-encoder reranking
- Multi-slot retrieval with role labels
- 8-theme prior as soft constraint
- Code expansion / clinical NER / PHI redaction at ingest
- AWS substrate (S3 · SQS · DynamoDB · OpenSearch · Bedrock · Comprehend Medical · Textract · Lambda)

What's *changed* is the consumer — in v3, retrieval primitives serve **exemplar retrieval** for the agents, not direct query→answer.

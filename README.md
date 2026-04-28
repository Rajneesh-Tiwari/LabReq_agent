# LabReq Agent — POC for SOP → Jira Story Extraction

## What this is

A proof-of-concept architecture for a chat-based system that extracts **dev-actionable Jira stories** from clinical laboratory SOPs, targeting Labcorp's **Connect** LIMS platform. The system uses agents trained on existing-discipline (Cytology) examples to produce stories for new disciplines (Microbiology, Histology) — replicating the multi-shape mix observed in real Cyto Jira (capability / workflow-stage-split / configuration-instance / cleanup) rather than normalizing to a single abstraction. A cross-SOP synthesis pass adds capability stories where patterns recur. Per-culture configuration profiles are emitted alongside the stories.

## What's in this repo

| File | Purpose |
|---|---|
| `microbio_lims_ingestion_retrieval.drawio` | Multi-page architecture diagram (8 pages currently). Open at [app.diagrams.net](https://app.diagrams.net) or with the VS Code drawio extension. |
| `microbio_lims_ingestion_retrieval.md` | Stage-by-stage architecture explainer. |
| `microbio_lims_glossary.md` | Plain-language glossary of every term and AWS service used in the diagrams. |
| `cytology_epic_themes.jpg` | Reference image: 8 themes derived from existing Cytology Jira epics. |
| `PROGRESS.md` | Current status of the work. |
| `DECISIONS.md` | Architectural decisions made + rationale. |
| `OPEN_QUESTIONS.md` | Pending decisions awaiting stakeholder input. |
| `NEXT_STEPS.md` | Concrete next actions. |

## How the architecture has evolved

Started with: chat-based RAG → epic generation from SOPs.

Currently at v3.1: **agent-based pipeline** — Epic Extractor → Story Extractor → Type-Aware Validator (gate #1) → Cross-SOP Synthesis → Type-Aware Validator (gate #2) → Dependency Resolver. The same Validator agent gates every story write, both per-SOP concrete stories and synthesized capability stories. The pipeline learns from curated Cyto examples, replicates Cyto's story-shape mix per-SOP, and lifts to capability stories only on cross-SOP recurrence. See `PROGRESS.md` for the full evolution and `DECISIONS.md` for the rationale.

## Viewing the diagrams

The drawio file has multiple pages. Open it at [app.diagrams.net](https://app.diagrams.net) (browser, no install) — the page selector at the bottom switches between Ingestion, Retrieval, Concepts & AWS, Detail pages, I/O examples, and Query Taxonomy.

## Reading order

If you're new to this:
1. `README.md` (this file)
2. `PROGRESS.md` — where we are and how we got here
3. The drawio diagrams (pages 1–2 first for the main flows)
4. `microbio_lims_glossary.md` — when a term is unfamiliar
5. `DECISIONS.md` and `OPEN_QUESTIONS.md` — for the architectural reasoning
6. `NEXT_STEPS.md` — what's next

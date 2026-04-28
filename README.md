# LabReq Agent — POC for SOP → Jira Story Extraction

## What this is

A proof-of-concept architecture for a chat-based system that extracts **dev-actionable Jira stories** from clinical laboratory SOPs, targeting Labcorp's **Connect** LIMS platform. The system uses agents trained on existing-discipline (Cytology) examples to produce stories for new disciplines (Microbiology, Histology) — replicating the multi-shape mix observed in real Cyto Jira (capability / workflow-stage-split / configuration-instance / cleanup) rather than normalizing to a single abstraction. A cross-SOP synthesis pass adds capability stories where patterns recur. Per-culture configuration profiles are emitted alongside the stories.

## What's in this repo

| File | Purpose |
|---|---|
| `microbio_lims_architecture.drawio` | Multi-page architecture diagram (10 pages, ordered for reading). Open at [app.diagrams.net](https://app.diagrams.net) or with the VS Code drawio extension. |
| `microbio_lims_ingestion_retrieval.md` | Stage-by-stage architecture explainer for the ingestion + retrieval substrate. |
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

`microbio_lims_architecture.drawio` is a 10-page deck, ordered for top-to-bottom reading. Open at [app.diagrams.net](https://app.diagrams.net) (browser, no install) and use the page selector at the bottom.

**Page order (read top to bottom):**

*v3.1 architecture — what the agent does*
1. **Working Model** — 3-level Cyto Jira hierarchy, agent boundary, 4 story shapes with concrete examples, Story + Epic schemas
2. **Agent Pipeline** — 5 agents end-to-end, Validator at gate #1 and gate #2, batch boundary, dual output streams
3. **Validator Rubrics** — 4 shape-specific sub-rubrics with rejected-example illustrations, revise/escalate flow
4. **Cross-SOP Synthesis & Exemplar Corpus** — recurrence-based capability lift, exemplar growth loop

*Foundational substrate — how ingestion and retrieval feed the agents*

5. **Ingestion** — main flow (S3 → trigger → parse → process → chunk → enrich → embed → store)
6. **Ingestion I/O Examples** — concrete input/output per ingestion stage
7. **Retrieval** — main flow (intent decode → expand → multi-slot retrieve → rerank → assemble)
8. **Retrieval I/O Examples** — concrete input/output per retrieval stage

*Chat experience & reference*

9. **Query Taxonomy & Routing** — 4 explicit policies (default discipline, out-of-corpus, vague, thresholds) + 6 query shapes
10. **Concepts & AWS Glossary** — every term and AWS service used in the diagrams

## Reading order (docs + diagrams)

If you're new to this:
1. `README.md` (this file)
2. `PROGRESS.md` — where we are and how we got here
3. The drawio diagrams — pages 1–4 for the v3.1 architecture; pages 5–8 for the substrate; 9–10 for chat policies and glossary
4. `microbio_lims_glossary.md` — when a term is unfamiliar
5. `DECISIONS.md` and `OPEN_QUESTIONS.md` — for the architectural reasoning
6. `NEXT_STEPS.md` — what's next

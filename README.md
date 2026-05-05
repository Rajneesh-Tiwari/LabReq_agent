# LabReq Agent — Architecture for SOP → Jira Story Extraction

## What this is

A proof-of-concept architecture for a system that ingests **Standard Operating Procedures (SOPs)** from any clinical-lab discipline and produces dev-actionable Jira artifacts (Epics + Stories + per-discipline configuration profiles), conditioned on a prior discipline's validated body of work.

The system is designed as a **generalization mechanism** — same architecture for Cytology, Microbiology, Histology, Hematology, etc. Each new discipline is a configuration + data event, not an engineering project. No per-story SME ratification at runtime; one-time architect curation per discipline pair.

Targeted at Labcorp's **Connect** LIMS platform. Cytology is the seminal prior (Cytology runs on Connect today; Microbiology and Histology are upcoming builds).

## Current architecture: v3.5

Layered evolution:

| Version | What it added |
|---|---|
| v1 | Chat → RAG → epic generation |
| v2 | SOP → Capability → Requirement → Configuration (rejected — too much SME burden) |
| v3 | Agent pipeline learning from Cyto exemplars; single-shape Story output |
| v3.1 | + 4 story shapes + cross-SOP synthesis + per-discipline configuration profile |
| v3.2 | + pre-flight Theme Discovery + conditioned-mode Epic Extractor + versioned config-as-data catalogs + ANALOGY map + G0/E0 first-class |
| v3.4 | + static catalogs (test, persona) + SME-free operation (multi-agent quorum, auto-park, drift report) + intake scope-check |
| **v3.5 (current)** | + generalization framing + universal `lab_stage_v1` enum + persona `actor_type` + Pass 3b discard quorum + M=4 → M=3 majority + D34 (prior narrowed; exemplars optional; holdout calibration dropped) + D35 (intake scope-check removed) |

## What's in this repo

### Architecture specs (formal, evolution-framed)

| File | Purpose |
|---|---|
| `V3_5_SPEC.md` | **Current architecture spec.** Decisions D26–D35. Layers on v3.4. |
| `V3_4_SPEC.md` | v3.4 spec — SME-free operation + static catalogs (D20–D25). |
| `V3_4_DECISIONS_LOG.md` | D20–D25 in lift-and-paste format for the main DECISIONS.md. |
| `V3_2_SPEC.md` | v3.2 spec — Conditioned Discovery (D16–D19). |
| `DECISIONS.md` | D1–D15 ratified architectural decisions. |

### Architecture canonical docs (clean, team-shareable)

| File | Purpose |
|---|---|
| `microbio_lims_architecture_v35.md` | **Current canonical reference (~1,500 lines).** Glossary, onboarding contract, pipeline, 8 schemas with field tables, two worked examples (Cyto → Micro, Cyto → Histo), audit artifact samples, onboarding playbook. The team-shareable single source of truth. |
| `microbio_lims_architecture_v32.{md,docx}` | v3.2 canonical (precursor; v3.5 supersedes). |
| `microbio_lims_architecture_v33.docx` | User-edited iteration on top of v3.2. |
| `microbio_lims_architecture.drawio` | 13-page architecture diagram. **Last updated for v3.2.** Update for v3.5 deferred. |

### Walkthrough docs (evolution-framed companions; legacy)

| File | Purpose |
|---|---|
| `microbio_lims_architecture_walkthrough.{md,docx,tex,pdf}` | Long-form walkthrough. Stops at v3.2; legacy companion. |
| `microbio_lims_architecture_walkthrough_visual.{tex,pdf}` | TikZ visual walkthrough. Same v3.2 cutoff. |

### Client-facing artifacts

| File | Purpose |
|---|---|
| `client_alignment_deck.pptx` | **8-slide native PowerPoint deck for client alignment meetings.** 16:9. Real shapes, flowcharts with decision diamonds, schema examples. |
| `build_client_deck.py` | Generator script for the deck. Run `python3 build_client_deck.py` to regenerate. |

### Reference / glossary

| File | Purpose |
|---|---|
| `microbio_lims_glossary.md` | Plain-language glossary of every term and AWS service. |
| `microbio_lims_ingestion_retrieval.md` | Stage-by-stage explainer of the ingestion + retrieval substrate. |
| `cytology_epic_themes.jpg` | Reference image: 8 Cytology themes from existing Cyto Jira. |

### Operational docs

| File | Purpose |
|---|---|
| `PROGRESS.md` | Status, completed milestones, evolution table. |
| `OPEN_QUESTIONS.md` | Pending decisions and stakeholder asks. |
| `NEXT_STEPS.md` | Concrete next actions. |

### Memory mirror (for cross-machine portability)

| Path | Purpose |
|---|---|
| `memory/MEMORY.md` | Index for the in-repo memory mirror. |
| `memory/project_overview.md` | Durable project facts (architecture state). |
| `memory/project_v35_state.md` | Current architecture snapshot — D26–D35, onboarding contract, what's preserved. |
| `memory/feedback_*.md` | Style and delivery preferences accumulated across sessions. |

### Diagrams folder

11 PNG renders (agent pipeline, story shapes, cross-SOP synthesis, ingestion, retrieval, validator flow, story DAG, Cyto→Micro lineage, theme discovery, conditioned epic extractor, ANALOGY map). Last regenerated for v3.2.

## How to read this repo (by audience)

**Client / business stakeholder, first time:**
1. Open `client_alignment_deck.pptx`. 8 slides, no jargon. Should take ~10 minutes.

**Architect / dev team lead, first time:**
1. `README.md` (this file).
2. `microbio_lims_architecture_v35.md` — the canonical doc. Glossary upfront.
3. `V3_5_SPEC.md` if you want the evolution narrative and the decision rationale.
4. `OPEN_QUESTIONS.md` for what's still TBD.

**Architect onboarding a new discipline:**
1. The "Onboarding playbook" section of `microbio_lims_architecture_v35.md`. 10-step procedure with effort budgets.

**Implementer building the pipeline:**
1. The "Pipeline" section of `microbio_lims_architecture_v35.md`. Has the 4-pass discovery algorithm in pseudocode.
2. The "Schemas" section — 8 schemas with JSON/YAML examples + per-field tables.
3. The "Audit artifacts" section — sample drift report, parked story, quorum decision log.
4. `V3_5_SPEC.md` for decision-level rationale on edge cases.

**Auditor / reviewer:**
1. `DECISIONS.md` (D1–D15) + `V3_2_SPEC.md` (D16–D19) + `V3_4_SPEC.md` (D20–D25) + `V3_5_SPEC.md` (D26–D35). The full decision log lives across these four files.

## Quick architectural facts (for the impatient)

- **Pipeline:** 5 main agents + 1 pre-flight: Theme Discovery → Epic Extractor (conditioned) → Story Extractor → Validator → Cross-SOP Synthesis → Validator → Dependency Resolver.
- **Stories come in 4 shapes:** capability, workflow-stage-split, configuration-instance, cleanup. Per-SOP extraction replicates the prior's shape mix; capability stories arise only from cross-SOP synthesis (≥ 2 distinct SOPs).
- **No SME at runtime.** Quorum panel of 5 reviewers (M=3 majority + min-pairwise cosine ≥ 0.8 on descriptions) replaces SME ratification. Auto-park (after 2 failed revisions) replaces escalation. Default thresholds + first-run telemetry replace holdout calibration.
- **Onboarding inputs (mandatory):** test catalog YAML + persona catalog YAML + prior discipline's theme + epic catalogs + ANALOGY links + 15–30 sample SOPs.
- **Onboarding inputs (optional):** sanitized prior-discipline Jira export for exemplar-style transfer.
- **Three output streams:** Jira tree (Epic + Story), per-discipline configuration profiles (YAML, partitioned by test), versioned reference catalogs + audit artifacts.
- **Architect-time per new discipline:** ~6–12 hours one-time + weekly drift report review.

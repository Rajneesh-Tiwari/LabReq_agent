---
name: v3.5 architecture state — generalization reframe
description: Current target architecture (v3.5). Generalization across clinical-lab disciplines; SME-free operation; prior discipline narrowed to themes + epics + optional exemplars; intake scope-check removed.
type: project
---

The current architecture target is **v3.5** (as of 2026-05-06). It layers on v3.4 (static catalogs + SME-free operation) which layers on v3.2 (conditioned discovery), which layers on v3.1 (4 story shapes + cross-SOP synthesis).

**POC scope under v3.5 is the *generalization mechanism* across clinical-lab disciplines, not Microbiology-specific extraction.** Worked examples: Cyto → Microbiology + Cyto → Histology, both demonstrating the same machinery on different evidence.

**Why:** the v3.4 spec carried Microbiology-POC scoping throughout, which obscured the actual value claim. v3.5 strips the scoping and codifies the per-discipline onboarding contract.

**Decisions in v3.5 (D26–D35):**
- **D26** — POC scope is generalization, demonstrated across ≥ 2 target disciplines.
- **D27** — Universal `lab_stage_v1` (6 stages) closed-enum on Stories.
- **D28** — Persona catalog gains `actor_type ∈ {human, system, external_system}`.
- **D29** — Theme Discovery runs for every new discipline (lifts v3.2/v3.4 deferral).
- **D30** — "No HITL" precision: no per-story SME ratification; one-time architect curation per discipline pair acknowledged.
- **D31** — Structural enum extensions are versioned events (defined process), not silent schema changes.
- **D32** — Pass 3b discard quorum for sparsely-classified inherited themes (δ_discard=15).
- **D33** — Vote threshold M=4 → M=3 (simple majority of N=5); min-pairwise convergence ≥ 0.8 unchanged.
- **D34** — Prior discipline narrowed: theme catalog + epic catalog mandatory; story exemplars optional; tasks unused; holdout calibration dropped (Validator uses default thresholds tuned by first-run telemetry). **Supersedes D23.**
- **D35** — Intake scope-check removed. Every SOP enters the pipeline; out-of-scope content auto-parks per D22. **Supersedes D25.**

**How to apply:**
- Authoritative spec: `V3_5_SPEC.md` (formal, evolution-framed).
- Team-shareable canonical: `microbio_lims_architecture_v35.md` (clean canonical, ~900 lines, 8 schemas with field tables, two worked examples).
- Client deck: `client_alignment_deck.pptx` (8 slides, native PowerPoint shapes; generator at `build_client_deck.py`).
- Three rounds of 5-pass parallel QC have been completed; round 3 surfaced 6 stale references that have been fixed.
- "Cyto-as-oracle" was renamed to "prior-discipline-as-oracle" in v3.5 (parameterized — Cyto is the seminal prior, not the only possible one).

**Onboarding contract (5 mandatory + 1 optional inputs per new discipline):**
1. `<discipline>_test_v1.yaml` — static test catalog
2. `<discipline>_persona_v1.yaml` — static persona catalog (with `actor_type`)
3. Prior discipline's theme + epic catalogs (small structured YAMLs)
4. Static `test_links` and `persona_links` to the prior (one-time architect curation)
5. Sample SOPs (15–30 for Theme Discovery; full corpus for the run)
6. (Optional) Sanitized prior-discipline Jira export — for exemplar retrieval at extraction time

**Universal artifacts (loaded once for the whole system):**
- `lab_stage_v1.yaml` — universal 6-stage workflow
- The 4-shape Validator rubric (default thresholds + telemetry tuning)
- The pipeline + agent harness

**What did NOT change in v3.5:**
- 5+1 agent pipeline shape
- 4 story shapes; type-aware Validator
- Conditioned discovery 4-pass algorithm (Pass 3 mechanism extended with Pass 3b)
- Cross-SOP synthesis ≥ 2-distinct-SOPs threshold (D11)
- 5-slot retrieval substrate
- Three output streams (A/B/C)
- Tasks remain out-of-scope (D14)
- Greenfield assumption preserved (D15)

**Key terminology fix:** "lab" → "discipline." The v3.5 docs and deck use "discipline" throughout; "lab procedure documents (SOPs)" preserved as the domain term for the documents themselves, not as a discipline classifier.

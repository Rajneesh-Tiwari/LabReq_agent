# v3.5 Spec — Generalization Reframe

**Status:** Draft
**Layers on:** v3.4 (Static Catalogs + SME-Free Operation)
**Carries forward unchanged:** the 5+1 agent pipeline, the four story shapes, cross-SOP synthesis, the type-aware Validator (with closed-enum + persona-shape extensions), conditioned discovery, multi-agent quorum, auto-park, prior-discipline-as-oracle, and the substrate (S3 / OpenSearch / Bedrock / DynamoDB).

---

## 1. Motivation

The POC's value claim is *generalization*, not single-discipline extraction. Given (a target discipline, a prior discipline, static catalogs, sample SOPs), the system must produce dev-actionable Jira artifacts without per-discipline engineering. v3.4's spec carried Microbiology-POC scoping throughout, which obscured this. v3.5 strips the scoping, codifies the per-discipline onboarding contract, and lifts three architectural decisions that were previously deferred or implicit:

1. **Theme Discovery runs for every new discipline,** not just disciplines without a strong prior. The v3.2 / v3.4 deferral for the seminal extension was a POC convenience, not architecturally justified — a target discipline plausibly has novel themes (e.g., AST or biosafety for Microbiology, frozen-section for Histology) that the conditioned algorithm should surface, even when most themes inherit from the prior.
2. **The 6-stage clinical-lab process map is universal** across clinical lab disciplines (Cyto, Micro, Histo, Hema, Chem, …). Image 1 of the project documentation grounds this. `stage` becomes a universal closed-enum field on stories, distinct from themes — themes carry orthogonal information (QC, compliance, platform) that doesn't map to stages.
3. **Persona catalogs need an `actor_type` discriminator** because they mix humans, systems (LIMS), and external systems (EHR, instruments). Image 1 lists "LIMS" and "External Systems" alongside human roles. Without the discriminator, the Validator's persona-shape rules can't distinguish "As the LIMS" from "As a Lab Tech" — they have different patterns and shapes.

These three lifts plus the generalization reframe are v3.5.

---

## 2. Core principle

> **The architecture is parameterized by (target discipline, prior discipline, static catalogs); no discipline-specific code paths exist. Every new discipline is a configuration + data event, not an engineering event.**

That is the system's generalization claim. The POC must demonstrate it across at least two target disciplines using a common seminal prior.

---

## 3. What's universal vs per-discipline

| Dimension | Scope | Source |
|---|---|---|
| 4 story shapes | Universal | D10 |
| Validator rubric | Universal (default thresholds; tuned by first-run telemetry) | D7, D34 |
| Pipeline + agent shape | Universal | v3.2 |
| 6-stage workflow (`lab_stage_v1`) | **Universal** | NEW in v3.5; sourced from project documentation |
| Persona catalog | Per-discipline | v3.4 D20; cross-discipline alignment in image 2 |
| Test catalog | Per-discipline | v3.4 D20 |
| Theme catalog | Per-discipline (via conditioned discovery) | v3.2 §5.1; deferral lifted in v3.5 D29 |
| Epic catalog | Per-discipline (via conditioned discovery) | v3.2 §5.2 |
| Three output streams | Per-discipline outputs | v3.2 |
| ANALOGY map | One per discipline pair | v3.2 §5.5 |

---

## 4. The onboarding contract for any new discipline

A new discipline arrives with five required inputs (plus one optional enhancement):

1. **`<discipline>_test_v1.yaml`** — static test catalog
2. **`<discipline>_persona_v1.yaml`** — static persona catalog (with `actor_type` per entry)
3. **Prior discipline's theme + epic catalogs** (small structured YAMLs; e.g., `cyto_v1.yaml` for themes, `cyto_epic_v1.yaml` for epics). These are the warm-start vocabularies the new discipline's discovery passes condition against.
4. **Static `test_links` and `persona_links` to the prior** — one-time architect curation per pairing (cross-discipline alignment table)
5. **Sample SOPs** (15–30 for Theme Discovery; full corpus for the full run)

**Optional (quality enhancement, not required):**

- **Sanitized prior-discipline Jira export** — if accessible, the Story Extractor uses it for (test, role, stage, shape)-matched exemplar retrieval at extraction time. Improves output style fidelity. The system runs without it on schema + shape definitions + closed-enum catalogs alone.

Universal artifacts (not per-discipline; loaded once):

- `lab_stage_v1.yaml` — the 6-stage closed enum
- The 4-shape Validator rubric — default thresholds tuned by first-run telemetry on the new discipline (D34; supersedes D23's holdout-based approach)
- The pipeline + agent harness

The system then runs:

1. **Conditioned Theme Discovery** against prior themes → `<discipline>_v1` theme catalog (with quorum-ratified novelties).
2. **Conditioned Epic Extractor** against prior epics → `<discipline>_epic_v1` epic catalog (with quorum-ratified novelties).
3. **Per-SOP run** — Story Extractor populates closed-enum fields (`tests[]`, `persona`, `stage`, `shape`, `themes[]`); Validator gate 1 runs closed-enum + shape rubric checks; auto-park on failure.
4. **Batch synthesis** — clustering on `(test, persona, stage, shape, behavior)`; capability lift on ≥ 2 distinct SOPs; Validator gate 2.
5. **Dependency Resolver** — topological ordering.
6. **Outputs A/B/C** + drift report.

No discipline-specific code paths. That is the generalization claim, and it is the POC's success criterion.

---

## 5. Schema deltas

### 5.1 Story schema (v3.4 → v3.5) — `stage` added

```diff
{
  id, epic_id,
  shape ∈ {capability, workflow-stage-split, configuration-instance, cleanup},
  title, description,
  acceptance_criteria[],
  tests[],                      // closed enum from <discipline>_test_v<N>
  persona: string | null,       // closed enum from <discipline>_persona_v<N>
+ stage: string | null,         // closed enum from lab_stage_v1; required for
+                               // workflow-stage-split shape, optional for others
  source_citations[],
  dependencies[],
  cross_links[],
  technical_hints?,
  estimated_complexity ∈ {S,M,L},
  edge_cases_handled[],
  status,
  source_chunks[],
  theme_catalog_version: string,
  quality ∈ {passed, parked},
  parked_reason?: string[],
}
```

Validator's persona-shape interaction rule extends:
- Workflow-stage-split shape: `stage` required.
- Capability shape: `stage` optional (allowed when scoped to a single stage; null when cross-stage).
- Configuration-instance and cleanup shapes: `stage` null (these shapes target artifacts/values, not workflow positions).

### 5.2 Persona catalog gains `actor_type`

```diff
persona_catalog:
  - id: ordering_provider
    name: "Ordering Provider"
+   actor_type: human
    workflow_stages: [test_ordering]
  - id: lims
    name: "LIMS"
+   actor_type: system
    workflow_stages: [accessioning_verification, test_setup_execution, ...]
  - id: ehr
    name: "External Systems (EHR)"
+   actor_type: external_system
    workflow_stages: [test_ordering, reporting_case_closure]
```

`actor_type ∈ {human, system, external_system}`. The Validator's persona-shape rules differentiate by actor type. A `system` actor is plausible on capability stories ("As the LIMS, I want to validate received specimens against open orders…") but rare on cleanup stories (cleanup typically targets an artifact, with a human owner).

### 5.3 New universal artifact: `lab_stage_v1.yaml`

```yaml
catalog_id: lab_stage_v1
applies_to: clinical_lab_disciplines
stages:
  - id: test_ordering
    name: "Test ordering"
    description: "Order entry, eligibility, billing pre-check."
    typical_themes: [G1, G6]
  - id: specimen_collection_transport
    name: "Specimen collection and transport"
    description: "Collection, labeling, transport conditions."
    typical_themes: [G1, G5]
  - id: accessioning_verification
    name: "Accessioning and verification"
    description: "Receipt at lab, ID match, suitability check, accession."
    typical_themes: [G1, G5, G8]
  - id: test_setup_execution
    name: "Test setup and execution"
    description: "Per-discipline test execution. Cyto: slide prep + screening; Micro: plating + incubation + identification + AST; Histo: tissue processing + sectioning + staining."
    typical_themes: [G2, G5, G7]
  - id: result_interpretation_review
    name: "Result interpretation and review"
    description: "Review by qualified personnel; sign-out."
    typical_themes: [G2, G3, G5]
  - id: reporting_case_closure
    name: "Reporting and case closure"
    description: "Result release to EHR, billing finalization, archival."
    typical_themes: [G3, G4, G6]
```

`typical_themes` are advisory — they tell the agent which themes commonly appear at each stage but don't constrain. (Theme tags on chunks remain primary; stage tags are independent.)

---

## 6. What changes operationally

### 6.1 Theme Discovery now runs for the seminal extension

The v3.2 / v3.4 deferral is lifted. Theme Discovery runs for every new discipline, conditioned on the chosen prior, with the same 4-pass algorithm and v3.4's quorum mechanism replacing SME ratification. Outcome may be `0 novel themes admitted` (in which case the new theme catalog is structurally identical to the prior); but the discovery is run, its evidence is recorded in the quorum decision log, and the outcome is defended.

**Quorum decision rule (clarified; v3.5 lowers vote threshold from v3.4's M=4 to M=3 simple majority — see D33):** Pass 3 evaluates each candidate against three possible outcomes:

- **Admit** — requires `M-of-N admit votes + min-pairwise description-cosine ≥ 0.8` across the M admit-voters' synthesized one-liners (min pairwise, not mean — one outlier description blocks admission).
- **Fold-in** — requires `M-of-N agreement on the same fold target`. No convergence threshold (fold target is named from the prior catalog, not synthesized). If admit-votes and fold-in-votes split such that neither side reaches M, the cluster parks. If fold-in votes split across multiple fold targets (e.g., 2 fold→G2, 2 fold→G6, 1 admit), the cluster parks.
- **Park to G0** — default when neither admit nor fold-in clears M. Cluster waits for the next alarm cycle, when τ_match has been lowered.

**Discard quorum (Pass 3b):** Themes inherited at Pass 1 with sparse evidence (e.g., G7 Instrumentation in the Histology bootstrap, with only 12 chunks) are evaluated for retention. Trigger: an inherited theme has fewer than `δ_discard` chunks classified to it (default `δ_discard = 15`, tunable). Quorum prompt: *"Should this prior theme survive in the target catalog given the sparse evidence?"* Decision rule: `M-of-N agreement to discard + ≥ 0.8 min-pairwise cosine on the discard rationale one-liner` → discard. Otherwise retain. Discarded themes are recorded in the ANALOGY map with a `partial` or `discarded_in_target` link to whichever target theme absorbed their semantics. Pass 4 re-tags the discarded theme's chunks against the post-discard taxonomy.

### 6.2 Prior discipline's role narrows to themes + epics (D34)

v3.4's D23 ("Cyto-as-oracle") cast the prior discipline as the source for both exemplar bootstrap (few-shot prompts at extraction) AND rubric calibration (Validator threshold tuning via holdout). v3.5 narrows this. **Mandatory contributions from the prior discipline:**

- **Theme catalog** — warm-start for Theme Discovery (Pass 1 classifies new chunks against this).
- **Epic catalog** — warm-start for the conditioned Epic Extractor (draft epics matched against this).

**Optional contributions:**

- **Story exemplars** — if the prior discipline's Jira backlog is accessible, the Story Extractor can retrieve (test, role, stage, shape)-matched exemplars for few-shot prompting. Improves output style consistency. The system runs without these — output stays schema-conformant via shape definitions + closed-enum constraints.

**Removed:**

- **Holdout-based rubric calibration.** Validator runs on **default thresholds** at first deployment, tuned from first-run telemetry on the new discipline itself. The closed-enum and shape-rule checks are deterministic; the calibration burden is lower than v3.4 assumed.
- **Tasks** — out of scope per D14, never used. Explicit removal of any implicit dependency.

**Operational impact:** the prior discipline now contributes two small structured artifacts (theme catalog, epic catalog), not a Jira backlog dependency. Deployment no longer requires sanitized prior-discipline Jira access — that becomes an enhancement path, not a blocker. See D34.

**Intake scope-check removed (D35).** v3.4's D25 imposed an 80% in-catalog test-reference threshold at SOP intake; below that, the SOP was rejected. v3.5 drops this gate. **Every SOP delivered to the system enters the pipeline.** Out-of-scope content (if any) surfaces downstream as closed-enum violations in the Validator and auto-parks per D22.

### 6.3 Stage tagging at chunk enrichment

Chunk enrichment gains a fourth tagging pass:

- Theme tag (existing, soft, from theme catalog)
- Test tag (v3.4, closed enum)
- Persona tag (v3.4, closed enum)
- **Stage tag (new in v3.5, closed enum from `lab_stage_v1`)**

Stage tagger is a closed-enum classifier (regex + ontology, or short LLM prompt). Cheap because the space is 6 values plus null/multi-stage. Calibrated against a small hand-labeled Cyto holdout (~200 chunks) tagged by SOP-context heuristics — used as one-time ground truth, separate from the Cyto stories themselves (which don't yet carry stage tags). Accuracy target ≥ 95% on this holdout.

Result: chunks become facet-queryable along **four axes** (theme, test, persona, stage).

### 6.4 Cross-SOP synthesis clustering tuple extends

v3.4 said `(test, persona, shape, behavior)`. v3.5 adds stage:

`(test, persona, stage, shape, behavior)` — five-axis clustering tuple.

Sharper grouping. Stage often correlates with shape (workflow-stage-split stories enumerate stages explicitly), so this may not radically change clusters; but it catches edge cases where two stories at different stages would otherwise be clustered together by behavior alone.

---

## 7. Worked example — Cyto seminal → Microbiology extension

**Inputs:**
- `prior_discipline`: cyto (themes G1–G8 in `cyto_v1`; epic catalog `cyto_epic_v1`)
- `target_discipline`: micro
- Static catalogs supplied: `micro_test_v1`, `micro_persona_v1`, `lab_stage_v1` (universal)
- `test_links` and `persona_links` to Cyto: pre-curated from project docs (image 2)
- Sample SOPs: 20 representative Microbiology SOPs

**Step 1 — Conditioned Theme Discovery on Microbiology chunks against `cyto_v1`**

Pass 1 — classify ~600 chunks against G1–G8:

| Theme | Micro chunks | Notes |
|---|---|---|
| G1 Pre-Analytic | 145 | Specimen receiving, transport, accessioning |
| G2 Analytic | 88 | Plating, incubation, identification, smear review |
| G3 Post-Analytic | 60 | Result release |
| G4 Reporting | 52 | Reports, sign-out |
| G5 QC | 44 | Plate QC, batch QC |
| G6 Compliance | 30 | CLIA, CAP |
| G7 Instrumentation | 38 | Identification systems, automated readers |
| G8 Platform | 20 | Direct fit |
| **Residual (score < 0.65)** | **~123** | Feeds Pass 2 |

Pass 2 — cluster residual:
- Cluster 1 (size 42): "Antibiotic susceptibility patterns are read at 18–24 hours; MIC values are interpreted per CLSI breakpoints…" — proposed novel theme **MI1: Susceptibility Testing**.
- Cluster 2 (size 28): "Class II biosafety cabinet; spore strip QC weekly; autoclave validation…" — proposed **MI2: Biosafety Containment**.
- Cluster 3 (size 15): "Critical alert organisms (e.g., M. tuberculosis, MRSA in CSF) trigger notification…" — proposed **MI3: Critical Result Notification**.
- ~38 noise chunks → G0.

Pass 3 — multi-agent quorum (N=5, M=3 majority — see D33):

| Candidate | Votes | Description convergence | Decision |
|---|---|---|---|
| MI1 Susceptibility Testing | admit/admit/admit/admit/admit | 0.92 | **admit** (5/5 admit clears M=3; min-pairwise convergence 0.92 ≥ 0.8) |
| MI2 Biosafety Containment | admit/admit/admit/admit/fold→G6 | 0.85 | **admit** (4/5 admit clears M=3; min-pairwise convergence 0.85 ≥ 0.8) |
| MI3 Critical Result Notification | admit/admit/fold→G4/fold→G4/fold→G4 | 0.71 | **fold-in to G4** (3/5 fold-in to G4 clears M=3 majority; admit-convergence 0.71 doesn't matter — fold-in has no convergence requirement) |

Note on the fold-in rule: admission requires `M-of-N admit votes + min-pairwise description-cosine ≥ 0.8`; fold-in requires `M-of-N agreement on the same fold target` (no convergence threshold — the fold target is named from the prior catalog, not synthesized).

Pass 4 — MI3's 15 chunks re-tag to G4 Reporting under updated semantics. No themes discarded (G7 Instrumentation survives — Microbiology has heavy instrumentation).

**Output: `micro_v1` theme catalog**
- inherited_themes: G1–G8 (8)
- novel_themes: MI1 Susceptibility Testing, MI2 Biosafety Containment (2)
- discarded_themes: (none)
- unclassified_bucket: ~38 chunks ≈ 6.3% of total (above 5% alarm — auto-rerun with `τ_match=0.60` next cycle)

**Steps 2 onward — Conditioned Epic Extractor, per-SOP main pipeline, batch synthesis, outputs.** Same as v3.4; not repeated here.

**Net result:** `micro_v1` has 10 active themes (8 inherited + 2 admitted). Stories generated downstream tag `theme_catalog_version: micro_v1`. ANALOGY map's `theme_links` is non-empty:
- `cyto_v1.G1 → micro_v1.G1, identical` (and similar for G2–G8)
- `cyto_v1.* → micro_v1.MI1, novel_in_target`
- `cyto_v1.* → micro_v1.MI2, novel_in_target`

The same flow applied to Histology produces `histo_v1` with novel themes around tissue processing, staining, and frozen section (per V3_2_SPEC.md §7's Histo example, with quorum substituted for SME). **Two disciplines, same machinery, same contract, different evidence-driven outputs.** That is the generalization the POC must show.

---

## 8. Decisions (proposed for the log)

These extend D20–D25 from V3_4_SPEC.md.

### D26 — POC scope is generalization across disciplines, not single-discipline extraction
**Date:** 2026-05-05

**Decision:** The system's POC value claim is *given (target discipline, prior discipline, static catalogs, sample SOPs), produce dev-actionable Jira artifacts without engineering rework*. The POC must demonstrate this across at least two target disciplines (e.g., Microbiology + Histology) using Cyto as the seminal prior. Single-discipline extraction is a sub-case.

**Rationale:** Single-discipline extraction is strictly less informative than generalization. The architecture has been designed to parameterize by discipline since v3.2 (conditioned discovery, ANALOGY map, versioned catalogs); v3.5 makes the framing explicit and aligns the deliverable with the architecture's actual capabilities.

**Implication:** Operational docs (`PROGRESS.md`, `NEXT_STEPS.md`, `OPEN_QUESTIONS.md`) currently scope work as "Micro POC" — they must be updated to drop the scoping. Follow-up workstream.

### D27 — Universal stage enum (`lab_stage_v1`) as a closed-enum field on stories
**Date:** 2026-05-05

**Decision:** Story schema gains a `stage` field drawn from a universal 6-value enum (test_ordering, specimen_collection_transport, accessioning_verification, test_setup_execution, result_interpretation_review, reporting_case_closure). Required on workflow-stage-split shape; optional on others. Validator hard-rejects out-of-enum values.

**Rationale:** The clinical-lab workflow at this granularity is shared across Cyto, Micro, Histo, Hema, Chem, etc. (project documentation, image 1). Treating stage as a discipline-agnostic dimension simplifies cross-SOP synthesis (sharper clustering tuple), enables stage-faceted retrieval, and constrains the agent's free-form stage naming. Distinct from themes — themes carry orthogonal information (QC, compliance, platform) that doesn't map to stages.

**Alternatives considered:** Per-discipline stage enums (rejected — image 1 confirms stages are universal at this granularity). Free-form stage strings (rejected — loses Validator leverage).

**Open:** Sub-stages within stage 4 (test_setup_execution) for disciplines like Histology (tissue processing / sectioning / staining). Add a discipline-specific `sub_stage` field if and when sub-stages become load-bearing for workflow-stage-split stories. Defer.

### D28 — Persona catalog gains `actor_type` discriminator
**Date:** 2026-05-05

**Decision:** Each persona-catalog entry carries `actor_type ∈ {human, system, external_system}`. The Validator's persona-shape rules differentiate by actor type — system personas (LIMS) are plausible on capability stories but unusual on cleanup stories; external_system personas (EHR, instruments) appear at workflow boundaries.

**Rationale:** Image 1 lists "LIMS" and "External Systems" as roles alongside human personas. Cyto Jira similarly references the platform as an actor ("Connect Cytology"). Without the discriminator, the Validator can't apply different consistency checks for human vs system actors.

**Alternatives considered:** Drop system/external roles from the persona catalog and treat them as untyped (rejected — loses signal that's already present in real Cyto Jira and project docs).

### D29 — Theme Discovery runs for every new discipline, including the seminal extension
**Date:** 2026-05-05

**Decision:** The v3.2 / v3.4 deferral of Theme Discovery for the seminal extension (originally Microbiology POC) is lifted. Theme Discovery runs for every new discipline, conditioned on the chosen prior. Outcome may be `0 novel themes admitted` (in which case the new catalog is structurally identical to the prior); but the discovery is run, its evidence is recorded in the quorum decision log, and the outcome is defended.

**Rationale:** The deferral was a POC convenience, not architecturally justified. Conditioned discovery is strictly more informative than wholesale reuse — it surfaces evidence of novel themes if they exist (likely for Microbiology: AST, biosafety) and confirms reuse if they don't. With v3.4's quorum mechanism, Theme Discovery has no SME burden. There is no architectural cost to running it.

**Supersedes:** V3_2_SPEC.md §9 step 5 ("Defer Theme Discovery Agent…"); V3_4_SPEC.md §5.2 ("For Micro POC specifically: theme catalog is `cyto_v1` reused wholesale; no Theme Discovery needed").

### D30 — "No human-in-the-loop" claim precision: no per-story SME ratification; one-time architect curation per discipline pair
**Date:** 2026-05-05

**Decision:** The system's "no human-in-the-loop" property is precisely: *no per-story SME ratification, no per-novelty SME ratification at runtime, no rubric calibration in production*. Human inputs that ARE required, and are out of scope for the runtime claim:

- **Per-discipline (one-time at onboarding):** architect chooses prior discipline; supplies `<discipline>_test_v1.yaml`; supplies `<discipline>_persona_v1.yaml`; supplies static `test_links` and `persona_links` to the prior; provides 15–30 sample SOPs for Theme Discovery.
- **Floor-hit escalation (rare):** when the G0/E0 alarm trips and `τ_match` has reached its 0.50 floor without resolution, the discipline is flagged in the drift report for **manual catalog re-curation**. This is a code-change to the catalog YAML, performed by an architect with repo access — not a runtime SME action, not a per-story decision. The pipeline halts on the unresolvable cluster only; rest of the pipeline continues.
- **Drift report review (informational):** anyone with repo access (architect, PM, dev lead) can read the drift report; it informs cadence-tuning decisions but blocks nothing.

**Rationale:** Earlier framing ("no human in the loop") was imprecise — clients reading it literally may expect zero human inputs, which is unachievable for any system that requires onboarding configuration. Precision protects the claim's defensibility under a sharp client review.

**Implication:** Onboarding cost — quantified as **architect-hours per new discipline** — becomes a tracked metric in the eval framework (open question, §10).

### D31 — Structural enum extensions are versioned events with a defined process, not engineering events
**Date:** 2026-05-05

**Decision:** When a new structural dimension genuinely requires a new closed-enum field (as `stage` and `actor_type` did in v3.5), the change is a **versioned event** with this process:

1. Architect proposes the new field with a candidate enum vocabulary.
2. Schema bumps (`Story_v3.5 → Story_v3.6`); Validator's persona-shape rules extend.
3. Existing stories tagged against the prior schema continue to validate; new stories must populate the new field.
4. Re-tag pass (analog to Pass 4) backfills the new field on existing stories where the value can be derived; flags as null where it can't.
5. Decision recorded in the architecture decisions log.

**Rationale:** D26 says "no engineering for new disciplines." That holds for *known structural shape* of a clinical-lab discipline — bringing a new discipline does not require schema changes. But the architecture admits that *structural shape* itself can evolve (sub-stages within stage 4 may become load-bearing for Histology, e.g.). When that happens, treat it as a versioning event with explicit process, not a silent change. The claim "no engineering" is preserved at the discipline-onboarding level, not at the architecture-evolution level.

**Implication:** D27's "Open" note on sub-stages is the canonical example — if/when sub-stages become load-bearing, D31's process applies.

### D32 — Discard-quorum (Pass 3b) added to the conditioned-discovery algorithm
**Date:** 2026-05-05

**Decision:** Pass 3 of conditioned discovery covers admit / fold-in / park decisions for novel candidates. Pass 3b — the discard-quorum — covers the inverse: whether to drop an inherited theme that has sparse evidence in the target discipline. Trigger: inherited theme classified to fewer than `δ_discard` chunks (default 15). Decision rule: `M-of-N agreement to discard + ≥ 0.8 min-pairwise cosine on discard rationale` → discard with `partial` or `discarded_in_target` link in the ANALOGY map; otherwise retain. Pass 4 re-tags discarded-theme chunks against the post-discard taxonomy.

**Rationale:** The Histology bootstrap example (V3_2_SPEC.md §7) drops G7 Instrumentation from `histo_v1` because instruments are different in Histology. v3.2 / v3.4 had this as an SME judgment call; v3.5's Pass 3b automates it with the same quorum machinery as admission. Without Pass 3b, the algorithm can only add themes — it can never drop inherited themes that don't fit the target discipline, leading to stale catalogs over time.

**Alternatives considered:** Never discard inherited themes (rejected — leads to stale `<discipline>_v1` catalogs that carry irrelevant entries from `cyto_v1`). Manual discard via architect re-curation only (rejected — adds an operational gate that the quorum mechanism can handle automatically).

### D33 — Vote threshold lowered from M=4 to M=3 (simple majority of N=5)
**Date:** 2026-05-05

**Decision:** v3.4's quorum used M=4 of N=5 (super-majority, 80% agreement). v3.5 lowers this to **M=3 of N=5** (simple majority, 60% agreement) for all three quorum decision types: admit, fold-in, and discard (Pass 3b). The description-cosine convergence threshold (≥ 0.8 min-pairwise) is **unchanged** — strict on what the agreement is *about*, forgiving on whether the agreement is reached.

**Rationale:** Two-knob quorum design: the vote-count knob (M) controls how easily agents can agree on an action; the convergence knob controls how tightly they must agree on the substance. Lowering M from 4 to 3 while keeping convergence at 0.8 (min-pairwise, strictest aggregation) reaches a coherent stance: *"let the agents agree on direction even with one dissenter, but require they're really talking about the same thing when they say yes."* Super-majority M=4 was conservative for a setting with no SME backstop; with the drift report capturing all admissions for retroactive review, M=3 trades a small admit-precision drop for materially better recall on novel themes.

**Implication for worked examples:**
- Microbiology MI3 (3/5 fold-in to G4) clears under M=3 → folds-in cleanly. Under v3.4's M=4 it would have parked.
- Histology H3 (4/5 admit, conv 0.86) clears under both — no change.
- Histology H4 (3/5 admit, conv 0.78) clears M=3 on votes but **still parks** because conv 0.78 < 0.8 — the min-pairwise convergence still does work as the second gate.

**Tuning posture:** if first-run telemetry shows admit-precision degrading materially (more than ~10% of admissions retroactively flagged in drift review), tighten back to M=4. The 5% G0 alarm and the drift report are the safety nets.

**Alternatives considered:** Keep M=4 (rejected — too conservative for a no-SME setting, blocks too many marginal-but-defensible novelties). Lower further to M=2 plurality (rejected — too easy to admit on weak evidence; opens the catalog to noise). Asymmetric thresholds — M=3 for admit, M=4 for discard (deferred — adds complexity without clear benefit pre-telemetry; revisit if discard quorum is too eager).

### D34 — Prior discipline contributes themes + epics (mandatory) and story exemplars (optional); no holdout calibration
**Date:** 2026-05-06

**Decision:** The prior discipline's role narrows from v3.4's "oracle for exemplar bootstrap + rubric calibration" to:

- **Themes catalog (mandatory).** Warm-starts Theme Discovery's Pass 1 classification.
- **Epics catalog (mandatory).** Warm-starts the conditioned Epic Extractor's matching pass.
- **Story exemplars (optional).** If the prior's Jira backlog is accessible, Story Extractor can retrieve (test, role, stage, shape)-matched exemplars for few-shot prompting. Output style improves; the system functions without them.
- **Tasks: not used.** Out of scope per D14; explicit removal of any implicit dependency.
- **Holdout-based rubric calibration: dropped.** Validator runs on default thresholds initially, tuned from first-run telemetry on the new discipline. Closed-enum and shape-rule checks are deterministic; the calibration burden is lower than v3.4 assumed.

**Rationale:** Themes and epics are small structured artifacts (closed-enum-like vocabularies); they transfer cleanly across disciplines. Stories and tasks carry style and implementation-specific content that's stylistically helpful but not architecturally load-bearing. Holdout calibration assumed continuous access to the prior's Jira; in practice that access is gated, so the architecture should not depend on it. This narrowing makes deployment substantially simpler — the prior discipline contributes two tiny YAML artifacts, not a Jira backlog dependency.

**Implications:**
- **Onboarding contract simplifies.** The prior-discipline input is now: theme catalog + epic catalog (committed YAML files). Optional: a sanitized Jira export for exemplar retrieval.
- **Story Extractor operates in two modes.** With exemplars (optimal): few-shot retrieval improves style fidelity. Without exemplars (default): schema + shape definitions + closed-enum constraints + new discipline's own theme/epic catalogs. Both modes produce valid, validator-passing output.
- **Validator calibration moves to telemetry.** Default thresholds are derived from common-sense rule defaults (e.g., AC granularity heuristics); first-run telemetry tunes them. The "≥ 95% acceptance on Cyto holdout" metric is dropped.
- **Cyto Jira accessibility (existing OPEN_QUESTIONS item) is no longer load-bearing.** It becomes an enhancement path, not a blocker.

**Supersedes:** D23 (Cyto-as-oracle for exemplar bootstrap and rubric calibration). D5 (Cyto as teaching corpus, not registry) still holds — Cyto remains a teaching reference; the mechanism just narrows from Jira-dependent to catalog-dependent.

**Alternatives considered:**
- Keep exemplars mandatory (rejected — couples deployment to Jira accessibility unnecessarily).
- Drop epics too, only inherit themes (rejected — epics are also small structured vocabularies; inheriting them gives the dev team immediate Cyto ↔ Micro epic-level traceability via `epic_analog`).
- Keep holdout calibration as optional (rejected — adds a dual-mode behavior in the Validator without clear benefit; first-run telemetry suffices).

### D35 — Intake scope-check removed
**Date:** 2026-05-06

**Decision:** SOPs are not filtered at intake by test-tag profile. Every SOP delivered to the system enters the pipeline. Out-of-scope content (if any) surfaces downstream as closed-enum violations in the Validator and auto-parks per D22. The 80% threshold from v3.4's D25 is removed.

**Rationale:** Operationally, SOPs delivered to the system are by definition in-scope — they're handed in by the architect for the discipline being onboarded. The 80% threshold solved a hypothetical "out-of-scope SOP delivered by mistake" problem that doesn't occur in practice; meanwhile, it added a fragile gate that depended on the test tagger working accurately at SOP-aggregate level. Dropping it simplifies the pipeline and removes a potential false-rejection source.

**Implications:**
- **Phase 2 simplifies.** Per-document run starts with chunk enrichment, no upfront SOP-level filter.
- **Auto-park absorbs scope violations.** If a chunk references an out-of-catalog test, that chunk is tagged `test: out_of_scope` and excluded from Story Extractor input (mechanism unchanged); if a story emerges with out-of-catalog test references, the Validator hard-rejects it. Scope enforcement still happens, just at chunk/story granularity instead of document granularity.
- **Open question — bulk delivery of mistakenly-scoped SOPs.** If a large batch of out-of-scope SOPs is delivered, the system would now process them and produce mostly auto-parked stories. The drift report's auto-park-rate metric catches this; an architect can intervene to pull the SOPs from the corpus. Acceptable given the rarity of the failure mode.

**Supersedes:** D25 (intake scope-check at 80% threshold).

**Alternatives considered:**
- Tighten the threshold to 95% (rejected — same false-rejection issue, just stricter).
- Keep the gate at the chunk level only, accept SOPs wholesale (rejected — already the case for chunks; the SOP-level gate added no signal beyond chunks).
- Replace with a soft warning that surfaces in the drift report (deferred — the auto-park-rate metric already covers this).

---

## 9. Migration from v3.4

For any discipline currently scoped under v3.4, the migration is small:

1. **Receive `lab_stage_v1.yaml`** as a project-wide universal artifact.
2. **Add `stage` field to the Story schema** and update Story Extractor + Validator (Validator's persona-shape rule extends to include stage requirements per shape).
3. **Add `actor_type` to persona catalog entries** for all currently-loaded persona catalogs (`cyto_persona_v1`, `micro_persona_v1`, `histo_persona_v1`).
4. **Lift the Theme Discovery deferral** — run conditioned Theme Discovery against the chosen prior for the seminal extension. If novelties admit, fork the theme catalog (e.g., `cyto_v1` → `micro_v1`); update Stories' `theme_catalog_version`. If no novelties admit, the new catalog is identical to the prior — record the run outcome anyway as evidence the architecture executed the discovery.
5. **Narrow the prior discipline's role per D34.** Strip exemplar bootstrap and holdout calibration from the load-bearing path. Theme catalog and epic catalog become the mandatory inputs; story exemplars become an optional quality enhancement (used only if Jira access is sanctioned). Drop the rubric calibration step against a Cyto holdout; switch the Validator to default thresholds tuned by first-run telemetry.
6. **Remove the intake scope-check per D35.** Drop the 80% test-reference gate at SOP intake. Phase 2 starts with chunk enrichment directly.
7. **Update operational docs** (`PROGRESS.md`, `NEXT_STEPS.md`, `OPEN_QUESTIONS.md`) to drop the single-discipline scoping. Follow-up workstream; not blocking.

---

## 10. Open questions (v3.5-specific)

- **Stage tagger calibration.** Hand-labeled Cyto holdout (~200 chunks) is the calibration ground truth. Accuracy target ≥ 95% per the persona/test tagger pattern. Open: whether 200 chunks is enough sample size to evaluate tagger error bounds at the 5% level.
- **`actor_type` distribution in the Cyto exemplar pool.** What fraction of Cyto stories are `human` vs `system`? Affects the Validator's persona-shape rule calibration. Telemetry call.
- **Stage-theme correlation.** `lab_stage_v1.yaml` carries `typical_themes` per stage. If actual data shows tight correlations, the agent can use stage as a soft prior for theme; if loose, treat them independently. Open: if MI(stage; themes) is high, drop `stage` from the cross-SOP synthesis clustering tuple (keep it as a story field for filtering only).
- **Sub-stages within stage 4.** Histology likely needs sub-stages (tissue processing / sectioning / staining); Cyto and Micro mostly don't. Add a discipline-specific `sub_stage` field if sub-stages become load-bearing. Defer; D31's versioning process applies if/when this lifts.
- **Choice of prior discipline.** When extending to a new discipline, who picks the prior? Defaults: lab-process-similarity heuristic (cyto for histo, micro for hema). Architect decision at onboarding.
- **POC eval framework.** Single-discipline acceptance rate (v3.4's implicit metric) doesn't measure generalization. A generalization-focused eval needs (a) per-discipline acceptance rate, (b) onboarding cost (architect-hours per new discipline — per D30), (c) catalog coherence (no spurious novel themes; no missed novelty against a held-out validation set). Telemetry framework TBD.
- **Generalization scope evidence.** The architecture's claim is "works for any clinical-lab discipline." Worked examples cover Cyto → Micro and Cyto → Histo. A Cyto → Hema (or Chem) third example would generate first-run evidence for non-AP-adjacent disciplines and exercise the rubric across a different shape distribution. Defer adding the third example to a follow-up; the claim itself stands.
- **Cosine convergence aggregation pinned to min-pairwise.** Specified as `min pairwise cosine across the M admit-voters' synthesized one-liners`. Open: whether this is too strict at typical operating points (up to 3 pairs at M=3 admit-voters; up to 10 pairs at full N=5 panel) — relax to mean-pairwise or 1-vs-mean only if first-run telemetry shows admissions blocked on cosmetic phrasing differences. Bias preserved: forgive on votes (M=3), strict on substance (min-pairwise + 0.8).
- **Fold-in tie-breaking with non-unanimous targets.** Pass 3 rule: fold-in requires M-of-N agreement on the *same* fold target. What if 4-of-5 agree on fold-in direction but split across multiple targets (e.g., 2 fold→G2, 2 fold→G6, 1 admit)? Current default: park to G0. Open: whether to add a "majority-target-with-fallback" rule (admit the cluster against the most-common fold target if the plurality is large enough) once telemetry justifies it.
- **Live-vs-panel quorum denominator.** When a quorum agent crashes or times out, is M evaluated against panel-size N=5 or against responding-N? Default lean: require M-of-`responding_N` with `responding_N ≥ 4` minimum (re-run if fewer respond). Make explicit in the implementation contract.
- **Quorum-agent independence.** Same model with different prompt frames is the v3.4 default; v3.5 inherits it. Carry forward v3.4's caveat about correlated errors and add: option to mix providers (one Bedrock model + one Anthropic via API) for the seminal extension to bound correlated-error risk; report inter-rater agreement on rejects + fold-ins, not just admits.
- **Exemplar pool minimums (now an enhancement question, per D34).** Story exemplars are optional in v3.5. If the prior discipline's Jira is accessible and used: minimum useful exemplar count per shape (≈ 25–50) below which Story Extractor falls back to schema + shape definitions only. Below the minimum, the marginal value of exemplars approaches zero and the cost of retrieval-time embedding becomes net-negative.
- **Cyto Jira accessibility (now optional, per D34).** Was load-bearing in v3.4 for both exemplar bootstrap and holdout calibration. v3.5 makes it optional: theme + epic catalogs (small YAMLs) are the mandatory inputs; story exemplars are a quality enhancement if access is sanctioned.
- **"Behavior" definition in 5-axis clustering tuple.** `(test, persona, stage, shape, behavior)` — four are closed-enum. "Behavior" is the only open dimension and is the dominant clusterer. Specify: embedding similarity on `title || description || AC.then` via Bedrock Titan; HDBSCAN at min_cluster=2. Pin a default rather than leaving it underspecified.
- **Auto-park rate alarm.** D22 defines auto-park but no max queue size or halt condition. Open: alarm thresholds — e.g., > 25% parked per SOP flags an upstream-batch off-scope signal (since D35 removed the SOP-level intake gate, this is now the primary bulk-misdelivery alarm); > 15% across 10 SOPs triggers rubric threshold re-tuning. Tunable; needs first-run baseline.
- **Pass-1 zero-tag chunk handling.** If Pass 1 classifier rejects all themes for a chunk (all scores < τ_match), it joins residual. Pass 2 only operates on clusters of size ≥ ε_novelty=3, so isolated zero-tag chunks land in G0 directly. Open: whether to tighten τ_match locally for zero-tag chunks before they go to G0, or accept the G0 first-fill as expected on a fresh discipline.

---

## 11. What v3.5 explicitly does NOT change

- Pipeline shape (5+1 agents): Theme Discovery (pre-flight) → Epic Extractor (conditioned mode) → Story Extractor → Validator → Cross-SOP Synthesis → Validator → Dependency Resolver.
- Conditioned discovery algorithm (4-pass: classify → cluster → admit → re-tag). Pass 3 still uses multi-agent quorum; Pass 3b (discard) added per D32.
- Multi-agent quorum panel size (N=5) and description-convergence threshold (≥ 0.8 min-pairwise). v3.5 lowers the vote-count threshold from M=4 to M=3 (D33) but keeps the panel and the convergence rule.
- Auto-park, drift report. (Intake scope-check is **removed** per D35. Prior-discipline-as-oracle is **narrowed** per D34 — themes + epics mandatory, story exemplars optional, holdout calibration dropped.)
- 4 story shapes; type-aware Validator with shape-specific sub-rubrics.
- Cross-SOP synthesis ≥ 2 distinct SOPs threshold (D11). Clustering tuple extends with stage but the recurrence rule is unchanged.
- 5-slot retrieval substrate.
- 3 output streams. Output B's per-grouping YAML profile generalizes (cultures for Micro, block types for Histo, panels for Hema); schema deterministic per static catalogs.
- Test catalog and persona catalog as static per-discipline (now persona has `actor_type`).
- Tasks remain out-of-scope (D14).
- D15 carries forward: greenfield assumption preserved across all target disciplines. The architecture's discipline-agnostic framing is platform-agnostic in expression; for the Labcorp deployment context, the platform is Connect, and the system generates all stories needed (including for capabilities Connect-Cyto already implements). Extension-mode (diff against existing platform) remains deferred per D15.

The v3.5 changes are: **framing + two small schema deltas** (`stage` field on Story, `actor_type` on persona entries) + **one universal artifact** (`lab_stage_v1.yaml`) + **lifting one deferral** (Theme Discovery for the seminal extension) + **one mechanism extension** (Pass 3b discard quorum) + **one threshold tuning** (M=4 → M=3 majority) + **two simplifications** (D34: prior discipline narrowed to themes+epics with optional exemplars; D35: intake scope-check removed). The pipeline shape and substrate are unchanged; the surface area shrinks.

# Clinical Lab LIMS Story Generation — Architecture Reference

A discipline-agnostic system that ingests SOPs from any clinical-lab discipline and produces dev-actionable Jira artifacts (Epics + Stories) for the target LIMS platform, conditioned on a prior discipline's validated body of work.

---

## Purpose

The system extracts **dev-actionable Jira artifacts** from clinical-lab Standard Operating Procedures (SOPs). It operates as a **generalization mechanism**: given (a target discipline, a prior discipline, static catalogs, and a sample of SOPs), it produces specification-grade Jira Epics and Stories for the target discipline's LIMS build, learning from the prior discipline's existing dev backlog as a teaching corpus.

Three properties define the system:

- **No discipline-specific code paths.** Every new discipline (Cytology, Microbiology, Histology, Hematology, Chemistry, …) is a configuration + data event, not an engineering event.
- **No per-story SME ratification.** Every runtime gate that would traditionally need an SME is replaced by an automated mechanism (multi-agent quorum, prior-discipline-as-oracle, auto-park, tightened thresholds + drift report). One-time architect curation per discipline (catalogs, prior choice, cross-discipline link tables) is required at onboarding; after onboarding the runtime needs no human input.
- **Specification-grade output.** Stories must pass the *"dev team picks it up Monday morning and codes against it without coming back to ask"* bar. The bar is shape-aware.

The system delivers three output streams per target discipline:

- **Output A** — Jira tree (Epic → Story).
- **Output B** — Per-discipline configuration profiles (YAML, partitioned by test).
- **Output C** — Versioned catalogs (theme, epic, ANALOGY map) plus audit artifacts (quorum decision log, parked-stories queue, drift report).

---

## Glossary

**ANALOGY map.** A versioned artifact that records typed cross-discipline links between two catalogs (theme, epic, test, persona). Each link carries `equivalence ∈ {identical, partial, discarded_in_target, novel_in_target}`. Theme- and epic-links are computed by the conditioned discovery passes; test- and persona-links are static (supplied at onboarding from the cross-discipline role inventory).

**Auto-park.** Terminal state for a story that fails the Validator after 2 revision attempts. The story transitions to `quality: parked`, lands in the `parked/` queue with its failed-checks list visible, and is excluded from Output A in strict mode (default). The pipeline does not block; subsequent stories continue to extract. Periodic non-SME review (architect, PM) can triage the parked queue.

**Conditioned discovery.** A 4-pass procedure for extending an existing taxonomy to a new discipline: (1) classify inputs against the prior catalog using a confidence threshold τ_match; (2) cluster only the residual (low-confidence) inputs at minimum cluster size ε_novelty; (3) ratify novel candidates via multi-agent quorum (Pass 3) plus a parallel discard quorum for sparsely-classified inherited themes (Pass 3b); (4) re-tag the corpus when the catalog version bumps. Used at both theme and epic levels.

**Cross-SOP synthesis.** A batch pass that runs after all in-scope SOPs have been extracted and validated. Clusters concrete stories across SOPs by behavioral similarity along the closed-enum tuple of test, persona, stage, shape; for clusters drawn from ≥ 2 distinct SOPs, emits an additional capability-shaped story that abstracts the variable parts as parameters. Concrete + capability stories coexist with cross-links.

**Drift report.** A weekly auto-generated artifact summarizing novelty admissions and rejections (with quorum vote tallies), parked-story counts, G0/E0 bucket sizes, alarm trips, and threshold-tightening events. Reviewable by anyone but blocks nothing.

**Epic.** A coarse organizing unit in the Jira hierarchy; one level above Story. Each epic has an `id`, `title`, `description`, `discipline`, `themes[]`, and an optional `epic_analog` link to a prior-discipline epic.

**`epic_analog`.** A typed cross-discipline link populated by the conditioned Epic Extractor when a draft epic matches a prior-discipline epic with score ≥ τ_match. Carries `{catalog_id, epic_id, equivalence}` where equivalence is one of `identical / partial / discarded_in_target / novel_in_target`.

**Fold-in.** A quorum decision outcome (alongside admit and park). When ≥ M agents vote to merge a novelty candidate into the same existing entry from the prior catalog, the cluster's chunks are re-tagged under that existing entry rather than admitted as a new theme. No convergence threshold applies (the fold target is named, not synthesized). Fold-in keeps the catalog from over-fragmenting on near-duplicate proposals.

**G0 / E0.** First-class "unclassified" buckets on every theme catalog (G0) and epic catalog (E0). Hold inputs that didn't classify into an existing entry and didn't cluster into a novel one. An alarm fires when the bucket exceeds 5% of total volume; alarm-trip auto-reruns the appropriate Discovery agent with τ_match lowered by 0.05 (floor 0.50).

**Multi-agent quorum.** A panel of N independent classifier agents (default N=5) that vote on whether to admit a novelty candidate. Independence enforced via prompt-frame diversity. Admission requires M-of-N agreement (default M=3, simple majority) plus min-pairwise description-cosine convergence ≥ 0.8 across the M admit-voters' synthesized one-liners. Fold-in (merging the candidate into an existing entry rather than admitting it as new) requires M-of-N agreement on the same fold target with no convergence requirement (target is named, not synthesized). Otherwise the candidate parks to G0/E0 for the next alarm cycle.

**Persona.** The actor referenced by a story (`As a {persona}, I want…`). Drawn from a per-discipline closed-enum catalog. Each entry carries `actor_type ∈ {human, system, external_system}` to differentiate human roles from systems (LIMS) and external integrations (EHR, instruments).

**Prior-discipline-as-oracle.** The prior discipline contributes its **theme catalog** and **epic catalog** as warm-start vocabularies for conditioned discovery in the new discipline (mandatory). **Optional enhancement:** if sanitized prior-discipline Jira is accessible, the Story Extractor uses filtered (test, role, stage, shape)-matched stories as few-shot exemplars. The system runs without exemplars on schema definitions + closed-enum constraints alone. Validator rubric uses default thresholds tuned by first-run telemetry, not a prior-discipline holdout.

**Shape.** The form a story takes. Four allowed values: capability, workflow-stage-split, configuration-instance, cleanup. The Validator's sub-rubric is shape-specific.

**Stage.** The clinical-lab workflow position a story addresses. Drawn from a universal 6-value closed enum (`lab_stage_v1`): test_ordering, specimen_collection_transport, accessioning_verification, test_setup_execution, result_interpretation_review, reporting_case_closure. Required on workflow-stage-split shape; optional on others.

**Story.** The dev-actionable unit produced by the system. Each story declares its `shape` at extraction time and carries closed-enum fields for `tests[]`, `persona`, `stage`, plus standard fields (`title`, `description`, `acceptance_criteria[]`, `source_citations[]`, `dependencies[]`, `cross_links[]`, `theme_catalog_version`, `quality`).

**Test.** A discipline-specific lab test (Pap test for Cyto, Gram stain for Micro, H&E for Histo). Drawn from a per-discipline closed-enum catalog. Stories link to the tests they operationalize via `tests[]`.

**Theme.** A semantic category of behavior. Drawn from a per-discipline closed-enum theme catalog (e.g., `cyto_v1` defines G1 Pre-Analytic, G2 Analytic, …). Each chunk in the corpus carries soft theme tags from this catalog.

**τ_match, ε_novelty.** The two bias knobs of conditioned discovery. `τ_match` (default 0.65) is the match-confidence threshold above which an input inherits from the prior. `ε_novelty` (default 3) is the minimum residual cluster size to be considered for novelty admission. High `τ_match` → eager to inherit; high `ε_novelty` → conservative about admitting novelty.

---

## The onboarding contract for a new discipline

Adding a discipline to the system is a five-input, no-engineering event.

**The discipline brings (mandatory):**

1. **`<discipline>_test_v1.yaml`** — static test catalog. The full set of in-scope tests for the discipline, each with id, name, description, and links to operating SOPs.
2. **`<discipline>_persona_v1.yaml`** — static persona catalog. Each entry has id, name, `actor_type ∈ {human, system, external_system}`, and the workflow stages the persona typically operates at.
3. **Prior discipline's theme + epic catalogs** (small structured YAMLs). For the seminal extension, that's `cyto_v1.yaml` and `cyto_epic_v1.yaml`. These are the warm-start vocabularies the new discipline's discovery passes condition against. Later disciplines may chain off any validated predecessor.
4. **Static `test_links` and `persona_links` to the prior** — one-time architect curation. A typed cross-discipline alignment table: `{source: cyto.cytotechnologist, target: histo.histotechnologist, equivalence: partial}`. Equivalence is `identical / partial / discarded_in_target / novel_in_target`.
5. **Sample SOPs.** 15–30 representative SOPs for Theme Discovery; the full in-scope corpus for the full run.

**Optional (quality enhancement, not required):**

6. **Sanitized prior-discipline Jira export.** If accessible, the Story Extractor uses it for (test, role, stage, shape)-matched exemplar retrieval at extraction time. Improves output style fidelity. The system runs without it on schema + shape definitions + closed-enum catalogs alone.

**Universal artifacts (not per-discipline; loaded once for the system):**

- **`lab_stage_v1.yaml`** — the 6-stage clinical-lab workflow enum.
- **The 4-shape Validator rubric**, with default thresholds tuned by first-run telemetry on the new discipline. Closed-enum and shape-rule checks are deterministic; no prior-discipline holdout calibration is required.
- **The pipeline + agent harness** itself.

**The system then runs, in order:**

1. Conditioned **Theme Discovery** against prior themes → `<discipline>_v1` theme catalog (with quorum-ratified novelties).
2. Conditioned **Epic Extractor** against prior epics → `<discipline>_epic_v1` epic catalog (with quorum-ratified novelties; auto-inheritance for matches above τ_match).
3. **Per-SOP run** — Story Extractor populates closed-enum fields; Validator gate 1 applies closed-enum + shape-rubric checks; auto-park on failure.
4. **Batch synthesis** at corpus boundary — clustering on (test, persona, stage, shape, behavior); capability lift on ≥ 2 distinct SOPs; Validator gate 2.
5. **Dependency Resolver** — topological ordering for sprint planning.
6. **Outputs A/B/C** + drift report.

That's the contract.

---

## The pipeline

### 0. Substrate (always-on)

The ingestion + retrieval substrate is shared across disciplines. SOPs land in S3, are parsed and chunked, and each chunk passes four enrichment taggers:

- **Theme tagger** — soft tag from the discipline's theme catalog. Multi-label allowed.
- **Test tagger** — closed-enum lookup against the discipline's test catalog. 0–N tags per chunk.
- **Persona tagger** — closed-enum lookup against the discipline's persona catalog. 0–N tags per chunk.
- **Stage tagger** — closed-enum lookup against `lab_stage_v1`. 0–N tags per chunk.

All four taggers are calibrated against prior-discipline chunks (back-derived from citing prior-discipline stories' field values) until ≥ 95% accuracy on a held-out validation set.

Enriched chunks are stored in OpenSearch with hybrid indexing (BM25 + Bedrock Titan / Cohere dense vectors). Retrieval uses a 5-slot pattern (PRIMARY, ANALOGY, ADJACENT, EXEMPLAR, REG) with role labels carried into LLM prompts, fused via Reciprocal Rank Fusion and re-ranked by cross-encoder. Multi-slot retrieval can filter by any combination of theme, test, persona, stage facets.

### 1. Pre-flight (once per new discipline)

**Theme Discovery agent.** Pre-flight, runs once per new discipline (and again only when the G0 alarm trips).

**Inputs:**
- 15–30 representative SOPs from the target discipline.
- The chosen prior theme catalog (e.g., `cyto_v1`).

**Algorithm (4 passes):**

```
PASS 1 — CLASSIFY against prior:
  for each chunk in target-discipline sample:
    score = best_match(chunk, prior_catalog)     # cosine on centroids; LLM-as-classifier tiebreaker
    if score ≥ τ_match (default 0.65):
      assign chunk → existing theme; record (theme_id, score)
    else:
      mark chunk as residual

PASS 2 — CLUSTER the residual:
  cluster residual via HDBSCAN
  for each cluster of size ≥ ε_novelty (default 3):
    summarize cluster → candidate_novel_theme {description, members, evidence}
  small clusters (< ε_novelty) → G0 unclassified bucket

PASS 3 — MULTI-AGENT QUORUM (admit / fold-in / park):
  for each candidate_novel_theme:
    run N=5 independent agents with diverse prompt frames:
      Agent 1: "Is this a coherent novel theme?" (binary + reasoning)
      Agent 2: "Compare to existing themes — distinct or fold-in?"
      Agent 3: "Synthesize a one-line description; is it sharp?"
      Agent 4: "Are the cluster members behaviorally consistent?"
      Agent 5: "Would admitting this fragment the catalog into too-fine pieces?"
    each agent returns: admit | fold-in (with target) | reject

    if ≥ M=3 agents return admit AND min-pairwise description-cosine ≥ 0.8:
      → admit, with consensus description as the entry's name
    else if ≥ M=3 agents return fold-in to the same existing entry:
      → fold-in (no novel entry; cluster members tagged to that existing entry)
    else:
      → park to G0 (don't admit, don't fold-in; defer to next alarm cycle)

PASS 3b — DISCARD QUORUM (for sparsely-classified inherited themes):
  for each inherited_theme with chunk-count < δ_discard (default 15):
    run the same N=5 agent panel with the discard prompt frame:
      "Should this prior theme survive in the target catalog given the sparse evidence?"
    each agent returns: discard | retain

    if ≥ M=3 agents return discard AND min-pairwise discard-rationale-cosine ≥ 0.8:
      → discard the inherited theme; record an ANALOGY-map link
        (partial or discarded_in_target) to whichever target theme absorbs the semantics
    else:
      → retain the inherited theme

PASS 4 — RE-TAG (only when catalog version bumps):
  re-run the classifier over previously-tagged chunks against catalog v(N+1)
  update Story.themes[] / Epic.themes[] accordingly
  any chunks previously assigned to a now-discarded theme get re-classified
  against the post-discard taxonomy
```

**Output:** `<discipline>_v1` theme catalog (versioned config-as-data YAML), plus a quorum decision log capturing each candidate's votes.

### 2. Per-SOP run (the main pipeline)

For each SOP in the in-scope corpus:

**Chunk-level scope handling.** Out-of-catalog test references in chunks are tagged `test: out_of_scope` and excluded from Story Extractor input. The agent only sees in-scope content. (No SOP-level intake gate — every delivered SOP enters the pipeline; out-of-scope content surfaces as closed-enum violations downstream and auto-parks per the Validator rules.)

**Epic Extractor (conditioned mode).** For each SOP:
1. Propose draft epics from the SOP content.
2. For each draft, score against the prior epic catalog. Match ≥ τ_match → reuse the existing epic ID; populate `epic_analog` by construction.
3. Drafts below τ_match feed Pass 2 across all SOPs (residual clustering at corpus boundary).
4. Pass 3 quorum admits novel epics; Pass 4 re-tags if the catalog version bumps.

Result: the discipline's stories attach under inherited epics where the prior catalog had a match, and under novel epics where evidence demanded one. The dev team reads the catalog and immediately sees what carried over from the prior.

**Story Extractor.** Inputs:
- The SOP and its enriched chunks.
- Schema definitions for the four story shapes + closed-enum catalogs (test, persona, stage) inlined as system context.
- **Optional:** dynamic exemplar retrieval, **(test, persona, stage, shape)-targeted** — used when the prior discipline's Jira export is provided. Improves style fidelity. Not required; absent exemplars, the agent works from schema + shape definitions + closed-enum constraints.

Outputs: stories with closed-enum fields populated:
- `tests[]` — selected from the discipline's test catalog. Empty allowed for non-test-specific stories.
- `persona` — selected from the persona catalog. Required for capability and workflow-stage-split shapes; null allowed for configuration-instance and cleanup.
- `stage` — selected from `lab_stage_v1`. Required for workflow-stage-split shape; optional for capability; null typical for configuration-instance and cleanup.
- `shape` — declared by the agent at extraction time (capability / workflow-stage-split / configuration-instance / cleanup).
- `themes[]` — soft tags from the discipline's theme catalog.

The agent replicates the prior discipline's shape mix per-SOP (it does not lift to a single capability story per SOP). Capability stories arise from cross-SOP synthesis only.

**Validator (gate 1).** Runs on every story emitted, in this order:

1. **Closed-enum checks** (deterministic, no revise loop):
   - `persona ∈ persona_catalog` — hard reject on enum violation.
   - `tests[] ⊆ test_catalog` — hard reject on enum violation.
   - `stage ∈ lab_stage_v1` (or null where allowed) — hard reject on enum violation.
2. **Shape verification** — re-examine the story against shape definitions; reject if declared shape disagrees.
3. **Persona-shape interaction:**
   - Capability shape: persona present and matches SOP context.
   - Workflow-stage-split shape: persona present, stage required, sibling stories enumerated.
   - Configuration-instance shape: persona may be null; concrete typed values present; target config table named.
   - Cleanup shape: target artifact named; before/after observable; persona typically null (artifact-level).
4. **Shape-specific sub-rubric:**
   - **Capability:** AC use MUST/SHALL; parameters explicit; configurability boundaries called out; observable outcomes per AC; no ambiguous quantifiers; scope estimable (S/M/L); source citation present and resolves.
   - **Workflow-stage-split:** stage explicit in title; stage-specific behavior testable; sibling stories cross-linked; entry/exit conditions observable.
   - **Configuration-instance:** concrete values present (no "appropriate"); values typed (units / enums); source SOP excerpt cited verbatim; no MUST/SHALL pretense.
   - **Cleanup:** target artifact (id/path/screen) named; before/after observable; regression risk acknowledged; links to artifact.
5. **Revise loop.** Up to 2 revisions for shape/AC issues. Closed-enum violations short-circuit the loop (re-extraction or scope escalation).
6. **Auto-park.** After 2 failed revisions, the story transitions to `quality: parked` with the failed-checks list visible. Parked stories land in the `parked/` queue, not Output A.

### 3. Batch boundary (after all in-scope SOPs validated)

**Cross-SOP Synthesis.** Cluster validated concrete stories on the tuple `(test, persona, stage, shape, behavior)`:
- For clusters whose members come from ≥ 2 distinct SOPs, emit a capability-shaped story.
- Constants across the cluster (test, persona, stage, shape) become fixed labels on the capability.
- Variable dimensions become parameters.
- Cross-links recorded: capability story → child concrete stories; child concrete stories → parent capability story.

**Validator (gate 2).** Synthesized capability stories pass through the same Validator with the same closed-enum + shape-rubric + auto-park behavior.

**Residual epic clustering.** Draft epics below τ_match (carried from the per-SOP run) are clustered across all SOPs. Pass 2 (cluster) and Pass 3 (quorum) admit novel epics into `<discipline>_epic_v1`. Pass 4 re-tags if the catalog version bumps.

**Dependency Resolver.** Resolves dependencies and cross-links into a topological ordering for sprint planning. The story DAG is materialized.

### 4. Outputs (per discipline)

**Output A — Jira tree.** Validated stories, organized by epic. Each story carries `tests[]`, `persona`, `stage`, `shape`, and full traceability (source citations, dependencies, cross-links, `theme_catalog_version`, `epic_analog` via parent epic). Stories with `quality: parked` are excluded in strict mode (default for new disciplines); included with `quality: review_needed` flag in permissive mode.

**Output B — Per-discipline configuration profile.** YAML, partitioned by test (since the test catalog is static and known). One profile per discipline-grouping (cultures for Microbiology, block types for Histology, panels for Hematology). Schema deterministic per the static catalogs.

```yaml
# Example: cultures/blood.yaml for Microbiology
pre_analytic:
  specimen_receipt: { ... }
tests:
  gram_stain:               { params, units, citations, persona_owner }
  blood_culture_incubation: { ... }
  maldi_identification:     { ... }
  ast:                      { ... }
post_analytic:
  result_release: { ... }
```

`persona_owner` per section makes handoff explicit.

**Output C — Reference catalogs and audit.**
- Theme catalog (versioned, conditioned-discovery output).
- Epic catalog (versioned, conditioned-discovery output).
- ANALOGY map (theme_links + epic_links computed by Discovery; test_links + persona_links static, supplied at onboarding).
- Static test catalog and static persona catalog as reference outputs.
- Quorum decision log — per-novelty audit trail showing N agents' votes.
- Parked stories queue — failed-checks list per parked story.
- Drift report — auto-generated weekly + on every alarm trip.

### 5. Continuous

**G0/E0 alarms.** When G0 (theme) or E0 (epic) bucket exceeds 5% rolling-window volume, the appropriate Discovery agent auto-reruns with τ_match lowered by 0.05. Repeated trips compound the lowering with a floor of τ_match = 0.50; below the floor, auto-rerun stops and the drift report flags the discipline for manual catalog re-curation.

**Drift report.** Weekly auto-generated artifact summarizing the period's quorum decisions, parked-story counts, G0/E0 trends, alarm trips, threshold-tightening events, catalog version bumps, and chunk-level scope-tagging counts. Reviewable by anyone (architect, PM, dev lead); blocks nothing.

---

## Schemas

### Story

```json
{
  "id": "STORY-MICRO-0042",
  "epic_id": "EPIC-MICRO-001",
  "shape": "capability",
  "title": "Validate received specimens against open orders",
  "description": "...",
  "acceptance_criteria": [
    {"when": "specimen received with accession number", "then": "system MUST match against open order"},
    {"when": "no matching order found within 24h", "then": "system MUST flag for accessioning review"}
  ],
  "tests": ["gram_stain", "blood_culture_incubation"],
  "persona": "lims",
  "stage": "accessioning_verification",
  "themes": ["G1", "G8"],
  "theme_catalog_version": "micro_v1",
  "source_citations": [{"sop": "SOP-MICRO-014", "lines": "23-31"}],
  "source_chunks": ["chunk_micro_014_p3_002", "chunk_micro_014_p3_005"],
  "dependencies": [],
  "cross_links": [],
  "technical_hints": "Match logic should reuse existing accession-lookup in Connect; not a new index.",
  "estimated_complexity": "M",
  "edge_cases_handled": ["expired open order", "duplicate accession"],
  "status": "validated",
  "quality": "passed"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Stable across catalog version bumps |
| `epic_id` | string | yes | Links to an epic in `<discipline>_epic_v<N>` |
| `shape` | enum | yes | One of capability / workflow-stage-split / configuration-instance / cleanup |
| `title`, `description` | string | yes | — |
| `acceptance_criteria[]` | array | yes | Each AC: `{when, then, expected_value?}` |
| `tests[]` | array of strings | yes (may be empty) | Closed enum from the discipline's test catalog |
| `persona` | string \| null | conditional | Required for capability, workflow-stage-split |
| `stage` | string \| null | conditional | Required for workflow-stage-split; null for configuration-instance and cleanup |
| `themes[]` | array of strings | yes | Soft tags from the discipline's theme catalog |
| `theme_catalog_version` | string | yes | Resolves `themes[]` |
| `source_citations[]` | array | yes | SOP excerpt id + line range. Each: `{sop, lines}` |
| `source_chunks[]` | array of strings | yes | Chunk IDs in the retrieval substrate that the agent drew from. Enables full retrieval-traceability. |
| `dependencies[]`, `cross_links[]` | arrays | yes | Inter-story relationships |
| `technical_hints` | string | optional | Free-form note from the Story Extractor about implementation considerations or platform conventions. Advisory, not binding. |
| `estimated_complexity` | enum | yes | S / M / L |
| `edge_cases_handled[]` | array | yes (may be empty) | — |
| `status` | string | yes | Lifecycle state |
| `quality` | enum | yes | passed / parked |
| `parked_reason` | array of strings | conditional | Required if `quality = parked`; the failed-checks list from the Validator. Omitted when `quality = passed`. |

### Epic

```json
{
  "id": "EPIC-MICRO-001",
  "title": "Specimen Receiving",
  "description": "...",
  "discipline": "microbiology",
  "themes": ["G1"],
  "theme_catalog_version": "micro_v1",
  "epic_analog": {
    "catalog_id": "cyto_epic_v1",
    "epic_id": "EPIC-CYTO-014",
    "equivalence": "identical"
  },
  "inheritance_basis": {
    "match_score": 0.78,
    "shared_themes": ["G1"],
    "auto_inherited": true
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id`, `title`, `description` | strings | yes | — |
| `discipline` | string | yes | — |
| `themes[]` | array | yes | Drawn from `theme_catalog_version` |
| `theme_catalog_version` | string | yes | — |
| `epic_analog` | object \| null | conditional | Populated by construction when match score ≥ τ_match |
| `inheritance_basis` | object \| null | conditional | Populated when inherited from prior catalog |

### Theme catalog

```yaml
catalog_id: micro_v1
parent_catalog: cyto_v1
discipline: microbiology
created: 2026-XX-XX

inherited_themes:
  - id: G1
    name: Pre-Analytic
    source: cyto_v1
    centroid_embedding_ref: s3://.../centroids/G1.npy
    match_count: 145

novel_themes:
  - id: MI1
    name: Susceptibility Testing
    source: micro_v1
    cluster_evidence:
      n_chunks: 42
      sample_excerpts: [<chunk_id_1>, ...]
      proposed_definition: "Antibiotic susceptibility patterns and MIC interpretation."
    admission_decision:
      mechanism: quorum
      n_agents: 5
      m_threshold: 3
      votes:
        - {agent_id: 1, vote: admit, reasoning_excerpt: "..."}
        - {agent_id: 2, vote: admit, reasoning_excerpt: "..."}
        - {agent_id: 3, vote: admit, reasoning_excerpt: "..."}
        - {agent_id: 4, vote: admit, reasoning_excerpt: "..."}
        - {agent_id: 5, vote: admit, reasoning_excerpt: "..."}
      description_convergence_score: 0.92
      decision: admit

discarded_themes: []

unclassified_bucket:
  count: 38
  pct_of_total: 6.3
  sample_excerpts: [...]
  next_review_due: 2026-XX-XX
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `catalog_id` | string | yes | Versioned name (e.g., `micro_v1`). Stories tag against this. |
| `parent_catalog` | string \| null | yes | The prior catalog this discovery was conditioned on. `null` only for the seminal catalog (`cyto_v1`). |
| `discipline` | string | yes | Target discipline name. |
| `created` | date | yes | Catalog creation date. |
| `inherited_themes[]` | array | yes | Themes carried over from `parent_catalog` after Pass 1 classification. |
| `inherited_themes[].id`, `.name` | strings | yes | Identifier and display name. |
| `inherited_themes[].source` | string | yes | Catalog of origin. |
| `inherited_themes[].centroid_embedding_ref` | string | yes | Reference to the precomputed centroid for retrieval. |
| `inherited_themes[].match_count` | integer | yes | Number of target-discipline chunks classified to this theme in Pass 1. |
| `novel_themes[]` | array | yes (may be empty) | New themes admitted at Pass 3 quorum. |
| `novel_themes[].cluster_evidence` | object | yes | `{n_chunks, sample_excerpts, proposed_definition}`. |
| `novel_themes[].admission_decision` | object | yes | Quorum vote tally + final decision (see worked example). |
| `discarded_themes[]` | array | yes (may be empty) | Themes from the parent dropped at Pass 3b. Each carries `{id, reason, decision_by, chunks_re_tagged}`. |
| `unclassified_bucket` | object | yes | G0 statistics: `{count, pct_of_total, sample_excerpts, next_review_due}`. Always present. |

### Epic catalog

Parallel structure to the theme catalog: `inherited_epics`, `novel_epics`, `discarded_epics`, `unclassified_drafts`. Each novel epic carries an `admission_decision` block from the quorum.

```yaml
catalog_id: micro_epic_v1
parent_catalog: cyto_epic_v1
discipline: microbiology
created: 2026-XX-XX

inherited_epics:
  - id: EPIC-MICRO-001
    title: Specimen Receiving
    epic_analog:
      catalog_id: cyto_epic_v1
      epic_id: EPIC-CYTO-014
      equivalence: identical
    inheritance_basis:
      match_score: 0.78
      shared_themes: [G1]
      auto_inherited: true                # match_score ≥ τ_match; bypassed quorum

novel_epics:
  - id: EPIC-MICRO-007
    title: Antibiotic Susceptibility Testing (AST)
    epic_analog: null                     # no Cyto correspondent
    novelty_basis:
      cluster_evidence:
        n_draft_epics: 4
        sample_drafts: [<draft_id_1>, ...]
      admission_decision:
        mechanism: quorum
        n_agents: 5
        m_threshold: 3
        votes: [admit, admit, admit, admit, admit]
        description_convergence_score: 0.91
        decision: admit

unclassified_drafts:
  count: 3
  pct_of_total: 4.1
  next_review_due: 2026-XX-XX
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `catalog_id` | string | yes | Versioned (e.g., `micro_epic_v1`). |
| `parent_catalog` | string \| null | yes | Prior epic catalog. `null` only for seminal. |
| `inherited_epics[]` | array | yes | Epics inherited from `parent_catalog` at score ≥ τ_match. |
| `inherited_epics[].epic_analog` | object | yes | `{catalog_id, epic_id, equivalence}`. |
| `inherited_epics[].inheritance_basis` | object | yes | `{match_score, shared_themes, auto_inherited}`. |
| `novel_epics[]` | array | yes (may be empty) | Epics admitted via Pass 3 quorum. |
| `novel_epics[].epic_analog` | object \| null | yes | `null` for true novelties; non-null only if the quorum admitted via fold-in onto a prior. |
| `novel_epics[].novelty_basis` | object | yes | `{cluster_evidence, admission_decision}`. |
| `discarded_epics[]` | array | optional | Epics from `parent_catalog` dropped at Pass 3b. |
| `unclassified_drafts` | object | yes | E0 statistics: `{count, pct_of_total, next_review_due}`. |

### ANALOGY map

```yaml
source_catalog: cyto_v1
target_catalog: micro_v1

theme_links:                            # computed by Theme Discovery
  - {source: G1, target: G1, equivalence: identical}
  - {source: G2, target: G2, equivalence: identical}
  - {source: null, target: MI1, equivalence: novel_in_target}
  - {source: null, target: MI2, equivalence: novel_in_target}

epic_links:                             # computed by Epic Extractor
  - {source: EPIC-CYTO-014, target: EPIC-MICRO-001, equivalence: identical}
  - {source: null,          target: EPIC-MICRO-007, equivalence: novel_in_target}

test_links:                             # static, supplied at onboarding
  - {source: cyto.pap_test, target: micro.gram_stain, equivalence: partial,
     note: "Slide preparation steps overlap; staining and screening differ."}

persona_links:                          # static, supplied at onboarding from cross-discipline role inventory
  - {source: cyto.cytotechnologist, target: micro.molecular_technologist, equivalence: partial}
  - {source: cyto.lab_director,     target: micro.lab_director,           equivalence: identical}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `source_catalog`, `target_catalog` | strings | yes | The two catalogs being linked. |
| `theme_links[]` | array | yes (may be empty) | Computed by Theme Discovery (Pass 3). One link per source-target pair (or `null` source for `novel_in_target`). |
| `theme_links[].equivalence` | enum | yes | `identical / partial / discarded_in_target / novel_in_target`. |
| `theme_links[].note` | string | optional | One-line note for non-identical links explaining the partial overlap or novelty rationale. |
| `epic_links[]` | array | yes (may be empty) | Computed by the conditioned Epic Extractor. Same shape and equivalence enum as theme links. |
| `test_links[]` | array | yes (may be empty) | Static, supplied at onboarding from the cross-discipline role inventory. Maps tests across disciplines. |
| `persona_links[]` | array | yes (may be empty) | Static, supplied at onboarding from the cross-discipline role inventory. Maps personas across disciplines. |

### Persona catalog (per-discipline)

```yaml
catalog_id: micro_persona_v1
discipline: microbiology

personas:
  - id: ordering_provider
    name: "Ordering Provider"
    actor_type: human
    workflow_stages: [test_ordering]

  - id: specimen_collection_staff
    name: "Specimen Collection Staff"
    actor_type: human
    workflow_stages: [specimen_collection_transport]

  - id: accessioning_technician
    name: "Accessioning Technician"
    actor_type: human
    workflow_stages: [accessioning_verification]

  - id: molecular_technologist
    name: "Molecular Technologist"
    actor_type: human
    workflow_stages: [test_setup_execution]

  - id: microbiologist_supervisor
    name: "Microbiologist / Supervisor"
    actor_type: human
    workflow_stages: [result_interpretation_review, reporting_case_closure]

  - id: lims
    name: "LIMS"
    actor_type: system
    workflow_stages: [accessioning_verification, test_setup_execution, result_interpretation_review, reporting_case_closure]

  - id: ehr
    name: "External Systems (EHR)"
    actor_type: external_system
    workflow_stages: [test_ordering, reporting_case_closure]

  - id: instruments
    name: "External Systems (Instruments)"
    actor_type: external_system
    workflow_stages: [test_setup_execution]

  # Extended administrative roles (from cross-discipline role inventory)
  - id: lab_director
    name: "Lab Director"
    actor_type: human
    workflow_stages: [result_interpretation_review, reporting_case_closure]

  - id: quality_manager
    name: "Quality Manager"
    actor_type: human
    workflow_stages: [accessioning_verification, test_setup_execution, result_interpretation_review]

  - id: compliance_officer
    name: "Compliance Officer"
    actor_type: human
    workflow_stages: [test_ordering, accessioning_verification, reporting_case_closure]
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `catalog_id` | string | yes | Versioned name (e.g., `micro_persona_v1`). |
| `discipline` | string | yes | Target discipline. |
| `personas[]` | array | yes | Static enumeration of all in-scope actor roles. |
| `personas[].id` | string | yes | Used as the value of `Story.persona`. |
| `personas[].name` | string | yes | Display name. |
| `personas[].actor_type` | enum | yes | `human / system / external_system`. Drives Validator's persona-shape rule differentiation. |
| `personas[].workflow_stages` | array of strings | yes | The stages from `lab_stage_v1` where this persona typically operates. Used as a soft consistency check by the Validator. |

### Test catalog (per-discipline)

```yaml
catalog_id: micro_test_v1
discipline: microbiology

tests:
  - id: gram_stain
    name: "Gram Stain"
    description: "Differential staining for bacterial cell wall classification."
    operating_sops: [SOP-MICRO-014]

  - id: blood_culture_incubation
    name: "Blood Culture Incubation"
    operating_sops: [SOP-MICRO-007]

  - id: maldi_identification
    name: "MALDI-TOF Identification"
    operating_sops: [SOP-MICRO-019]

  - id: ast
    name: "Antibiotic Susceptibility Testing"
    operating_sops: [SOP-MICRO-022]
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `catalog_id` | string | yes | Versioned name (e.g., `micro_test_v1`). |
| `discipline` | string | yes | Target discipline. |
| `tests[]` | array | yes | Static enumeration of all in-scope tests. |
| `tests[].id` | string | yes | Used as a value in `Story.tests[]`. |
| `tests[].name` | string | yes | Display name. |
| `tests[].description` | string | optional | Human-readable description. |
| `tests[].operating_sops` | array of strings | optional | SOP IDs that operationalize this test. Used by the test tagger and for traceability. |

### `lab_stage_v1` (universal)

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

| Field | Type | Required | Notes |
|---|---|---|---|
| `catalog_id` | string | yes | Always `lab_stage_v1` (universal artifact, single version). |
| `applies_to` | string | yes | `clinical_lab_disciplines` for the current scope. |
| `stages[]` | array | yes | The 6-stage closed enum. Stories reference stages by `id`. |
| `stages[].id` | string | yes | Used as the value of `Story.stage`. |
| `stages[].name` | string | yes | Display name. |
| `stages[].description` | string | yes | Human-readable description for tooling and review. |
| `stages[].typical_themes` | array of strings | optional | Advisory hint for the agent — themes commonly seen at this stage. Not constraining. |

---

## Closed-enum vocabularies

Every story emitted by the system fits within five closed enums and one open dimension:

| Dimension | Type | Source | Discipline-scoped? |
|---|---|---|---|
| `shape` | Enum (4) | D10 | Universal |
| `stage` | Enum (6) | `lab_stage_v1` | Universal |
| `tests[]` | Enum (variable per discipline) | `<discipline>_test_v1` | Yes |
| `persona` | Enum (variable per discipline) | `<discipline>_persona_v1` | Yes |
| `themes[]` | Soft tags from theme catalog | `<discipline>_v1` | Yes |
| Behavioral content (title, description, AC) | Free-form | Generated by Story Extractor | N/A |

Closed enums collapse the agent's hallucination surface — for any field with a closed enum, the agent picks from a list rather than inventing a label. Validator hard-rejects out-of-enum values (no revise loop).

---

## Quality mechanisms (no per-story SME)

Every per-story gate that traditionally needed an SME is replaced by one of four automated primitives. The exceptions are explicit: one-time architect curation per discipline (catalogs, prior choice, cross-discipline link tables) and rare floor-hit escalations when the τ_match decay reaches its 0.50 floor without resolution. See "Open questions / TBD" below for the architect-onboarding-cost metric.

### Multi-agent quorum

Used at theme and epic novelty admission, plus discard quorum for sparsely-classified inherited themes (Pass 3b). A panel of N=5 independent agents runs distinct prompt frames; each returns `admit / fold-in / reject` (or `discard / retain` in Pass 3b). The decision rule is two-knob:

- **Vote count (M):** ≥ 3-of-5 (simple majority) on the same action. Forgiving on direction — one dissenter doesn't block.
- **Description convergence:** min-pairwise cosine ≥ 0.8 across the M voters' synthesized one-liners (admit and discard only — fold-in's target is named, not synthesized, so no convergence check). Strict on substance — one outlier description blocks.

Disagreement on either knob parks the cluster to G0/E0 for the next alarm cycle. All decisions are auditable in the quorum decision log.

Cost: 5× LLM calls per novelty candidate. Acceptable because Discovery runs rarely (once per discipline + on alarm trips).

### Prior-discipline-as-oracle (narrowed)

The prior discipline contributes structured warm-starts; the rest is optional or unused.

**Mandatory contributions:**

- **Theme catalog.** Warm-starts Theme Discovery's Pass 1 classification.
- **Epic catalog.** Warm-starts the conditioned Epic Extractor's matching pass.

**Optional (quality enhancement):**

- **Story exemplars.** If sanitized prior-discipline Jira is accessible, filter for quality signals (non-empty AC, linked test cases, no `WIP` / `draft` status, source citations resolve), trace each surviving story to its source SOP excerpt, tag with the (test, persona, stage, shape) tuple, and index for retrieval. Story Extractor uses these as few-shot examples. **The system runs without exemplars** — the Story Extractor falls back to schema definitions + closed-enum constraints. Output stays valid; style consistency improves marginally with exemplars present.

**Not used:**

- **Holdout-based rubric calibration is not used.** Validator runs on default thresholds at first deployment; first-run telemetry on the new discipline tunes them. The closed-enum and shape-rule checks are deterministic, which keeps the calibration burden low.
- **Tasks** — out of scope per architecture.

### Auto-park

Used at the Validator gate. After 2 failed revision attempts, stories transition to `quality: parked` and land in a separate `parked/` queue with their failed-checks list visible. Pipeline does not block; subsequent stories continue. Strict mode (default for new disciplines) keeps parked stories out of Output A; permissive mode includes them with a `review_needed` flag.

### Tightened thresholds + drift report

Used at G0/E0 alarm response. Bucket > 5% rolling-window → auto-rerun Discovery with τ_match −0.05; floor at τ_match = 0.50. Drift report (weekly + on alarm trip) summarizes quorum decisions, parked-story counts, G0/E0 trends, threshold-tightening events. Reviewable by any human; blocks nothing.

---

## Worked example — Cyto seminal → Microbiology

**Inputs:**
- `prior_discipline`: cyto (themes G1–G8 in `cyto_v1`; epic catalog `cyto_epic_v1`)
- `target_discipline`: micro
- Static catalogs supplied: `micro_test_v1` (Gram stain, blood culture incubation, MALDI identification, AST, …), `micro_persona_v1` (sourced from cross-discipline role inventory at onboarding), `lab_stage_v1` (universal)
- `test_links` and `persona_links` to Cyto: pre-curated from project documentation (cross-discipline role inventory)
- Sample SOPs: 20 representative Microbiology SOPs

### Step 1 — Theme Discovery

**Pass 1 — classify ~600 chunks against G1–G8:**

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

**Pass 2 — cluster the residual:**

| Cluster | Size | Sample excerpt | Proposed novel theme |
|---|---|---|---|
| 1 | 42 | "Antibiotic susceptibility patterns are read at 18–24 hours; MIC values are interpreted per CLSI breakpoints…" | **MI1: Susceptibility Testing** |
| 2 | 28 | "Class II biosafety cabinet; spore strip QC weekly; autoclave validation…" | **MI2: Biosafety Containment** |
| 3 | 15 | "Critical alert organisms (e.g., M. tuberculosis, MRSA in CSF) trigger notification…" | **MI3: Critical Result Notification** |
| Noise | 38 | (heterogeneous) | → G0 |

**Pass 3 — multi-agent quorum (N=5, M=3 majority):**

- **MI1 Susceptibility Testing:** 5/5 admit, min-pairwise convergence 0.92 → **admit** (vote and convergence both clear).
- **MI2 Biosafety Containment:** 4/5 admit (1 fold-in→G6), min-pairwise convergence 0.85 → **admit** (4 ≥ 3 vote; 0.85 ≥ 0.8 convergence).
- **MI3 Critical Result Notification:** 2/5 admit, 3/5 fold-in→G4, admit-convergence 0.71 → **fold-in to G4** (3 ≥ 3 vote on the same fold target; convergence is not checked for fold-in).

**Pass 3b — discard quorum:** No inherited theme has fewer than δ_discard=15 chunks (G7 Instrumentation has 38). Pass 3b is a no-op for Microbiology.

**Pass 4 — re-tag MI3 chunks to G4 Reporting** under updated semantics. No themes discarded.

**Output: `micro_v1` theme catalog**
- inherited_themes: G1–G8 (8)
- novel_themes: MI1, MI2 (2)
- discarded_themes: (none)
- unclassified_bucket: 38 chunks ≈ 6.3% of total → above 5% alarm → auto-rerun queued for next cycle with τ_match=0.60

### Step 2 — Epic Extractor (conditioned mode)

For each Microbiology SOP:

- Draft epics proposed.
- Match against `cyto_epic_v1`. Most draft epics (Specimen Receiving, Order Entry, Reporting, Billing, etc.) match Cyto epics with score ≥ 0.65 → reuse Cyto epic IDs; populate `epic_analog: identical`.
- Drafts below threshold (e.g., AST-related drafts) feed residual clustering.
- Residual clusters above ε_novelty=3 go through quorum.
- One novel epic admits with 5/5 quorum: **EPIC-MICRO-007 — Antibiotic Susceptibility Testing.**

**Output: `micro_epic_v1`** with most epics inherited from `cyto_epic_v1` plus 1 novel (AST). ANALOGY map's `epic_links` populated by construction.

### Step 3 — Per-SOP main pipeline

- Story Extractor produces stories with `tests[]`, `persona`, `stage`, `shape` populated from closed enums.
- Validator gate 1 enforces enum and shape rubrics; auto-parks failures.
- Cross-SOP synthesis at corpus boundary lifts capability stories on ≥ 2-SOP recurrence using `(test, persona, stage, shape, behavior)` clustering.
- Validator gate 2 on synthesized stories.
- Dependency Resolver materializes the story DAG.

### Step 4 — Outputs

- **Output A:** Jira tree of validated Microbiology stories, organized by epic, with `epic_analog` traceability to Cyto.
- **Output B:** `cultures/blood.yaml`, `cultures/urine.yaml`, `cultures/target_pathogens.yaml` — partitioned by test, with `persona_owner` per section.
- **Output C:** `micro_v1` theme catalog, `micro_epic_v1` epic catalog, ANALOGY map (cyto_v1 ↔ micro_v1; cyto_epic_v1 ↔ micro_epic_v1; with `test_links` and `persona_links`), quorum decision log, parked stories queue, drift report.

The Microbiology team reads Output A and immediately sees:
- What carries over from Cytology (most Specimen Receiving, Reporting, Billing stories).
- What's distinctly Microbiology (AST stories, biosafety stories — both with quorum-defended evidence).

---

## Worked example — Cyto seminal → Histology

The same machinery, with different inputs and different evidence-driven outputs. Inputs: 20 representative Histology SOPs, prior `cyto_v1`.

**Theme Discovery** classifies most chunks into G1–G8 (Pre-Analytic, Analytic, Post-Analytic, Reporting, QC, Compliance, Platform survive; G7 Instrumentation has only 12 chunks — Histology instrumentation differs from Cyto's). Residual clusters surface 4 novelty candidates: H1 Tissue Processing, H2 Staining, H3 Block & Slide Archive, H4 Frozen Section.

**Quorum admits** H1 (5/5, convergence 0.91), H2 (5/5, convergence 0.94), H3 (4/5, convergence 0.86 — both gates clear). H4 doesn't clear: 3/5 admit (clears M=3 vote) BUT min-pairwise convergence is 0.78 < 0.8 (fails strictness) → parks to G0; revisits on next alarm cycle with τ_match=0.60. The convergence gate is doing real work here — voters agreed on direction (admit) but not on substance (descriptions diverged).

**Discard quorum on G7:** 4/5 vote to discard → G7 dropped from `histo_v1`; ANALOGY map records `cyto_v1.G7 → histo_v1.H1, partial`. Pass 4 re-tags G7's 12 chunks to H1 (most) or G0 (rest).

**Result:** `histo_v1` has 10 active themes (7 inherited + 3 admitted), G7 discarded, H4 parked for revisit. Stories generated downstream tag `theme_catalog_version: histo_v1`. Same Validator, same auto-park, same outputs format.

**Two disciplines, same machinery, same contract, different evidence-driven outputs.** That is the generalization claim, demonstrated.

---

## What ships per discipline

Three output streams, plus four audit artifacts:

**Output A — Jira tree.** Validated stories organized by epic. Every story carries `tests[]`, `persona`, `stage`, `shape`, source citations, dependencies, cross-links, `theme_catalog_version`, and inherits `epic_analog` via parent epic.

**Output B — Configuration profiles.** Per-discipline-grouping YAML, partitioned by test. Schema deterministic per the static test catalog. `persona_owner` per section.

**Output C — Reference catalogs.**
- Theme catalog (`<discipline>_v1`) with inherited / novel / discarded entries and admission_decision blocks.
- Epic catalog (`<discipline>_epic_v1`) parallel structure.
- ANALOGY map (`{prior}_v1 ↔ {discipline}_v1`) with theme_links + epic_links computed by Discovery; test_links + persona_links static, supplied at onboarding.
- Static test catalog and persona catalog as reference outputs.

**Audit artifacts.**
- Quorum decision log — per-novelty audit trail showing N agents' votes and reasoning.
- Parked stories queue — failed-checks list per parked story.
- Drift report (weekly + on alarm trip).
_(SOP-level intake gate removed; chunk-level out-of-scope tagging is captured by the test tagger and surfaced in the audit log.)_

---

## Open questions / TBD

These are the deliberately-unresolved items the team should see in this artifact. Each lists the current default and what needs to happen to move it out of TBD.

### Calibration (need first-run telemetry)

- **τ_match and ε_novelty defaults.** Currently 0.65 / 3 for both Theme and Epic Discovery. May be too eager / too lazy depending on first-run distribution. Calibration: review the Cyto → Micro Theme Discovery output; if G0 > 10% over multiple cycles, raise τ_match. If novelties admit at low cluster sizes (< 5), consider raising ε_novelty.
- **Quorum size and threshold.** N=5, M=3 (simple majority) for vote count plus min-pairwise description-cosine ≥ 0.8 for substance. Defaults are reasoned but unmeasured. Tuning posture: if first-run admit-precision degrades materially (more than ~10% of admissions retroactively flagged in drift review), tighten to M=4; if it admits very rarely (G0 explodes), drop the convergence threshold to 0.75 before lowering M.
- **Description convergence threshold.** 0.8 cosine is a guess. Real first-run convergence values determine if this is too strict (admissions blocked on cosmetic phrasing) or too loose (semantic disagreement getting through).
- **Auto-park rate budget.** What % of stories landing in `parked` is acceptable? < 5% suggests rubric thresholds are well-tuned; 5–15% suggests rubric tightness; > 15% suggests miscalibration or out-of-scope content. Because there is no SOP-level intake gate, a sustained > 15% rate is the primary signal that an upstream batch may be off-scope.
- **Stage-theme correlation.** `lab_stage_v1` carries `typical_themes` per stage. If actual data shows tight correlations, the agent can use stage as a soft prior for theme; if loose, treat them independently.

### Operational (need decision before deployment)

- **Cross-version querying.** When two disciplines have different live theme catalogs (e.g., Micro on `cyto_v1` and Histo on `histo_v1`) and a query crosses both, does the retriever fan out across both catalogs and reconcile via the ANALOGY map, or does it pick one as primary? Default lean: primary-with-ANALOGY-fanout.
- **Re-tagging on catalog version bump.** Three options: (a) regenerate stories with the new `theme_catalog_version`; (b) update `themes[]` in place and bump `theme_catalog_version`; (c) leave old stories alone and only tag new ones. Default lean (b) — preserves story identity, updates resolution.
- **Drift report distribution.** Slack post, dashboard, Jira ticket, email? Affects who reviews it. Default lean: dashboard + weekly summary email.
- **Strict vs permissive mode default.** Strict (parked stories not in Output A) for new disciplines; switch to permissive only if parked-story volume is < 5%.
- **Alarm cooldown.** Max 1 alarm-triggered Discovery re-run per discipline per day (cost bound for the 5× quorum LLM calls).

### Implementation (need decision before code)

- **Jira integration mechanism.** Manual export (CSV upload), API push, or webhook? Affects Output A format.
- **Per-grouping profile granularity for multi-variant SOPs.** A single SOP may describe multiple specimen variants (e.g., voided / catheter / midstream urine). Each gets its own profile, or one profile with sub-keys?
- **Story-shape classifier training.** Validator routes by shape; classifier currently zero-shot off schema definitions. If zero-shot drift exceeds 5% in production telemetry, label disagreements from accepted Micro outputs (not from a prior-discipline holdout) and fine-tune.
- **Sub-stages within stage 4 (test_setup_execution).** Histology likely needs sub-stages (tissue processing / sectioning / staining); Cyto and Micro mostly don't. Add a `sub_stage` field if and when it becomes load-bearing for workflow-stage-split stories.
- **Choice of prior discipline.** When extending to a new discipline, who picks the prior? Defaults: lab-process-similarity heuristic (cyto for histo; micro for hema). Architect's call at onboarding.

### Stakeholder / compliance (need external input)

- **PHI handling policy.** Redact-and-index, restrict-route, or refuse? SOPs shouldn't contain PHI, but transcripts might. Compliance call needed.
- **Sample artifact access (now optional).** The mandatory inputs from the prior discipline are its theme catalog and epic catalog (small structured YAMLs, not Jira-export-dependent). Sanitized prior-discipline Jira is **only** needed to enable optional exemplar retrieval at story extraction time — a quality enhancement, not a prerequisite. New-discipline SOPs and the new-discipline catalogs (test, persona) remain required as before.
- **POC eval framework for generalization.** Single-discipline acceptance rate isn't the right metric. A generalization-focused eval needs: (a) per-discipline acceptance rate; (b) onboarding cost (architect-hours per new discipline); (c) catalog coherence (no spurious novel themes; no missed novelty against a held-out validation set). Framework TBD.

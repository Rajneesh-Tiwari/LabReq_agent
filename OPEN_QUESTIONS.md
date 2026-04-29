# Open Questions

Pending decisions or items awaiting stakeholder confirmation. Resolved items move to `DECISIONS.md` and get cross-referenced at the bottom of this file.

## Stakeholder / SME

- [ ] **LIMS technical context** — confirmed platform = **Connect** (D15). Still open: which Connect capabilities already exist for Micro vs. need to be built? POC operates under greenfield assumption (D15); v2 extension-mode requires a Connect capability inventory we don't have yet.
- [ ] **PHI handling policy** — redact-and-index, restrict-route, or refuse? SOPs shouldn't contain PHI, but transcripts might. Compliance call needed.
- [ ] **Cyto SME availability** — exemplar curation requires SME pairing on the first ~10 tuples. Estimated 1–2 days of focused SME time. Need this scheduled.
- [ ] **Sample artifacts access** — can sanitized Cyto Jira stories + Cyto SOPs (1–2 examples) be brought out of the office network for development?
- [ ] **Variation scope confirmation** — POC scope is **blood culture, urine culture, target-pathogen area** (3 SOPs). Confirm: any additional in-scope cultures? Any out-of-scope ones to explicitly exclude (e.g., molecular methods, AST, anaerobic chambers)?

## Architectural / technical

- [ ] **Multi-user / session model** — single-tenant POC for one SME, or multi-tenant with collaboration? Affects session-state design.
- [ ] **Bedrock Knowledge Bases vs. roll-our-own OpenSearch** — managed convenience vs. flexibility.
- [ ] **Jira integration mechanism** — manual export (CSV upload), API push, or webhook? Affects output format.
- [ ] **Confidence thresholds** — τ=0.7, θ=0.5 as initial defaults. Need telemetry on real queries to tune.
- [ ] **Cross-SOP synthesis recurrence threshold** — currently set at ≥2 SOPs to trigger a capability story (D11). With only 3 in-scope SOPs for the POC, this means *anything seen in 2 of 3* lifts. Is that too aggressive (will produce many capability stories)? Stricter alternative: ≥majority. Looser: ≥2 always. Revisit after first run.
- [ ] **Cyto-epic-equivalence annotation source** (D13) — does a SME pre-curate the Cyto↔Micro epic mapping, or does the Epic Extractor infer it from retrieval signal? Inference is cheaper but less reliable; SME-curated table is more authoritative but requires upfront work.
- [ ] **Story-shape classifier** — the Validator routes by shape (D7). Does the classifier need its own labeled training set, or can it run zero-shot off the schema definitions in D10? Recommendation: zero-shot first, label only the disagreements with SME.
- [ ] **Synthesis-revision loop** — when the synthesis pass adds a capability story (D11), should the Validator re-validate the *child* concrete stories for consistency with the parent (e.g., do all PHI-stage children reference the same field set)? Or are they independent once promoted? (The capability story itself does pass through the Validator at gate #2 per the corrected pipeline; this open question is about whether children are re-checked.)

- [ ] **Cross-SOP synthesis clustering mechanism** — D11 specifies clustering "by behavioral similarity" but not the mechanism. Options: (a) embedding similarity over story title + AC + source SOP excerpt; (b) explicit feature extraction (action verbs, AC field overlap, target object); (c) LLM-as-clusterer prompt asking "are these the same behavior?". (a) is fast/cheap but coarse; (b) is interpretable but needs feature design; (c) is expensive but most semantic. Default to (a) for prototype, validate against SME on first run.

- [ ] **4-shape coverage / escape hatch** — what happens when an SOP element doesn't fit any of the four shapes (capability / workflow-stage-split / configuration-instance / cleanup)? Plausible misfits: regulatory-compliance, non-functional/performance, external-integration. Currently no escape hatch — Validator would force misfit classification. Options: (a) add a 5th "other" shape with permissive rubric and mandatory SME review; (b) refuse extraction and flag for SME; (c) wait for evidence this is actually a problem before adding complexity.

- [ ] **Per-culture configuration profile granularity** — D12 emits one profile per culture type. But a single SOP may describe multiple specimen variants (e.g., voided / catheter / midstream urine). Each variant gets its own profile, or one profile with sub-keys? Affects profile schema design.

## Quality / governance

- [ ] **Validator rubric calibration** — type-aware sub-rubrics (D7) need SME calibration on ~10 stories per shape: which checks are too strict, which too lenient.
- [ ] **Story-acceptability bar — concrete examples per shape** — need: 5 "good" + 5 "rejected" examples for each of the four shapes (capability / workflow-stage-split / configuration-instance / cleanup), drawn from Cyto Jira where possible. Bar is shape-specific (D7) so the examples must be too.
- [ ] **Eval framework** — how do we measure improvement? Per-shape acceptance rate (% passing Validator without revision)? End-to-end SME-acceptance rate? Per-discipline coverage?
- [ ] **Configuration profile schema** — D12 sets YAML as default. Need: an actual schema for what fields a culture profile contains. Best derived from a worked example (urine culture profile filled in by SME) before generalizing.

## Deferred design choices

- [ ] **Tasks-as-output (deferred to v3.2 or later)** — D14 currently fixes Tasks as out-of-scope. If reversed later, three postures available: (A) titles + intent only; (B) constrained categories — automation / doc / acceptance-test, all Story-grounded so codebase access is not required; (C) full task generation with codebase access. Lean B if/when revisited. Current posture: validate v3.1 Story output first (NEXT_STEPS steps 7–11), don't pre-design Tasks. Reopens D14.

## Smaller architectural inconsistencies (from earlier QC pass)

- [ ] Slot 2 (Cyto analogy) when multiple older disciplines exist (Cyto + Histo) — split into 2a/2b or merge?
- [ ] Theme `unclassified` chunks — currently orphaned at retrieval; need admin review path or absorb into adjacent slot. *(Subsumed by the G0/E0 first-class promotion in `V3_2_SPEC.md` § 5.6 / D19 — review path becomes the Discovery Agent re-run triggered by the 5% alarm.)*
- [ ] Co-reference resolver — needs to know what type of artifact "epic 3" refers to (draft vs in-corpus epic).

## Larger architectural questions for v3.2 / v4

> **Status:** Three of the four questions below now have a draft answer in `V3_2_SPEC.md` (Conditioned Discovery — warm-start theme/epic bootstrap with prior). The questions remain *open* until the spec is ratified and the τ_match / ε_novelty defaults are calibrated against a real run, but they are no longer un-answered.

- [ ] **Theme cold-start for new disciplines.** v3.1 assumes themes G1–G8 are known upfront. They're load-bearing across the theme tagger, 8 precomputed centroid embeddings, intent-decode classifier (closed enum), ADJACENT retrieval slot ("centroid neighbors"), and the Epic schema. For Micro this is fine — Cyto's taxonomy bootstraps it. For a brand-new discipline (Histology, Hematology, Chemistry) without prior taxonomy, there's nothing to retrieve into and no labels for the classifier. Options for v3.2/v4:
  - **(A) Theme-discovery agent** that runs once per discipline before the main pipeline: read N representative SOPs → cluster → propose taxonomy → SME confirmation → emit theme config. Pipeline boots from that config. Recommended.
  - **(B) Layered themes** — keep G1–G3 (workflow stages: pre/analytic/post) as universal, replace G4–G8 with discipline-specific. Cleaner because workflow stages really are universal.
  - **(C) Themes-from-data** — cluster the corpus, label clusters post-hoc. Adaptive but unstable; Story.themes[] becomes a moving target.
  - Whichever path, themes should become **config-as-data with a versioned taxonomy**, not a closed enum baked into schemas.
  - **→ Addressed in `V3_2_SPEC.md` (§§ 4–5):** option A is taken with a conditioning twist — the discovery is *warm-start* against the existing prior catalog rather than pure cold-start, governed by τ_match / ε_novelty knobs. Versioned config-as-data is adopted (D18). Open: τ_match / ε_novelty calibration on a real run; Pass-1 scoring backend (cosine vs LLM-as-classifier vs hybrid).
- [ ] **Unclassified bucket as first-class concept.** Today it's an implicit fallback for low-confidence theme tagging. It's also doing unspoken work as the safety valve when the taxonomy doesn't match reality. Should be promoted to G0 with an alarm threshold (e.g., >5% chunk volume triggers SME review).
  - **→ Addressed in `V3_2_SPEC.md` (§ 5.6, D19):** G0 (theme) and E0 (epic) promoted to first-class with an explicit count + sample + 5% alarm threshold; alarm tripping re-runs the appropriate Discovery Agent.
- [ ] **Story DAG materialization.** The Story schema's `dependencies[]` and `cross_links[]` arrays already serialize a DAG, but it lives only as flat arrays. Worth deciding: do we surface this as a Jira link graph, persist it in a graph DB / join table, or just leave it implicit? Affects how Dependency Resolver's topological ordering is exposed for sprint planning. *(Not addressed by `V3_2_SPEC.md`; remains open.)*
- [ ] **Cross-discipline ANALOGY mapping.** Currently the ANALOGY slot assumes Cyto and Micro share a theme space. If themes diverge per discipline (option B or C above), ANALOGY needs an explicit theme-mapping table.
  - **→ Addressed in `V3_2_SPEC.md` (§ 5.5):** explicit ANALOGY map artifact with typed links (identical / partial / discarded_in_target / novel_in_target) at both theme and epic level. Drawio page "v3.2 ANALOGY Map" shows the cyto_v1 ↔ histo_v1 case visually. Open: cross-version querying behavior (fan-out vs primary-with-fanout) when two catalogs are live simultaneously.

## Resolved (moved out of open questions — cross-reference to decisions)

- ✅ How to handle ambiguous query intent → see D4 (4 explicit policies)
- ✅ Whether Cyto is a registry or a teaching corpus → see D5
- ✅ How many abstraction layers → see D6 (Epic → Story → Task; agent stops at Story)
- ✅ How to enforce story actionability → see D7 (type-aware Validator sub-rubrics)
- ✅ Whether to fine-tune or use exemplars → see D8 (exemplars)
- ✅ Story schema → see D9 (extended with `shape` field)
- ✅ How many story shapes / which abstraction level → see D10 (4 shapes; per-SOP replicates Cyto mix)
- ✅ Cross-SOP abstraction policy → see D11 (synthesis pass; concrete + abstract coexist)
- ✅ Configuration extraction format → see D12 (inline AC + per-culture YAML profile)
- ✅ Cyto-epic equivalence handling → see D13 (annotation, not structural)
- ✅ Tasks in scope or not → see D14 (out-of-scope; agent stops at Story)
- ✅ Platform name → see D15 (Connect; greenfield assumption)
- ✅ POC scope confirmation — Story-with-AC + per-culture configuration profile (D12, D14)

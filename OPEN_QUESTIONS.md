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
- [ ] Theme `unclassified` chunks — currently orphaned at retrieval; need admin review path or absorb into adjacent slot.
- [ ] Co-reference resolver — needs to know what type of artifact "epic 3" refers to (draft vs in-corpus epic).

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

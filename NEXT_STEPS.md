# Next Steps

Concrete actions, in order.

## Immediate

1. **Build new drawio pages 9–12** capturing the v3.1 agent-based architecture:
   - **Page 9 — Working Model:** SOP → Epic → Story (3-level Cyto Jira hierarchy with Tasks marked out-of-scope), the **four story shapes** (capability / workflow-stage-split / configuration-instance / cleanup) with one concrete example per shape, and the v3.1 story schema (including the `shape` and `cyto_epic_analog` fields).
   - **Page 10 — Agent Pipeline:** five agents — Epic Extractor → Story Extractor → Story Validator (type-aware) → Cross-SOP Synthesis → Dependency Resolver. Show batch boundary (synthesis runs after all SOPs are extracted) and the dual output streams (Stories + per-culture Configuration Profile).
   - **Page 11 — Validator Rubrics:** the four shape-specific sub-rubrics from D7, side-by-side. Plus the revise (×2) → SME-escalate flow with failed-checks visibility.
   - **Page 12 — Cross-SOP Synthesis & Exemplar Corpus:** synthesis trigger logic (cluster concrete stories across SOPs by behavioral similarity, ≥2-SOP recurrence threshold), exemplar curation flow, and the growth loop where accepted Micro outputs become future exemplars.
2. **Light edits to existing pages 1–8** — small annotations (not structural changes) re-labeling retrieval primitives as exemplar-retrieval consumers in the agent pipeline.

## Short-term

3. **Schedule Cyto SME pairing** to curate exemplar #1.
4. **Confirm Connect capability inventory** with Labcorp engineering — what already exists for Micro vs. needs to be built. Determines whether v2 extension-mode is viable now or stays deferred.
5. **PHI policy decision** with compliance.
6. **Confirm variation scope** — blood culture, urine culture, target-pathogen area is the working POC scope. Lock or expand.

## First experiment (after exemplar #1)

7. **Curate one Cyto exemplar per shape** — one capability, one workflow-stage-split, one configuration-instance, one cleanup. Pair with SME, capture (SOP excerpt → story tuple) at gold-standard level. Four total.
8. **Test Story Extractor on a *different* Cyto SOP** — sanity check that agent + 4 exemplars (one per shape) reproduces SME-quality extraction across the shape mix.
9. **Test Story Extractor on the urine culture Micro SOP** — first real Micro run. Eyeball output for actionability and shape distribution. Identify gaps.
10. **Run Cross-SOP Synthesis pass on 2+ Micro SOPs** — verify capability stories emerge defensibly from recurrence (only after at least urine + blood SOP runs are in).
11. **Calibrate the Validator sub-rubrics** with the SME from steps 8–10. Tune per shape.

## Mid-term (after first experiment validates the approach)

12. **Scale exemplar corpus to ~15–25** based on what gaps the first run reveals — distribute across the four shapes proportionally to observed Cyto frequency.
13. **Build the agent pipeline as code** (Bedrock + OpenSearch + Lambda + DynamoDB). Five agents wired with the type-aware Validator.
14. **Set up telemetry + eval signal** — per-shape acceptance rate, cross-SOP synthesis precision (how often synthesized capability stories survive SME review), τ/θ tuning.
15. **Run on full Micro SOP corpus for the POC scope** (3 SOPs: urine, blood, target pathogens) and produce first end-to-end Jira batch + per-culture configuration profiles.

## Decisions to make before code starts

These are blockers for implementation; tracked in `OPEN_QUESTIONS.md`:

- [ ] PHI handling policy (blocker for ingestion privacy filter)
- [ ] Multi-user / session model
- [ ] AWS deployment topology (managed Bedrock KB vs. roll-our-own)
- [ ] Jira integration mechanism (CSV upload / API push / webhook)
- [ ] Cross-SOP synthesis recurrence threshold (default ≥2 SOPs, may need stricter)
- [ ] Cyto-epic-equivalence annotation source (SME-curated table vs. agent-inferred)

## Cadence for updates

- Update `PROGRESS.md` after each meaningful milestone (new diagrams, decisions, exemplar curation, first agent runs).
- Move resolved items from `OPEN_QUESTIONS.md` into `DECISIONS.md` with a new D-number.
- Strike completed items from this file with a date annotation.

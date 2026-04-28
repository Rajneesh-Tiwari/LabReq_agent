# Next Steps

Concrete actions, in order.

## Immediate

1. **Build new drawio pages 9–12** capturing the agent-based architecture:
   - Page 9: Working Model (SOP → Epic → Story, vague-vs-actionable example, story schema)
   - Page 10: Agent Pipeline (Epic Extractor → Story Extractor → Validator → Dependency Resolver)
   - Page 11: Story Validator Rubric (explicit checks + revise/escalate logic)
   - Page 12: Cyto Exemplar Corpus (curation, storage, retrieval, growth loop)
2. **Light edits** to existing pages 1–8 to re-contextualize retrieval primitive use in the new pipeline (small annotations, not structural changes).

## Short-term

3. **Schedule Cyto SME pairing** to curate exemplar #1.
4. **Confirm LIMS technical context** with Labcorp engineering.
5. **PHI policy decision** with compliance.

## First experiment (after exemplar #1)

6. **Curate one Cyto exemplar** — pick a Cyto SOP with well-validated Jira stories, pair with SME, capture (SOP excerpt → story tuple) at gold-standard level.
7. **Test Story Extractor on a *different* Cyto SOP** — sanity check that agent + 1 exemplar reproduces SME-quality extraction.
8. **Test Story Extractor on a Micro SOP** — first real run. Eyeball output for actionability. Identify gaps.
9. **Calibrate the Validator rubric** with the SME from steps 7 and 8.

## Mid-term (after first experiment validates the approach)

10. **Scale exemplar corpus to ~10–20** based on what gaps the first run reveals.
11. **Build the agent pipeline as code** (Bedrock + OpenSearch + Lambda + DynamoDB).
12. **Set up telemetry + eval signal** so we can tune τ, θ, and validator rubric from real data.
13. **Run on full Micro SOP corpus** (~10–30 SOPs) and produce first end-to-end Jira story batch.

## Decisions to make before code starts

These are blockers for implementation; tracked in `OPEN_QUESTIONS.md`:

- [ ] LIMS technical context (blocker for Configuration Extractor scope)
- [ ] PHI handling policy (blocker for ingestion privacy filter)
- [ ] Multi-user / session model
- [ ] AWS deployment topology (managed Bedrock KB vs. roll-our-own)
- [ ] Jira integration mechanism

## Cadence for updates

- Update `PROGRESS.md` after each meaningful milestone (new diagrams, decisions, exemplar curation, first agent runs).
- Move resolved items from `OPEN_QUESTIONS.md` into `DECISIONS.md` with a new D-number.
- Strike completed items from this file with a date annotation.

# Open Questions

Pending decisions or items awaiting stakeholder confirmation.

## Stakeholder / SME

- [ ] **LIMS technical context** — which LIMS is being configured for Microbiology? Beaker? Epic? Custom? Affects what the Configuration Extractor can produce. May determine whether POC stops at *Story with AC* or extends to *Configuration steps*.
- [ ] **PHI handling policy** — redact-and-index, restrict-route, or refuse? SOPs shouldn't contain PHI, but transcripts might. Compliance call needed.
- [ ] **Cyto SME availability** — exemplar curation requires SME pairing on the first ~10 tuples. Estimated 1–2 days of focused SME time. Need this scheduled.
- [ ] **POC scope confirmation** — Story-with-AC as the deliverable, or push through to Configuration step?
- [ ] **Sample artifacts access** — can sanitized Cyto Jira stories + Cyto SOPs (1–2 examples) be brought out of the office network for development?

## Architectural / technical

- [ ] **Multi-user / session model** — single-tenant POC for one SME, or multi-tenant with collaboration? Affects session-state design.
- [ ] **Bedrock Knowledge Bases vs. roll-our-own OpenSearch** — managed convenience vs. flexibility.
- [ ] **Jira integration mechanism** — manual export (CSV upload), API push, or webhook? Affects output format.
- [ ] **Confidence thresholds** — τ=0.7, θ=0.5 as initial defaults. Need telemetry on real queries to tune.
- [ ] **Edge cases for Micro-only topics** — AST, MALDI-TOF, anaerobic cultures have no Cyto exemplar. How does the agent handle gracefully? Currently planned: extract anyway, mark low-confidence, escalate to SME.

## Quality / governance

- [ ] **Validator rubric calibration** — initial rubric needs SME calibration on ~10 stories: which checks are too strict, which too lenient.
- [ ] **Story-acceptability bar** — concrete examples needed: 5 "good" stories and 5 "rejected" stories with reasons, both for Cyto (validation) and Micro (early output).
- [ ] **Eval framework** — how do we measure that the system is improving? Golden query set? Per-discipline success metrics?

## Smaller architectural inconsistencies (from earlier QC pass)

- [ ] Slot 2 (Cyto analogy) when multiple older disciplines exist (Cyto + Histo) — split into 2a/2b or merge?
- [ ] Theme `unclassified` chunks — currently orphaned at retrieval; need admin review path or absorb into adjacent slot.
- [ ] Co-reference resolver — needs to know what type of artifact "epic 3" refers to (draft vs in-corpus epic).

## Resolved (moved out of open questions — cross-reference to decisions)

- ✅ How to handle ambiguous query intent → see D4 (4 explicit policies)
- ✅ Whether Cyto is a registry or a teaching corpus → see D5
- ✅ How many abstraction layers → see D6 (two: Epic → Story)
- ✅ How to enforce story actionability → see D7 (Validator rubric)
- ✅ Whether to fine-tune or use exemplars → see D8 (exemplars)

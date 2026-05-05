# Proposed Decisions — v3.4

Companion to `V3_4_SPEC.md`. Decisions D20–D25 in the format used by `DECISIONS.md`, ready to lift-and-paste into the main log when ratified.

`V3_4_SPEC.md` is the architectural justification; this file is the entry-format mirror.

---

## D20 — Static catalogs for tests and personas; no discovery on either dimension
**Date:** 2026-05-05

**Decision:** Test catalog (`<discipline>_test_v<N>`) and persona catalog (`<discipline>_persona_v<N>`) are static reference YAML inputs, supplied at project start. Closed enums fed to agents and Validator. The Story schema gains:

- `tests[]` — values drawn from `<discipline>_test_v<N>`. Empty allowed.
- `persona` — single value drawn from `<discipline>_persona_v<N>`. Required for capability and workflow-stage-split shapes; optional (nullable) for configuration-instance and cleanup.

No conditioned discovery, no τ_match/ε_novelty knobs, no novelty alarms for these dimensions. ANALOGY map's `test_links` and `persona_links` are also static one-time inputs.

**Rationale:** The discipline's tests and personas are stable organizational facts — they don't drift over POC timeframes, and they're enumerable upfront. Treating them as discoverable adds machinery without payoff. Closed enums sharpen Validator checks (hard rejects on enum violations) and tighten cross-SOP synthesis clustering (test + persona become explicit grouping axes alongside shape and behavior).

**Implications:**
- Validator gains closed-enum consistency checks that run before the shape-specific sub-rubric. Enum violations are hard rejects (no revise loop) — either re-extraction picks valid values, or the issue escalates as a scope problem (D25).
- Cross-SOP synthesis clusters along `(test, persona, shape, behavior)` — sharper than v3.2's behavior-only signal. Capability stories' parameter lists become cleaner: dimensions constant within the cluster (test, persona, shape) become fixed labels; varying dimensions become parameters.
- Per-culture YAML profile (D12) schema becomes deterministic — sections pre-declared per test, with `persona_owner` per section.
- Exemplar retrieval becomes (test, persona, shape)-targeted at the tuple level for tighter few-shot.

**Alternatives considered:**
- Conditioned discovery for tests + personas (rejected — over-engineered for static dimensions; adds two discovery domains without payoff).
- Free-text `tests` / `persona` fields (rejected — loses Validator leverage and cross-SOP clustering precision).

---

## D21 — Multi-agent quorum replaces SME ratification at every novelty admission gate
**Date:** 2026-05-05

**Decision:** Theme Discovery Pass 3 and Epic Discovery Pass 3 invoke a multi-agent quorum (default N=5 agents, M=4 agreement threshold) instead of an SME reviewer. Independence is enforced via prompt-frame diversity (5 distinct reasoning angles) with optional model diversity. Admission requires:

- ≥ M agents return `admit`, AND
- description-convergence cosine ≥ 0.8 across the M admit-voters' synthesized one-liners.

Otherwise the cluster is parked to G0 (theme) or E0 (epic) — not admitted, not folded-in, deferred to the next alarm cycle. A separate quorum mode (`fold-in` consensus) handles the case where ≥ M agents agree the cluster is a near-duplicate of an existing entry.

**Rationale:** Discovery runs rarely (once per discipline + on alarm trip), so 5× LLM cost is acceptable. Independent prompt frames catch different failure modes — coherence (Agent 1), distinctness vs. existing entries (Agent 2), description sharpness (Agent 3), member behavioral consistency (Agent 4), taxonomy fragmentation (Agent 5). M-of-N filters single-agent overconfidence. The quorum decision log is auditable; later non-SME human review can re-assess admissions without re-running the pipeline.

**Implications:**
- Catalog schemas replace `sme_confirmed: bool` + `sme_notes: string` with an `admission_decision` block recording the panel's votes, reasoning excerpts, description convergence score, and final decision.
- Inherited entries with `auto_inherited: true` (match_score ≥ τ_match against prior) skip the quorum entirely.
- Discarded themes (parent-catalog themes that don't apply) get a separate quorum prompt: "should this prior theme survive in the new catalog?" — same M-of-N rule.

**Tuning knobs:** N (panel size), M (threshold), description-convergence cosine threshold. Defaults are guesses; first-run telemetry calibrates. If G0 explodes after first run → lower M to 3-of-5. If catalog pollutes → raise to 5-of-5 or N to 7.

**Alternatives considered:**
- Single-agent classifier (rejected — single point of failure, no audit dimension).
- LLM-as-judge with one large agent (rejected — same single-point issue).
- Self-consistency over a single agent's repeated samples (rejected — same model, same prompt, no genuine independence).

---

## D22 — Auto-park replaces SME escalation at the Validator gate
**Date:** 2026-05-05

**Decision:** After 2 failed Validator revisions, stories transition to `quality: parked` and land in a separate `parked/` queue with their failed-checks list (`parked_reason: string[]`) visible. They do **not** reach Output A in strict mode (default). The pipeline does not block. Periodic non-SME review (architect / PM) can triage parked queue volume and surface systemic Validator-rubric issues.

**Modes:**
- **Strict (default for POC):** parked stories are not in Output A. Recall lost; precision preserved.
- **Permissive (switchable):** parked stories reach Output A flagged `quality: review_needed`. Recall preserved; dev team must triage.

**Rationale:** With no SME, escalation has no human target. Auto-park preserves precision (parked stories don't pollute Jira) at the cost of recall (some good stories may be parked when the rubric mishandles edge cases). Strict-mode default reflects POC priority of "ship clean output" over "ship comprehensive output" — trust erosion from a polluted Jira hurts more than recall loss.

**Implications:**
- Story schema gains `quality ∈ {passed, parked}` and `parked_reason?: string[]`.
- New artifact `parked/<run_id>/<story_id>.yaml` per parked story, including the original SOP excerpt and the Validator's verdict.
- Drift report (D24) summarizes parked-story volume per shape per culture per run.
- Closed-enum violations (test/persona not in catalog) short-circuit the 2-revision loop — they're either re-extraction-fixable (label mismatch) or scope-violation escalations (D25). Only shape/AC issues consume revision attempts.

**Alternatives considered:**
- Permissive mode as default (rejected for POC — trust over recall; switchable later).
- Auto-revise to N>2 attempts (rejected — diminishing returns; usually fails again on the same edge).
- Discard parked stories silently (rejected — no audit trail; can't retrospectively review rubric calibration).

---

## D23 — Cyto-as-oracle for exemplar bootstrap and rubric calibration
**Date:** 2026-05-05

**Decision:** Cyto Jira's existing SME-validated stories are the exemplar oracle. Two applications:

**(a) Exemplar bootstrap.** Filter Cyto stories by quality signals: non-empty AC list, linked test cases, no `WIP` / `draft` status tags, source citations resolve, status not new/backlog. Trace each surviving story to its source SOP excerpt via `source_citations[]`; if missing, use retrieval over Cyto SOPs to find the most-likely originating excerpt. Resulting (excerpt → story) pairs become the exemplar corpus, tagged with their (test, persona, shape) tuple at ingestion for precision-targeted retrieval.

**(b) Rubric calibration.** Hold out 20% of Cyto stories per shape as a calibration set. Run Validator's shape-specific sub-rubric over the holdout. Tune thresholds (AC granularity cutoffs, "concrete value" detector cutoffs, etc.) until acceptance rate on the holdout is ≥ 95%.

**Rationale:** Cyto Jira has been through Cyto's own SME review process; the surviving stories are by definition gold-standard for the shape mix the system needs to learn. Eliminates active SME pairing on exemplar curation (D8 loop) and on rubric tuning. Holdout-based calibration ports the Cyto quality bar to the automated Validator without per-story labels.

**Caveat:** Depends on Cyto Jira accessibility — existing OPEN_QUESTIONS item ("can sanitized Cyto Jira stories be brought out of the office network for development?"). Becomes load-bearing under v3.4: without sanitized Cyto Jira access outside the office network, the exemplar oracle has no source. Possible fallback: synthetic exemplars from Cyto SOPs constructed by an upfront LLM pass — lower quality but unblocks development.

**Caveat 2:** Cyto stories may not perfectly cover all four shapes evenly; cleanup and configuration-instance shapes may be under-represented. For under-represented shapes, fall back to manually-specified rubrics (the v3.2 baseline) until enough Micro accepted outputs accumulate to backfill.

**Alternatives considered:**
- Ground-up exemplar curation by SME (blocked — no SME available).
- Synthetic-only exemplar corpus generated from SOPs (rejected as primary — risks reinforcing the agent's own biases without a quality anchor; acceptable as fallback if Cyto Jira blocked).

---

## D24 — G0/E0 alarm response: auto-rerun with τ_match −0.05; floor at 0.50; drift report for non-SME review
**Date:** 2026-05-05

**Decision:** When G0 (theme) or E0 (epic) bucket exceeds 5% rolling-window volume:
1. Automatically re-run the appropriate Discovery agent with `τ_match` lowered by 0.05 (more eager to inherit).
2. New candidates from the re-run go through the standard multi-agent quorum (D21).
3. Repeated alarm trips compound the lowering, with a floor of `τ_match = 0.50`.
4. Below the floor, auto-rerun **stops**. The drift report flags the discipline for manual catalog re-curation. Manual re-curation is a code-change to the catalog YAML, not a runtime SME action — anyone with repo access can perform it.

A weekly drift report is auto-generated containing:
- Quorum decisions (admitted / folded-in / parked, with vote tallies).
- Parked-story counts per shape per culture per run.
- G0/E0 bucket sizes and 4-week trend.
- Alarm trips and threshold-tightening events in the period.
- Catalog version bumps in the period.
- Per-SOP intake stats: accepted, scope-rejected, in-flight.

The drift report is **informational** — nothing in the pipeline waits on it. Reviewable by architect, PM, or dev lead.

**Rationale:** v3.2 said SME reviews the bucket and re-runs Discovery on alarm. With no SME, the system must self-respond. Threshold-tightening is the natural response — the bucket grew because prior-catalog matches were too strict. Bounded tightening (floor at 0.50) prevents drift compounding indefinitely. Visibility via the drift report is the second line of defense against silent quality erosion.

**Implications:**
- Alarm cooldown: max 1 alarm-triggered re-run per discipline per day (cost bound for the 5× quorum LLM calls).
- Drift report distribution: emit to a known channel (Slack, dashboard, or Jira ticket) so it doesn't go silently unread. Specific channel TBD.
- The 5% threshold is unchanged from V3_2_SPEC.md D19; rolling window definition unchanged.

**Alternatives considered:**
- Park alarm-trip Discovery without re-run, just log and wait for manual action (rejected — accumulates G0 mass with no recovery path).
- Larger τ_match decrement per trip (rejected — risk of over-correction admitting noise).
- Smaller decrement (rejected — alarm trips persist longer, fatigue).

---

## D25 — Intake scope-check: SOPs with <80% in-scope test references rejected at intake
**Date:** 2026-05-05

**Decision:** SOP arrival triggers a test-tag scan against the closed test catalog (D20). The intake gate computes the fraction of SOP test references that resolve to in-catalog entries:

- **Fraction < 80%** → reject SOP at intake with structured reason: `out_of_scope: too_many_unrecognized_tests`. Reject is final; no agent runs on the SOP.
- **Fraction ≥ 80%** → SOP passes intake. Out-of-catalog test references at the chunk level are tagged `test: out_of_scope` and excluded from Story Extractor input. The agent only sees in-scope content.

**Rationale:** Without an SME to confirm scope, intake must enforce it automatically. Otherwise an out-of-scope SOP — say, a molecular-pathology SOP delivered by mistake — would silently drag novel content into the pipeline, pollute the catalogs, and degrade outputs. The 80% threshold balances false-rejection (a legitimately in-scope SOP that mentions adjacent tests) against false-acceptance (an out-of-scope SOP slipping through). Threshold is tunable.

**Implications:**
- Rejected SOPs are logged with their reason; the drift report (D24) summarizes intake rejections per period.
- Test tagger (chunk enrichment) is the same closed-enum classifier reused at SOP-aggregate level for intake.
- A reviewer noticing a high rate of intake rejections can adjust the test catalog (manual re-curation) or lower the threshold.

**Alternatives considered:**
- Soft-warn instead of reject (rejected — silent acceptance defeats the purpose).
- Reject at chunk level only, accept SOP wholesale (rejected — under-classified chunks at scale create the same novelty pollution problem).
- Higher threshold (e.g., 95%) for stricter scope (deferred — start at 80%, tighten if false-acceptance is observed).

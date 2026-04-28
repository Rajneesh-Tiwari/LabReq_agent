# Architectural Decisions Log

Format: each decision has a date, the decision itself, the rationale, and the alternatives considered.

---

## D1 — Hybrid retrieval (BM25 + Dense + RRF), not pure semantic
**Date:** 2026-04-27

**Decision:** Use both sparse (BM25) and dense (Bedrock Titan / Cohere) retrieval, fused via Reciprocal Rank Fusion. Cross-encoder rerank on top.

**Rationale:** Clinical SOPs contain many exact-token signals (ICD codes, organism names, regulatory citations like CLIA §493.1252). Pure dense embeddings collapse these into adjacent-but-distinct neighborhoods. Dense alone also fails on negation (*"rejected if not refrigerated"* embeds the same as *"accepted if refrigerated"*). BM25 catches the literals; dense catches paraphrase intent.

**Alternatives considered:** Pure dense (rejected — fails on codes and negation); pure sparse (rejected — fails on paraphrase).

---

## D2 — Multi-slot retrieval with role labels
**Date:** 2026-04-27

**Decision:** Five retrieval slots — PRIMARY (in-theme target), ANALOGY (Cyto), ADJACENT (neighbor themes), EXEMPLAR (Jira), REG (regulatory) — each with explicit role labels carried into the LLM prompt.

**Rationale:** A single retrieval pass mixes evidence types and the LLM can't distinguish source-of-truth from analogy. Role-labeled slots let the LLM treat each chunk appropriately.

---

## D3 — Theme prior is soft, not hard
**Date:** 2026-04-27

**Decision:** The 8 Cytology themes (G1–G8) serve as a soft prior in the system prompt and as multi-label tags on chunks/epics, not as a forced taxonomy. New themes can emerge.

**Rationale:** Microbiology may legitimately need themes Cyto doesn't have (e.g., AST). Hard taxonomy would force mis-bucketing.

---

## D4 — Four explicit policies for query routing
**Date:** 2026-04-27

**Decision:**
- **P1 — Default discipline:** when unspecified, default to active POC discipline (Micro), tag output, allow override.
- **P2 — Out-of-corpus:** refuse to hallucinate when discipline absent from corpus; respond with 3 options (upload SOPs / draft from analogy with caveat / clarify scope).
- **P3 — Vague query:** ask structured clarifying question; don't retrieve.
- **P4 — Thresholds:** τ=0.7 (intent confidence), θ=0.5 (retrieval relevance). Tunable from telemetry.

**Rationale:** Without explicit policies, the system's behavior on edge cases is implicit and inconsistent.

---

## D5 — Cyto reframed: teaching corpus, not registry
**Date:** 2026-04-28

**Decision:** Cyto data functions as curated exemplars that train the agents (via few-shot prompting and dynamic exemplar retrieval), not as a registry to match Micro outputs against.

**Rationale (per stakeholder feedback):** The goal is to *learn from Cyto patterns and produce Micro outputs natively*, not to inherit Cyto artifacts. This eliminates capability-matching ambiguity, generalizes to future disciplines (Histology, etc.), and matches how few-shot LLM systems actually work.

**Implication:** No "REUSE / ADAPT / NEW" tagging on output. Output is pure Micro artifacts. Cyto's footprint is the exemplar corpus, not a matching layer.

**Alternative considered:** Capability matching with delta map (rejected — too much SME burden on capability equivalence judgments).

---

## D6 — Two-layer hierarchy: Epic → Story (story is the deliverable)
**Date:** 2026-04-28

**Decision:** Collapse the earlier 4-layer model (SOP → Capability → Requirement → Configuration) to two: SOP → Epic → Story. Story is the actual deliverable to dev teams.

**Rationale:** Client requirement — *"clear, unambiguous stories that can be acted upon by dev teams."* The 4-layer abstraction was useful for thinking but the dev team only acts on stories. Capabilities collapse into epics (organizing layer). Requirements fold into story description + AC. Configurations either embed in stories (as AC details) or get left to dev judgment.

---

## D7 — Story Validator with rubric is the quality gate
**Date:** 2026-04-28

**Decision:** Every generated story passes through a Validator agent (Haiku-class) that checks against an explicit rubric:
- AC use MUST/SHALL, not "should/may"
- Each AC is testable (specific values, observable outcomes)
- No ambiguous quantifiers ("appropriate", "relevant", "necessary")
- Source citation present and resolves
- Scope estimable (S/M/L)
- Edge cases / error paths enumerated

Two revision attempts allowed before SME escalation.

**Rationale:** The actionability bar can only be enforced *structurally*. Without the validator, the system produces plausible-but-vague output that erodes dev team trust.

---

## D8 — Few-shot exemplar approach, not fine-tuning
**Date:** 2026-04-28

**Decision:** Agents are configured via curated exemplar corpus + dynamic exemplar retrieval + structured output schemas. No model fine-tuning for POC.

**Rationale:** Exemplar-driven prompting gets us 80%+ of the way at a fraction of the cost and complexity. Iterates in hours. Bedrock Anthropic fine-tune options are limited anyway. Fine-tuning is "option 6" if exemplar approach plateaus.

---

## D9 — Story schema as the contract
**Date:** 2026-04-28

**Decision:** Define a strict schema for the Story artifact: `{id, epic_id, title, description, acceptance_criteria[], source_citations[], dependencies[], technical_hints?, estimated_complexity, edge_cases_handled[], status, source_chunks[]}`. Each AC has structure: `{when, then, expected_value?}`.

Anything that doesn't fit is rejected at extraction time.

**Rationale:** Schema enforcement is how we *structurally* prevent vague stories from reaching the SME. The schema itself encodes the actionability bar.

# Architectural Decisions Log

Format: each decision has a date, the decision itself, the rationale, and the alternatives considered. When a later decision refines an earlier one, the earlier entry has an **Updated** note pointing forward.

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

## D6 — Jira hierarchy: Epic → Story → Task; agent stops at Story
**Date:** 2026-04-28 *(updated later same day after reviewing real Cyto Jira)*

**Decision:** The Jira hierarchy is **three levels**: Epic → Story → Task. The agent's deliverable is **Epics + Stories** only. Tasks are **out-of-scope** for the agent (see D14).

**Rationale:** Direct evidence from Cyto's Jira backlog confirms a 3-level structure. Tasks reference test IDs, lib versions, internal validators, and other implementation-detail the agent cannot responsibly fabricate. Stories are where dev intent is captured at a level abstract enough for the agent to produce defensibly. Capabilities collapse into Epics (organizing layer); requirements fold into Story description + AC; configurations get their own stream (D12).

**Previously:** Earlier same-day framing was "two-layer" (Epic → Story). The 3-level reality was confirmed by Cyto Jira screenshots; the agent's *scope* remains Epic + Story but the platform's full hierarchy is acknowledged.

---

## D7 — Story Validator with type-aware rubric is the quality gate
**Date:** 2026-04-28 *(updated later same day to be type-aware)*

**Decision:** Every generated story passes through a Validator agent (Haiku-class). The Validator first **classifies the story shape** (one of: capability / workflow-stage-split / configuration-instance / cleanup — see D10) and then applies a **shape-specific sub-rubric**:

- **Capability shape:** AC use MUST/SHALL; parameters explicit; configurability boundaries called out; observable outcomes per AC; no ambiguous quantifiers; scope estimable (S/M/L); source citation present and resolves.
- **Workflow-stage-split shape:** stage explicit in title; stage-specific behavior testable; sibling stories enumerated and cross-linked; entry/exit conditions for the stage observable.
- **Configuration-instance shape:** concrete values present (no "appropriate"); target config table named; source SOP excerpt cited verbatim; values typed (units / enums); no MUST/SHALL pretense (this isn't capability language).
- **Cleanup/correction shape:** target artifact (id/path/screen) named; before/after observable; regression risk acknowledged; links to the artifact being modified.

Two revision attempts allowed, then SME escalation with the failed checks shown.

**Rationale:** A single rubric over-fits to capability stories and rejects perfectly good configuration-instance and cleanup stories that don't (and shouldn't) read with MUST/SHALL. The actionability bar is shape-dependent; the Validator must enforce it shape-by-shape.

**Previously:** A single MUST/SHALL-centric rubric was the original D7. After reviewing real Cyto Jira shapes, this was generalized.

---

## D8 — Few-shot exemplar approach, not fine-tuning
**Date:** 2026-04-28

**Decision:** Agents are configured via curated exemplar corpus + dynamic exemplar retrieval + structured output schemas. No model fine-tuning for POC.

**Rationale:** Exemplar-driven prompting gets us 80%+ of the way at a fraction of the cost and complexity. Iterates in hours. Bedrock Anthropic fine-tune options are limited anyway. Fine-tuning is "option 6" if exemplar approach plateaus.

---

## D9 — Story schema as the contract (extended for shape)
**Date:** 2026-04-28 *(extended later same day to carry `shape` field)*

**Decision:** Strict schema for the Story artifact:

```
{
  id, epic_id, shape ∈ {capability, workflow-stage-split, configuration-instance, cleanup},
  title, description,
  acceptance_criteria[],          // each AC: {when, then, expected_value?}
  source_citations[],             // SOP excerpt id + line range
  dependencies[],                 // other story ids
  cross_links[],                  // sibling stories (e.g., stage-split siblings) and capability-parent
  technical_hints?,
  estimated_complexity ∈ {S,M,L},
  edge_cases_handled[],
  status,
  source_chunks[],
  cyto_epic_analog?               // optional annotation, see D13
}
```

Anything that doesn't fit is rejected at extraction time. The `shape` field drives Validator routing (D7).

**Rationale:** Schema enforcement is how we *structurally* prevent vague stories from reaching the SME. The schema itself encodes the actionability bar. The `shape` field makes the bar shape-aware.

---

## D10 — Stories have four shapes; per-SOP extraction replicates the Cyto mix
**Date:** 2026-04-28

**Decision:** Stories are typed by **shape**, with four allowed values:

1. **Capability** — describes a configurable system feature. Example pattern: *"As {role}, I want {feature} so that {benefit}; the system MUST support configuration of {params}."*
2. **Workflow-stage-split** — same underlying capability, decomposed by workflow stage. One story per stage. Example pattern observed in Cyto: PHI Update *Before Work Has Started* / *After Work Has Started* / *After Results Are Reported* — three stories, one capability.
3. **Configuration-instance** — concrete values for a specific lab / culture profile. Example pattern: *"Lab setup: accession and lab code combination to identify {Connect Cytology / Connect Microbiology} orders per Lab."*
4. **Cleanup/correction** — modifies an existing artifact. Example pattern: *"Need to remove Result Bucket option from Add/Modify QT code screens."*

**Per-SOP extraction follows option A — replicate the Cyto mix.** The Story Extractor produces stories at whichever shape best matches each SOP element. It does **not** lift to a single capability story per SOP. Output of any single SOP looks shape-for-shape like Cyto's existing backlog.

**Rationale:** Real Cyto Jira evidence shows stories live across all four shapes. Forcing one abstraction level (e.g., always-capability) would not match how the dev team plans sprints, and would obscure stage-specific testability. Replicating the mix is more work for the agent but produces output the dev team can consume without re-decomposition.

**Alternatives considered:**
- Option B (normalize to capability + configuration only) — rejected as breaking dev team's planning rhythm.
- Option C (replicate mix per-SOP *and* lift in-SOP) — rejected as risk of agent fabricating capability boundaries from a single source.

---

## D11 — Cross-SOP synthesis lifts capability stories on recurrence; concrete + abstract coexist
**Date:** 2026-04-28

**Decision:** A **cross-SOP synthesis pass** runs **after all in-scope SOPs have been extracted** (batch, not progressive). It clusters concrete stories across SOPs by behavioral similarity and, for clusters of size ≥ 2, emits an additional **capability-shaped story** that abstracts the variable parts as parameters. Both the per-SOP concrete stories **and** the synthesized capability story are kept and pushed to Jira. Cross-links are recorded (capability story → child concrete stories; child concrete stories → parent capability story).

**Rationale:** Abstraction is only defensible when grounded in cross-SOP evidence. A single SOP cannot reveal which details are variable vs. fixed. Coexistence (rather than supersession) preserves the granular sprint-ready stories the dev team needs while giving the architecture team a capability anchor for platform planning.

**Open:** Recurrence threshold (≥2 SOPs vs. majority vs. all). Currently set at ≥2 for the 3-SOP POC; revisit with telemetry. See `OPEN_QUESTIONS.md`.

---

## D12 — Configuration extraction: inline AC + per-culture profile artifact
**Date:** 2026-04-28

**Decision:** Configuration values surfaced from each SOP are emitted on **two channels**:

- (a) **Inline in the related capability story's AC** — for traceability (e.g., AC: *"when urine profile is loaded, centrifuge step uses {speed: 1500g, duration: 5min}"*).
- (b) **A separate per-culture configuration profile artifact** — YAML (or spreadsheet, if SME prefers) — as the source-of-truth for what values populate the platform for each culture type. One artifact per culture type (urine, blood, target pathogens for the POC).

**Rationale:** Inline alone makes the configs hard to operate on (no single-source view). Profile-only loses the link between the capability story and its concrete values. Both channels solve the dual need.

**Format:** YAML default, with field `cyto_epic_analog` available where relevant (D13). Each value typed (units / enums / nullable) with citation back to the SOP excerpt.

---

## D13 — Cyto-epic equivalence captured as annotation, not structural mapping
**Date:** 2026-04-28

**Decision:** Where a Micro epic appears to mirror a Cyto epic (e.g., Micro Billing ↔ Cytology Billing), the equivalence is recorded as an **optional annotation field** on the Micro epic (`cyto_epic_analog: <cyto-epic-id>`), populated by the Epic Extractor when retrieval signal supports it. It is **not** a structural mapping that drives downstream behavior.

**Rationale:** A structural mapping would couple Micro generation to Cyto's epic taxonomy and break when Histology arrives with different domain shape. Annotation pays off for: (i) human reviewers seeing the mental map, (ii) future v2 extension-mode where the agent diffs against existing Connect platform capabilities and only proposes deltas. It does not constrain the current generation logic.

---

## D14 — Tasks are out-of-scope for the agent
**Date:** 2026-04-28

**Decision:** The agent does not generate Jira Tasks. The handoff to dev teams is at the **Story** level. Dev teams decompose stories into tasks themselves once they have visibility into the codebase.

**Rationale:** Real Cyto Tasks reference test IDs, internal lib versions, validator implementations, DB column names, and other impl-specific detail the agent cannot responsibly fabricate. Generating Tasks would either produce hallucinated implementation choices or duplicate the dev team's own decomposition work. Stopping at Story preserves agent value (specification) without overreach into implementation.

---

## D15 — Platform name is "Connect"; greenfield assumption with deferred extension-mode
**Date:** 2026-04-28

**Decision:** Labcorp's LIMS platform is named **Connect**. Cyto runs on Connect today (existing system); Micro is being built on Connect. The POC operates under a **greenfield assumption** — the agent generates all stories needed to build the Micro experience on Connect, including capabilities that already exist in Connect-Cyto. A v2 **extension-mode** (where the agent diffs against existing Connect-Cyto capabilities and emits only deltas / Micro-specific extensions) is deferred.

**Rationale:** Greenfield is simpler to evaluate and demo. Extension-mode requires a Connect capability inventory the agent doesn't currently have access to. The annotation in D13 keeps the door open for extension-mode without coupling the current build to it.

**Implication:** Stories will reference "the platform" or "Connect" interchangeably in output text (per Cyto convention — Cyto stories reference "Connect Cytology orders"). For Micro, equivalent references read "Connect Microbiology."

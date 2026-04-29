---
name: Stories must clear the dev-actionability bar — and the bar is shape-aware
description: The deliverable to dev teams is unambiguous, testable, well-scoped Jira stories — but actionability looks different across the four story shapes
type: feedback
originSessionId: 48bcc75e-a71b-45c0-b007-a168c583c917
---
The deliverable from this system is **Jira stories that a Connect LIMS dev team picks up Monday morning and codes against without coming back to the SME for clarification.** Vague outputs are a failure mode, not a draft to be improved later. The bar is **shape-aware** — actionability looks different depending on which of the four story shapes a story belongs to (see project memory for the four shapes).

**Why:** Client-stated requirement: "clear, unambiguous stories that can be acted upon by dev teams." Real Cyto Jira evidence shows stories come in four shapes (capability / workflow-stage-split / configuration-instance / cleanup) and a single rubric over-fits to capability stories. A configuration-instance story is "actionable" by being precise about values, not by MUST/SHALL language. A cleanup story is actionable by naming the exact artifact being modified. Anti-pattern stories like *"As a user, I want to record results so that I can communicate findings"* with AC like *"Support result entry. Validate input."* don't pass any shape's rubric — they require the dev to invent the actual specification.

**How to apply:**
- Every generated story must conform to a strict schema (see D9 — title, description, AC list, citations, dependencies, complexity, edge cases, plus `shape` field). The Epic that owns the story carries an optional `cyto_epic_analog` annotation per D13; stories inherit that link via `epic_id` rather than duplicating it.
- Validator (Haiku-class) is **type-aware**: classifies shape first, then applies the shape-specific sub-rubric (D7).
  - **Capability:** MUST/SHALL, parameters explicit, configurability boundaries called out.
  - **Workflow-stage-split:** stage explicit in title, sibling stories enumerated, stage-specific behavior testable.
  - **Configuration-instance:** concrete values present (typed), target config table named, no MUST/SHALL pretense.
  - **Cleanup:** target artifact named, before/after observable, regression risk acknowledged.
- Two revision attempts allowed, then escalate to SME with failed-checks visible.
- Per-SOP extraction replicates the Cyto shape mix (D10) — don't normalize to a single abstraction. Capability stories arise from cross-SOP synthesis (D11), not from in-SOP lifting.
- When showing extraction outputs, default to the *concrete* form of a story per shape, not the abstract category. Side-by-side vague-vs-actionable contrast clarifies the bar — and the contrast must be drawn within the same shape (an actionable capability story vs. a vague capability story; not capability vs. configuration).
- Don't propose "draft stories that SMEs will refine" — that pushes specification work onto humans. The agent must produce specification-level output.

---
name: Reference-doc style preferences
description: Single-source reference docs should be schemas-explicit (field tables + JSON/YAML examples), have a glossary upfront, use concrete I/O traces, and stay simple in language while keeping technical jargon when it earns its keep
type: feedback
originSessionId: cff33524-ac6a-4e39-b128-dde72748c770
---
When the user asks for "a single point of reference for anyone looking to understand the entire process," they mean a doc that:

1. Has a **glossary upfront** defining every technical term used (shape, theme, intent, τ/θ, batch wait, etc.) so the rest of the doc can use them freely.
2. Treats **schemas as first-class content** — full JSON/YAML examples *plus* per-field tables (type / required / notes). Don't summarize; show the structure.
3. Uses **concrete I/O traces** — pick one real-ish input (e.g. `SOP-MICRO-014_Gram-Stain_v3.docx`, query "Generate epics for specimen rejection in microbiology") and walk it through every stage with actual data shapes. Beats abstract pipeline descriptions.
4. Has **graph/DAG views** where relationships matter — Story dependency graph, Cyto→Micro lineage, etc. The user actively likes graph framing and asked for it explicitly.
5. Keeps language **simple but technically honest** — define jargon on first use, but don't dumb it down. Their words: "less jargons (but still keep technical jargons if they are helpful to communicate with technical folks)."

**Why:** the user's audience is mixed — SMEs, dev leads, architects. A doc that's too jargon-heavy loses the SMEs; one that's too dumbed-down loses credibility with the architects. The glossary + schemas + traces structure threads that needle.

**How to apply:**
- Don't draft summaries when the user asks for a reference. Bias toward more detail, more examples, more schemas.
- Always include a glossary section near the top of any new reference doc.
- For each schema, render: a JSON/YAML example + a field table with type, required, notes. Both, not either-or.
- For each pipeline stage with non-trivial state, include an I/O trace example with concrete values.
- When relationships are non-obvious (graphs, lineage, DAGs), draw them — the user explicitly values graph views.
- Length budget is generous when the doc is meant as a reference. The user's prior 2-page-cap was for a different ask (executive summary). Reference docs can be 6–8 pages with diagrams.

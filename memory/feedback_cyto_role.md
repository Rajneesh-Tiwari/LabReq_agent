---
name: Cyto is a teaching corpus, not a registry to match against
description: Stakeholder-confirmed framing for how Cytology data feeds the Microbiology generation pipeline
type: feedback
originSessionId: 48bcc75e-a71b-45c0-b007-a168c583c917
---
Cytology data (SOPs + Jira) is a **teaching corpus** — curated exemplars that train the LLM agents via few-shot prompting and dynamic exemplar retrieval. It is *not* a registry that Microbiology outputs are matched against, and there is no "REUSE / ADAPT / NEW" tagging on Micro outputs. Output is pure Micro artifacts produced natively by agents that have learned Cyto patterns.

**Why:** The user explicitly redirected here when I proposed a Cyto-as-anchor-registry approach with capability matching. Their framing — confirmed from stakeholder conversations — is that the goal is to *learn from Cyto and produce Micro outputs natively*, not to inherit Cyto artifacts. Capability-matching imposes too much SME burden on equivalence judgments and doesn't generalize to future disciplines.

**How to apply:**
- Don't propose architectures that require capability-level matching between disciplines.
- Don't include "REUSE / ADAPT / NEW" tags or similar inheritance markers on outputs.
- Frame Cyto's footprint as: curated exemplars used by agents at extraction time. The exemplar corpus grows organically (accepted Micro outputs become future exemplars too).
- This generalizes cleanly — when Histology is next, same agents, just keep enriching the exemplar corpus.
- The retrieval primitives (hybrid BM25+dense, multi-slot, theme prior) still apply, but their consumer is *exemplar retrieval for agents*, not direct query→answer for users.

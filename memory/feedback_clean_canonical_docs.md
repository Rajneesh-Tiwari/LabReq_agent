---
name: Clean canonical docs vs version-evolution docs
description: When a doc is for sharing with the team to understand the current system, present the current version as THE architecture — no v3.1-vs-v3.2 contrast, no "(v3.2)" version markers, no "v3.2 addition" callouts. Keep evolution-framed walkthroughs as separate parallel files for audiences that care about how the architecture got here.
type: feedback
originSessionId: cff33524-ac6a-4e39-b128-dde72748c770
---
When the user asks for a doc to share with their team for understanding the current architecture, default to the **clean canonical style**:

- Present the current version as if it's THE architecture, not an iteration. No "v3.1 vs v3.2 — what changed" contrast blocks, no "v3.2 modifications inside the main pipeline" callouts, no "(v3.2)" suffix on schema headings, no "v3.2 update" annotation boxes pointing to other pages, no "earlier this was X but now it's Y" framing.
- Strip any field-table annotations like "(v3.2 — replaces cyto_epic_analog)" — just describe the field as it is.
- Strip references to "the user's stated motive / preference" — depersonalize to "the design intent" since the doc is for an audience that doesn't know who "the user" is.
- Promote items that were treated as v(N) additions to first-class structure (e.g., the catalog artifacts went from "v3.2 addition" callouts to "Output C — Versioned catalog artifacts" alongside Output A and Output B).
- If pages or sections were added in a later version, reorder them to follow execution order or pedagogical order — don't leave them appended at the end as "v3.2 pages."

**Why:** the user explicitly rejected the evolution-framed walkthrough when asking for a team-shareable doc with: *"I dont want to muddle stuff with redudant stuff from earlier approaches."* They created the v3.2 spec separately and wanted a clean canonical doc that stands alone. They later asked for a v3.3 iteration starting from the v3.2-only docx, confirming that the clean canonical track is the one they iterate on going forward.

**How to apply:**
- For team-shareable docs: clean canonical only. If the doc previously had evolution framing, fork it: keep the original with evolution framing as a separate file (the "walkthrough" suffix is the existing convention), and produce a clean version (the no-suffix or `_v32`-style filename is the clean one).
- Two parallel tracks are fine. Don't try to satisfy both audiences in one doc — it ends up muddled either way.
- A useful check: search the doc for `v3.X`, `cyto_epic_analog` (or other renamed-in-v(N) fields), `same as v3`, "user's stated", and `Replaces v` strings before declaring the doc clean. These are the most common leaks.
- Drawio-specific: page titles that start with "v3.2 " should drop the prefix in canonical decks; "v3.2 update" annotation boxes on older pages should be removed (or merged into the page's main content); "v3.1 vs v3.2" comparison blocks inside detail pages should be replaced with a neutral principle callout.
- A clean canonical doc still needs an "Open questions / what's still TBD" section at the end so the team sees the deliberately-unresolved items in the same artifact rather than discovering them mid-implementation. This is the one place version-evolution context can leak in (e.g., "this default is a guess from the first run").

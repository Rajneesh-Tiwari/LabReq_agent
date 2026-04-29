---
name: Prefer .docx for client-facing deliverables
description: Prefer pandoc-built .docx over LaTeX/PDF when the artifact is going to a client or external audience — PDFs styled with LaTeX defaults are visibly AI/auto-generated and the user does not want that signal on delivery
type: feedback
originSessionId: cff33524-ac6a-4e39-b128-dde72748c770
---
When a reference / handoff / client-facing doc is the goal, build it as **markdown → pandoc → .docx with embedded PNGs** rather than LaTeX → PDF.

**Why:** the user explicitly said "if I give PDF they would know I generated via Claude." Pandoc-default Word styling (Calibri body, Cambria-ish headings) looks like ordinary human-authored Word output; LaTeX defaults (Computer Modern fonts, very tight typesetting) are recognizable as machine-generated. The user delivers to Labcorp stakeholders and needs the artifact to read as their own work.

**How to apply:**
- For client-facing docs: lead with .docx as the deliverable; keep the .tex / .pdf as an internal-reference companion if useful but do not present it as the handoff.
- Author content in markdown so it converts cleanly. Render diagrams as standalone PNGs (e.g. via `\documentclass{standalone}` + Ghostscript) and embed via `![caption](path/to.png){width=100%}`.
- `pandoc input.md -o output.docx` with default styling is the right baseline — no `--reference-doc` needed; default Calibri/Cambria reads as natural Word.
- The visual TikZ PDF is still useful as the user's own working reference (vector quality, easy to update). Keep both in the repo, but route the docx to anyone external.

---
name: Project terminology rules
description: Specific terms the user prefers + corrections made during sessions. Apply project-wide (specs, canonical doc, deck, slides, code).
type: feedback
---

Two terminology rules the user explicitly enforced. Apply both project-wide.

**Rule 1: discipline, NOT lab.**

The user explicitly corrected: *"why do we say new lab or old lab, its new discipline or old discipline."* This applies wherever we mean a discipline classification (Cytology, Microbiology, Histology, Hematology, Chemistry, etc.):

- Use: "prior discipline," "new discipline," "target discipline," "any clinical-lab discipline," "the discipline brings…", "per-discipline."
- Don't use: "prior lab," "new lab," "similar lab," "any lab type," "per-lab."

OK to keep "lab" where it refers to the physical lab (the workplace, not the discipline classification): "clinical lab," "lab-process workflow," "lab procedure documents" (when introducing SOPs). The phrase "clinical-lab" as an adjective is acceptable.

**Why:** the user delivers to Labcorp stakeholders. "Discipline" is the precise term Labcorp uses internally for organizational divisions (Cytology vs. Microbiology vs. Histology). "Lab" is generic and conflates concepts.

**Rule 2: SOP (or SOPs), NOT document.**

The user explicitly said: *"we only have 1 type of document which is the SOPs."* The system handles **only** SOPs as input — there is no other document type. So:

- Use: "SOP," "SOPs," "SOP chunks," "sample SOPs," "per-SOP processing," "across SOPs."
- Don't use: "document," "documents," "document chunks," "procedure documents" (except introducing SOPs as "SOPs (Standard Operating Procedures)" on first mention).
- Schema field naming: prefer `source_sops` over `source_documents`.

**Why:** "Documents" is overly generic and obscures the precision the architecture depends on. SOPs have specific structural properties (sections, stages, citation format) the system relies on. Using "documents" suggests the system might handle anything, which it doesn't.

**Other terminology to spell out at first use:**

- **AC** = Acceptance Criterion / Acceptance Criteria. The user pushed back on undefined "AC" in slide examples. Either spell out as "Criterion 1:", "Criterion 2:" or define inline at first use.
- **DAG** = Directed Acyclic Graph. Used for the dependency resolver output. Spell out at first use.
- **ANALOGY map** = the cross-discipline link table artifact. Capitalized for emphasis; defined in the canonical glossary.
- **G0 / E0** = first-class unclassified buckets on theme/epic catalogs respectively. Defined in glossary; safe to use after.
- **`τ_match`, `ε_novelty`** = the two bias knobs of conditioned discovery. Defined in glossary.

**How to apply:**

- Audit pass before any client-facing artifact ships: search for "lab" (flag occurrences), "document(s)" (flag), unexplained acronyms (flag).
- Apply to: slide content, schema field names, architecture doc text, code variable names where reasonable, commit messages.
- Exception for legacy: `microbio_lims_architecture_*.{md,docx,drawio}` filenames retain the `microbio_` prefix because of file-naming convention; the *content* is now discipline-agnostic.

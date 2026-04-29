---
name: Theme taxonomy assumption — addressed by v3.2 Conditioned Discovery
description: v3.1 assumed themes G1–G8 known upfront. v3.2 addresses this with a pre-flight Theme Discovery agent that warm-starts a new discipline's catalog from the prior, surfacing only the residual as novel. Versioned config-as-data replaced the closed enum.
type: project
originSessionId: cff33524-ac6a-4e39-b128-dde72748c770
---
The v3.1 architecture took the theme set (G1 Pre-Analytic, G2 Analytic, G3 Post-Analytic, G4 Reporting, G5 QC, G6 Compliance, G7 Instrumentation, G8 Platform) as a precondition. Themes aren't decoration — they're the coordinate system the retrieval substrate uses for everything: the theme tagger needs the label set; the 8 centroid embeddings are precomputed; intent-decode outputs into the closed enum; the ADJACENT retrieval slot is "centroid neighbors"; the Epic schema constrains `themes` to G1–G8.

**v3.2 resolves this** with **Conditioned Discovery** at both theme and epic levels (see `V3_2_SPEC.md` and `microbio_lims_architecture_v32.md`):

- A new pre-flight **Theme Discovery agent** runs once per discipline before the main pipeline. It classifies the new discipline's SOP chunks against the prior catalog at threshold `τ_match` (default 0.65), clusters only the residual at minimum size `ε_novelty` (default 3), and routes novel candidates to SME ratification. Inherited themes bypass review.
- Catalogs are now versioned config-as-data with distinct names: theme catalogs as `<discipline>_v<N>` (e.g. `cyto_v1`, `histo_v1`); epic catalogs as `<discipline>_epic_v<N>` (e.g. `cyto_epic_v1`, `micro_epic_v1`). They version independently. Stories carry `theme_catalog_version` for theme resolution.
- **G0 (theme) and E0 (epic) unclassified buckets** are first-class with a 5% alarm threshold over a rolling window. Alarm trips re-run the appropriate Discovery agent — replaces the v3.1 implicit fallback.
- Cross-discipline links are explicit in an **ANALOGY map** artifact (typed: identical / partial / discarded_in_target / novel_in_target).
- Worked Histology example: 7/8 of Cyto's themes carry over, 4 novel (H1–H4) emerge, G7 discarded with partial mapping to H1.

For the Micro POC, the theme catalog stays `cyto_v1` (Micro reuses Cyto's themes wholesale) and only the epic catalog forks into `micro_epic_v1`.

**Why:** the user surfaced this in 2026-04 as a sharp architectural question. v3.2 design preference, captured in the user's words: "don't just end up with entirely new ones." Hence the warm-start (high `τ_match`, non-trivial `ε_novelty`) rather than cold-start clustering.

**How to apply:**
- When asked about extending to a new discipline (e.g. Histology, Hematology), point at the v3.2 Theme Discovery flow — it's no longer a "the architecture doesn't handle this" problem, it's "run Theme Discovery against `cyto_v1` as the prior."
- The `τ_match` and `ε_novelty` defaults are guesses pending first-run telemetry — see the "Open questions" section in `microbio_lims_architecture_v32.md` for the calibration plan.
- Story `themes[]` carries `theme_catalog_version` so taxonomy version bumps can be tracked; a Pass 4 re-tag updates the corpus when the catalog changes.

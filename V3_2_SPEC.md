# v3.2 Spec — Conditioned Discovery

**Status:** Draft  
**Supersedes:** parts of v3.1 that assume themes G1–G8 are known upfront and that epics are produced ex nihilo from SOPs alone.  
**Carries forward unchanged:** the 5-agent pipeline, the four story shapes, cross-SOP synthesis, the type-aware Validator, the per-culture YAML profile, and Cyto's role as a teaching corpus.

---

## 1. Motivation

v3.1 makes two implicit cold-start assumptions:

1. **Themes G1–G8 are known.** The theme tagger, the eight centroid embeddings, the intent-decode classifier (closed enum by construction), and the ADJACENT retrieval slot all assume the G1–G8 vocabulary is fixed. The Epic schema's `themes[]` field is *soft* per D3, but its values are drawn from this same closed vocabulary — so a new discipline still has nowhere to put a tag that doesn't fit. (See `project_theme_taxonomy_assumption.md`.)
2. **Epics are generated from-scratch per SOP.** The Epic Extractor reads SOPs and proposes epics directly, with a `cyto_epic_analog` annotation slot (D13) that is populated *after* the fact when retrieval signal happens to align — i.e., the analog is a post-hoc decoration, not a generation constraint.

Both assumptions hold for a single-discipline POC where Cyto's taxonomy is the ground truth. They break the moment we extend:

- **New discipline (Histology, Hematology, Chemistry):** there is no prior taxonomy to retrieve into and no labels for the classifier. The `unclassified` bucket would balloon.
- **Within Micro itself:** if the Epic Extractor proposes epics cold from each SOP, we end up with a Micro epic catalog that *looks Micro-shaped* but doesn't visibly inherit Cyto's organizing structure — even when the underlying capability is identical (Specimen Receiving, Billing, Reporting, etc.). The dev team then has to do the mental mapping themselves.

The fix is not to discard the existing structure ("themes-from-data" pure clustering — option C in `OPEN_QUESTIONS.md`) and not to freeze it ("config swap" — what v3.1 implicitly does). It is to treat existing themes and existing epics as a **prior** that biases new generation. Where evidence supports reuse, reuse. Where evidence demands novelty, novelty emerges — but it must clear an evidentiary bar, and an SME signs off on the new structure being added to the catalog.

This is **conditioned discovery**.

---

## 2. Core principle

> **Don't generate from scratch when you have a strong prior. Don't freeze the prior when the evidence has moved on. Condition new generation on what already exists, surface only the residual as novel, and let an SME ratify the additions.**

Applied at two levels:

| Level | Prior | Discovery target | Output |
|---|---|---|---|
| **Theme** | G1–G8 from Cyto | The taxonomy for a new discipline | Versioned theme config (mostly inherited, plus 0–N novel themes) |
| **Epic** | Cyto's existing epic catalog | The epic set for a new SOP corpus | Epic candidates (mostly aligned to existing epics, plus 0–N novel epics) |

Both use the same algorithmic pattern (§4). The schemas and SME gates differ slightly because themes are taxonomic (small set, slow-changing) and epics are content (larger set, faster-changing).

---

## 3. Glossary (delta vs v3.1)

- **Conditioned discovery.** A four-pass procedure: (1) **Classify** the input against an existing prior catalog using a confidence threshold; (2) **Cluster** only the residual (low-confidence) inputs to surface novel candidates; (3) **SME ratifies** the novel candidates (inherited entries bypass review); (4) **Re-tag** the existing corpus when the catalog version bumps. The first two passes are the algorithmic core; the third is the gate; the fourth is a side effect.
- **Prior catalog.** The set of themes (or epics) treated as the existing structure to reuse. For Micro POC, this is the Cyto theme set + Cyto epic set. For a future discipline, it is whichever taxonomy the SME decides to inherit from (could be Cyto's, or could be the most recent ratified Micro one).
- **Residual.** Inputs (SOP chunks for theme discovery, SOP-level epic proposals for epic discovery) that fall below the prior-classification confidence threshold. The residual is the candidate pool for novel discovery.
- **G0 / E0.** The "Unclassified" bucket promoted to first-class. Replaces the implicit fallback in v3.1. Has a configurable alarm threshold (default 5% of input volume) that triggers SME review and possibly a re-run of conditioned discovery.
- **Catalog naming.** Theme catalogs are named `<discipline>_v<N>` (e.g., `cyto_v1`, `histo_v1`). Epic catalogs are named `<discipline>_epic_v<N>` (e.g., `cyto_epic_v1`, `micro_epic_v1`) — they are *separate* artifacts from theme catalogs and version independently. A discipline may share its theme catalog with a parent (Micro reuses `cyto_v1` for themes; see §9) while having its own epic catalog.
- **Taxonomy version.** Stories and Epics carry an explicit `theme_catalog_version` field referencing which theme catalog their `themes[]` resolve in. Epics belong to an epic catalog by file membership (no separate version field needed). A re-tagging script handles version bumps.
- **ANALOGY map.** An explicit table linking themes/epics across disciplines (e.g., `cyto.G7 ↔ histo.H1, equivalence: partial`). Replaces v3.1's implicit assumption of a shared theme space.

Terms unchanged from v3.1 (shape, theme, intent, τ/θ, batch wait, etc.) are defined in `microbio_lims_architecture_walkthrough.docx`.

---

## 4. The conditioning algorithm

The same pattern runs at both levels. Stated in pseudocode:

```
INPUT:
  prior_catalog      # existing themes or epics, with descriptions + (themes only) centroids
  candidate_inputs   # SOP chunks (theme-level) or SOP-level epic proposals (epic-level)
  τ_match            # match-confidence threshold (default 0.65)
  ε_novelty          # novelty-evidence threshold (min cluster size in the residual; default 3)

PASS 1 — CLASSIFY against prior:
  for each input:
    score = best_match(input, prior_catalog)         # cosine on centroids OR LLM-as-classifier
    if score ≥ τ_match:
      assign input → existing entry; record (entry_id, score)
    else:
      mark input as residual

PASS 2 — CLUSTER the residual:
  cluster the residual using HDBSCAN (or LLM-as-clusterer for small N)
  for each cluster of size ≥ ε_novelty:
    summarize cluster → candidate_novel_entry {description, members, evidence}
  small clusters (size < ε_novelty) → G0/E0 unclassified bucket

PASS 3 — SME RATIFICATION (gate):
  present to SME:
    - candidate novel entries (with evidence and proposed name)
    - G0/E0 bucket size and sample
    - the assignments from Pass 1 (skim, not deep-review)
  SME confirms / renames / rejects each novel candidate
  ratified novel entries are merged into the catalog → emit catalog_v(N+1)

PASS 4 — RE-TAG (only when catalog version bumps):
  re-run the classifier over previously-tagged corpus chunks against catalog_v(N+1)
  update Story.themes[] / Epic.themes[] / Epic.epic_analog accordingly
  (any chunks previously assigned to a now-discarded theme get re-classified
   against the post-discard taxonomy)
```

Two knobs control the bias:

- **τ_match high** → eager to inherit (lots of inputs map to existing entries; small residual). Risk: forced fits. Default 0.65, tunable per discipline.
- **ε_novelty high** → conservative about admitting novelty (cluster needs more witnesses to count). Default 3, tunable.

For the Micro POC with Cyto as prior, default both knobs to *bias toward reuse*. The user's stated motive — "don't just end up with entirely new ones" — corresponds to a high τ_match and a non-trivial ε_novelty.

---

## 5. New components and schema changes

### 5.1 Theme Discovery Agent (new)

A pre-flight agent that runs **once per discipline**, not per SOP. Inputs: a sample of N representative SOPs (15–30) from the new discipline + the prior theme catalog (e.g., Cyto's G1–G8). Output: a versioned theme config and an SME report.

**Pipeline placement:** *pre-flight* — Theme Discovery is not part of the live per-SOP main pipeline. It runs once before the main pipeline boots for the new discipline (and again only when the G0 alarm trips). Its published theme config feeds the Theme Tagger, the centroid embedder, the intent-decode classifier, the ADJACENT slot, and the Epic schema's `themes[]` vocabulary at runtime.

**When does it run?**
- Once when bootstrapping a new discipline.
- On-demand re-run when the G0 alarm trips (>5% chunk volume tagged unclassified over a rolling window).
- Manually, on SME request.

### 5.2 Epic Discovery (modification to existing Epic Extractor)

The v3.1 Epic Extractor read SOPs and produced epics directly. In v3.2 it runs in **conditioned mode**:

1. For each SOP, propose draft epics as before.
2. For each draft epic, run Pass 1 against the prior epic catalog (Cyto's, plus any previously-ratified Micro epics). If it matches an existing epic with score ≥ τ_match, link to it (`epic_analog`) and re-use the existing epic ID. The SOP's stories then attach under the existing epic.
3. Drafts that don't match feed Pass 2 (cluster the residual across SOPs).
4. Pass 3 SME ratification gates novel epics into the catalog.

This means the Micro epic catalog grows **conservatively**: most SOPs attach stories under inherited Cyto epics with `epic_analog` populated by *construction*, not as a post-hoc annotation. Genuinely novel Micro epics (e.g., AST-Antibiotic-Susceptibility-Testing if it has no Cyto analog) emerge with explicit evidence.

### 5.3 Versioned taxonomy config (new schema)

```yaml
# theme_config schema
catalog_id: histo_v1
parent_catalog: cyto_v1            # the prior we inherited from
discipline: histology
created: 2026-XX-XX
sme_reviewer: <name>

inherited_themes:
  - id: G1
    name: Pre-Analytic
    source: cyto_v1
    centroid_embedding_ref: s3://.../centroids/G1.npy
    match_count: 142               # number of histo chunks that classified into G1
  - id: G2
    name: Analytic
    source: cyto_v1
    ...

novel_themes:
  - id: H1
    name: Tissue Processing
    source: histo_v1
    cluster_evidence:
      n_chunks: 38
      sample_excerpts: [<chunk_id_1>, <chunk_id_2>, ...]
      proposed_definition: "Steps that transform fixed tissue into sectioned, stained slides ready for analytic review."
    sme_confirmed: true
    sme_notes: "Confirmed. Distinct from G2 Analytic — review happens later."

discarded_themes:
  - id: G7  # Instrumentation
    reason: "Folded into H1 (Tissue Processing) for histology — instrument concerns are not a top-level cut here. Recorded in the ANALOGY map as G7 → H1 (partial)."
    decision_by: <sme_name>
    chunks_re_tagged: 12             # Pass 4 re-classified the 12 chunks Pass 1 had assigned to G7

unclassified_bucket:
  count: 22
  pct_of_total: 3.2                # below 5% alarm
  sample_excerpts: [...]
  next_review_due: 2026-XX-XX
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `catalog_id` | string | yes | Versioned (`<discipline>_v<N>`). Stories tag against this. |
| `parent_catalog` | string\|null | yes | The prior the discovery was conditioned on. `null` only for the very first ever (`cyto_v1`). |
| `inherited_themes[]` | array | yes | Themes that survived from `parent_catalog` after classification. |
| `novel_themes[]` | array | yes | New themes ratified by SME. May be empty. |
| `discarded_themes[]` | array | optional | Themes from the parent that don't apply here, with reason. |
| `unclassified_bucket` | object | yes | G0 stats. Always present, even if empty. |

### 5.4 Epic catalog (new artifact)

```yaml
# epic_catalog schema
catalog_id: micro_epic_v1
parent_catalog: cyto_epic_v1            # the prior we inherited from
discipline: microbiology
created: 2026-XX-XX

inherited_epics:
  - id: EPIC-MICRO-001
    title: Specimen Receiving
    epic_analog:
      catalog_id: cyto_epic_v1
      epic_id: EPIC-CYTO-014
      equivalence: identical
    inheritance_basis:
      match_score: 0.78
      shared_themes: [G1]
      auto_inherited: true              # match_score ≥ τ_match; bypassed SME review per §5.2

novel_epics:
  - id: EPIC-MICRO-007
    title: Antibiotic Susceptibility Testing (AST)
    epic_analog: null                   # no Cyto correspondent
    novelty_basis:
      cluster_evidence:
        n_draft_epics: 4                # how many SOPs contributed drafts to the cluster
        sample_drafts: [<draft_id_1>, ...]
      sme_confirmed: true               # required for novel — SME-ratified at Pass 3

unclassified_drafts:
  count: 3
  pct_of_total: 4.1
  next_review_due: 2026-XX-XX
```

### 5.5 ANALOGY map (new artifact, replaces implicit assumption)

```yaml
# analogy_map schema
source_catalog: cyto_v1                 # theme catalogs (epic-level links live below in epic_links)
target_catalog: histo_v1

theme_links:
  - source: G1,   target: G1, equivalence: identical
  - source: G7,   target: H1, equivalence: partial,
    note: "Cyto Instrumentation has no top-level peer in histo_v1 (discarded as a theme); concepts partially absorbed by H1 Tissue Processing for slide-prep instruments."
  - source: null, target: H2, equivalence: novel_in_target
  - source: null, target: H3, equivalence: novel_in_target
  - source: null, target: H4, equivalence: novel_in_target

# Each non-identical theme link carries a one-line note. Each cyto theme appears at most once
# as a `source`; "discarded with partial mapping" is a single entry, not two.

epic_links:
  - source: EPIC-CYTO-014, target: EPIC-HISTO-002, equivalence: identical
  - source: EPIC-CYTO-022, target: null,           equivalence: discarded_in_target
```

This drives the ANALOGY retrieval slot for cross-discipline queries: when the user asks Histo questions and the LLM wants Cyto context, the ANALOGY map filters Cyto chunks down to themes that actually have a target-side correspondent.

### 5.6 G0 / E0 — Unclassified as first-class

In v3.1, "unclassified" is implicit fallback behavior. In v3.2 it is a reviewable bucket with a contract:

- Every theme catalog has an `unclassified_bucket` object (count, sample, due date).
- Every epic catalog has an `unclassified_drafts` object.
- An alarm fires when the bucket exceeds 5% of total volume (configurable). When the alarm fires, the appropriate Discovery Agent re-runs.
- The bucket is **not** a permanent home — items either get re-classified into an existing entry (manual SME action) or feed the next discovery cluster.

### 5.7 Schema deltas on existing artifacts

**Epic schema (v3.1 → v3.2):**

```diff
{
  id, title, description,
  discipline,
- themes[],                       // soft theme tags (D3)
+ themes[],                       // soft theme tags (D3); values drawn from theme_catalog_version below
+ theme_catalog_version: string,  // e.g. "cyto_v1" — which theme catalog these tags resolve in
                                  // (the epic catalog version is implicit by file membership)
- cyto_epic_analog?               // optional annotation, see D13
+ epic_analog?                    // optional cross-catalog link {catalog_id, epic_id, equivalence}
+ inheritance_basis?              // populated by Epic Discovery: {match_score, shared_themes, auto_inherited}
}
```

**Story schema:** add `theme_catalog_version` mirroring the Epic field. Stories don't change shape otherwise — `themes[]` is just now resolved against a versioned theme catalog rather than a closed enum.

---

## 6. Pipeline diagram (v3.2 delta)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ONE-TIME PER DISCIPLINE (or when G0 alarm trips)                       │
│                                                                         │
│   Sample SOPs ──┐                                                       │
│                 ├──► Theme Discovery Agent ──► SME ratify ──► theme     │
│   prior catalog ┘                                              config   │
│   (e.g. cyto_v1)                                              v(N+1)    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼  (published config feeds the live pipeline)
┌─────────────────────────────────────────────────────────────────────────┐
│  PER-SOP-CORPUS RUN (the v3.1 main pipeline, with Epic Extractor        │
│   running in conditioned mode)                                          │
│                                                                         │
│   SOPs ──► Epic Extractor (conditioned mode) ──► draft epics            │
│              │                                                          │
│              ├── score ≥ τ_match ──► link epic_analog, reuse epic id ─┐ │
│              │                                                        │ │
│              └── score < τ_match ──► cluster residual ──► SME ratify ─┤ │
│                                                                       ▼ │
│                                       epic catalog v(N+1) ──► Story Extr│
│                                                              ──► Validator
│                                                              ──► … (unchg)
└─────────────────────────────────────────────────────────────────────────┘
```

Two SME gates are added to v3.2: one at theme ratification (one-time per discipline), one at epic ratification (per SOP corpus run). Both surface the *novel* candidates with evidence — the SME is not asked to re-review the inherited ones.

---

## 7. I/O trace — bootstrapping Histology from Cyto

A worked example to make the algorithm concrete.

**Inputs:**
- `prior_catalog`: `cyto_v1` (themes G1–G8, ~40 epics)
- `candidate_inputs`: 20 sample Histology SOPs, ~600 chunks after ingest
- `τ_match`: 0.65, `ε_novelty`: 3

**Pass 1 — Classify against G1–G8:**

| Theme | Histo chunks classified | Notes |
|---|---|---|
| G1 Pre-Analytic | 142 | Specimen receiving, fixation prep — direct fit |
| G2 Analytic | 98 | Slide review by pathologist — direct fit |
| G3 Post-Analytic | 67 | Reporting workflow — direct fit |
| G4 Reporting | 54 | Report templates, sign-out — direct fit |
| G5 QC | 41 | Slide QC, batch QC — direct fit |
| G6 Compliance | 28 | CLIA, CAP — direct fit |
| G7 Instrumentation | 12 | Sparse — instruments are different here |
| G8 Platform | 18 | Direct fit |
| **Residual (score < 0.65)** | **140** | Feeds Pass 2 |

**Pass 2 — Cluster the residual:**

HDBSCAN on the 140 residual chunks → 4 clusters above ε_novelty=3, plus 22 noise chunks → G0.

| Cluster | Size | Sample excerpt | Proposed novel theme |
|---|---|---|---|
| 1 | 38 | "Tissue is processed through graded alcohols, embedded in paraffin, sectioned at 4–5μm…" | **H1: Tissue Processing** |
| 2 | 32 | "Sections are stained with H&E using the auto-stainer protocol…" | **H2: Staining** |
| 3 | 25 | "Block storage and retention per CAP guidelines: 10 years for blocks, 2 years for slides…" | **H3: Block & Slide Archive** |
| 4 | 23 | "Frozen section turnaround target is 20 minutes from receipt to verbal report…" | **H4: Intraoperative / Frozen Section** |

**Pass 3 — SME ratification:**

SME reviews 4 novel candidates with evidence:
- H1 confirmed (rename to "Tissue Processing", definition refined).
- H2 confirmed.
- H3 confirmed.
- H4 confirmed but flagged: "this might split into Frozen-Section and Routine-Archive depending on observed volume in production. Revisit at the 6-month G0 review."

Discarded themes: SME notes G7 Instrumentation in Cyto is a top-level cut because Cyto has many instrument-specific stories. In Histo, instrument concerns fold into H1 (Tissue Processing) — drop G7 from `histo_v1` and link it in the ANALOGY map as `partial → H1`.

**Pass 4 — re-tag the 12 G7 chunks:** because G7 was discarded, the 12 chunks Pass 1 had assigned to G7 no longer have a target. Pass 4 re-runs the classifier over those 12 chunks against the post-discard taxonomy (G1–G6, G8, H1–H4). They land predominantly in H1 (consistent with the ANALOGY map's `G7 → H1, partial` link); any that fall below τ_match against the new taxonomy go to G0. This is the general invariant: discarding a theme triggers re-classification of its chunks; nothing is left dangling.

**Output: `histo_v1` theme config**

```yaml
catalog_id: histo_v1
parent_catalog: cyto_v1
inherited_themes: [G1, G2, G3, G4, G5, G6, G8]    # 7 of the 8 prior themes carried over
novel_themes:     [H1, H2, H3, H4]                # 4 new, SME-ratified
discarded_themes: [G7]                            # mapped via ANALOGY, chunks re-tagged in Pass 4
unclassified_bucket:
  count: 22
  pct_of_total: 3.7                               # under 5% alarm
```

**Net result:** `histo_v1` has **11 active themes** (7 inherited + 4 novel; G7 discarded is recorded in the ANALOGY map but not in the active catalog). 7 of those 11 active themes (≈ 64%) come straight from Cyto, and 7 of the 8 prior themes (87.5%) survived the bootstrap. The dev team reading `histo_v1` immediately sees what carries over from Cyto and what's genuinely new about Histology — without having to do that mapping themselves.

---

## 8. Decisions (proposed for the log)

These would be added to `DECISIONS.md` after spec review.

### D16 — Conditioned discovery (warm-start) is the v3.2 mechanism for cross-discipline extension

**Decision:** When extending the system to a new discipline (or re-bootstrapping after the G0 alarm trips), the Theme Discovery Agent and the conditioned-mode Epic Extractor classify-against-prior first and cluster only the residual. The catalog grows by inheritance + ratified novelty, never by full regeneration.

**Rationale:** Cold-start clustering produces taxonomies that float free of existing structure and force the dev team to do the cross-discipline mapping themselves. Pure config-swap can't accommodate genuinely novel themes (frozen-section, AST). Conditioned discovery preserves reuse signal where it exists and surfaces novelty with evidence where it doesn't.

**Alternatives considered:**
- (B) Layered themes — keep G1–G3 universal (workflow stages), allow G4–G8 to vary per discipline. Rejected as a hard layering: cleaner architecturally but assumes workflow-stage themes are universal, which is itself a Cyto-bias claim.
- (C) Themes-from-data clustering. Rejected as failing the user's stated motive ("don't just end up with entirely new ones").

### D17 — Two-pass classify-then-cluster, with τ_match and ε_novelty as the bias knobs

**Decision:** The conditioning algorithm is two-pass: classify each input against the prior at threshold τ_match, then cluster only the residuals at minimum cluster size ε_novelty. Defaults: τ_match=0.65, ε_novelty=3. Knobs are tunable per discipline based on telemetry.

**Rationale:** Two-pass is interpretable (every input has a traceable disposition), debuggable (residuals are inspectable), and gives the SME exactly two knobs that map to the real architectural tradeoff (eagerness-to-reuse vs. evidence-bar-for-novelty).

**Alternatives considered:** Single-pass joint clustering with priors as soft labels (semi-supervised clustering). More elegant in theory but harder to debug and harder to expose to SME review.

### D18 — Theme and epic catalogs are versioned config-as-data, not closed enums

**Decision:** Theme catalogs (`<discipline>_v<N>`, e.g. `cyto_v1`) and epic catalogs (`<discipline>_epic_v<N>`, e.g. `cyto_epic_v1`) are separate versioned YAML artifacts. Stories and Epics carry an explicit `theme_catalog_version` field for theme resolution; epic catalog membership is implicit by file. A re-tagging script handles version bumps.

**Rationale:** v3.1 baked G1–G8 as a closed enum into the Epic schema, the theme tagger, and several other places. Treating the catalog as data instead of code means a new discipline doesn't require a code change to the agents; only a new catalog row. It also lets two disciplines coexist with different (linked-via-ANALOGY) taxonomies.

### D19 — G0 (theme) and E0 (epic) unclassified buckets are first-class with a 5% alarm threshold

**Decision:** Replace the implicit "unclassified" fallback with explicit first-class buckets that always exist on every catalog and always have a count + sample + alarm threshold. When the bucket exceeds 5% of input volume over a rolling window, the appropriate Discovery Agent re-runs.

**Rationale:** In v3.1, the unclassified bucket does silent work as a safety valve — taxonomy mismatch is invisible until someone goes looking. Making it first-class with an alarm makes "the taxonomy has drifted" a visible signal instead of an inference.

---

## 9. Migration from v3.1

For the Micro POC currently in flight, v3.2 is *additive* — nothing v3.1 produces becomes invalid. Migration steps:

1. **Snapshot Cyto's themes G1–G8 as `cyto_v1`** (the parent *theme* catalog every other theme catalog will derive from). Compute and store the eight centroid embeddings as `cyto_v1` artifacts.
2. **Snapshot Cyto's existing epic backlog as `cyto_epic_v1`** (the parent *epic* catalog). This becomes the prior for the conditioned Epic Extractor. Note the deliberate naming split: `cyto_v1` (themes) vs `cyto_epic_v1` (epics) — they are separate artifacts that version independently.
3. **Run conditioned Epic Extractor over the 3 in-scope Micro SOPs** (blood culture, urine culture, target pathogens). Output: a `micro_epic_v1` epic catalog with most epics linked to `cyto_epic_v1` analogs and possibly 1–2 novel Micro-only epics (likely AST).
4. **Stories generated from those epics** carry `theme_catalog_version: cyto_v1` (since Micro reuses Cyto's theme catalog wholesale for the POC), and attach to epics in `micro_epic_v1` via `epic_id`. Micro does not get its own theme catalog yet — it changes the *epic* catalog only.
5. **Defer Theme Discovery Agent to v3.2-extension** (Histology bootstrap or similar). For the Micro POC, the theme catalog stays `cyto_v1` because the assumption of theme-reuse holds within the same lab-process family.
6. **Add ANALOGY map artifacts as deliverables** alongside epics/stories — even for Micro, the `cyto_epic_v1 ↔ micro_epic_v1` ANALOGY map is now explicit instead of implicit. (No theme-level ANALOGY map is needed for Micro since the source and target theme catalogs are the same.)

This means the v3.2 Micro POC delivery looks like:
- Same Stories + per-culture YAML profiles as v3.1, now carrying `theme_catalog_version: cyto_v1`.
- *Plus* a `micro_epic_v1` epic catalog with explicit `cyto_epic_v1` lineage on every inherited epic.
- *Plus* an explicit `cyto_epic_v1 ↔ micro_epic_v1` ANALOGY map (epic_links only — theme_links empty since theme catalog is unchanged).

Net additional work for the POC: small. Net additional value: the dev team and the architecture team can read the output and immediately see what's inherited from Cyto vs. what's novel about Micro.

---

## 10. Open questions (v3.2-specific)

These extend `OPEN_QUESTIONS.md`:

- **τ_match and ε_novelty defaults.** Defaults of 0.65 / 3 are guesses. Need telemetry on the first real run (Micro epic discovery against Cyto's catalog) to calibrate. Too high τ_match → residual too small → novelty under-detected. Too low → residual too noisy → spurious novel clusters. Same logic for ε_novelty.
- **Match scoring backend.** Pass 1 can be (a) cosine similarity on centroid embeddings, (b) LLM-as-classifier with prompt + prior catalog descriptions, or (c) hybrid (cosine pre-filter, LLM tiebreaker). (a) is fast/cheap; (b) is most semantic but expensive; (c) is the practical default. Validate (c) on the Micro epic-discovery run.
- **SME ratification UX.** The novel-candidate review is the most SME-burden-heavy part of v3.2. Open: is this a Jira ticket per candidate, a single review document with all candidates, or a dedicated lightweight UI? Lean toward "review document + Jira ticket per ratified addition" for the POC; revisit if SME finds it heavy.
- **Re-tagging on catalog version bump.** Implementation is simple in principle (re-run the classifier), but for a corpus that has already produced Stories in Jira, do we (a) regenerate the Stories with the new `theme_catalog_version`, (b) only update the `themes[]` field on existing Stories (and bump `theme_catalog_version` in place), or (c) leave old Stories alone and only tag new ones? Lean (b) for the POC — preserves story identity, updates the resolution.
- **Cross-version querying.** When two disciplines have different live theme catalogs (e.g., Micro on `cyto_v1` and Histo on `histo_v1`) and a query crosses both, does the retriever fan out across both catalogs and reconcile via the ANALOGY map, or does it pick one as primary? Probably primary-with-ANALOGY-fanout, but specify before v3.2-extension lands.
- **What happens to v3.1 outputs already produced?** For the POC corpus already extracted under v3.1, do we re-run them through conditioned Epic Extractor to gain `epic_analog` populated by construction? Or grandfather them with `cyto_epic_analog` as best-effort post-hoc annotation? Lean re-run if cheap (the Epic Extractor is the cheap-ish part of the pipeline).

---

## 11. What v3.2 explicitly does *not* change

To keep the diff surface honest:

- The 5-agent main pipeline (Epic Extractor → Story Extractor → Validator → Cross-SOP Synthesis → Validator → Dependency Resolver) is unchanged in *shape*. Epic Extractor gains conditioned mode; the other four agents are untouched. Theme Discovery is a *new* sixth agent, but it is **pre-flight** (one-time-per-discipline) — it does not run on the per-SOP critical path.
- The four story shapes (capability, workflow-stage-split, configuration-instance, cleanup) and the type-aware Validator rubrics.
- Cross-SOP synthesis with the ≥2 distinct SOPs threshold.
- Cyto's role as a teaching corpus (D5) and the three transfer mechanisms (`epic_analog`, `exemplar_of`, `retrieval_analogy`).
- The hybrid retrieval substrate (BM25 + dense + RRF + rerank), the multi-slot retrieval (PRIMARY / ANALOGY / ADJACENT / EXEMPLAR / REG), and the τ=0.7 / θ=0.5 query thresholds (these are *query-time* thresholds, distinct from the new τ_match / ε_novelty *discovery-time* thresholds).
- The per-culture YAML configuration profile (D12).
- Tasks remaining out-of-scope (D14).

The v3.2 changes are concentrated at the **boundary**: how the pipeline starts up (the new pre-flight Theme Discovery agent), how Epic Extractor decides what's reused vs. novel (conditioned mode), and how the catalogs are versioned (config-as-data, ANALOGY map). The interior of the main pipeline is the same architecture v3.1 ratified.

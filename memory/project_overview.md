---
name: Labcorp Connect LIMS — Microbiology GenAI POC
description: Agent-based extraction of dev-actionable Epics + multi-shape Stories + per-culture config profiles from Microbiology SOPs, learning from Cytology exemplars
type: project
originSessionId: 48bcc75e-a71b-45c0-b007-a168c583c917
---
POC for Labcorp: a chat-based system that ingests Microbiology SOPs (one per culture type — blood culture, urine culture, target-pathogen area for the POC) and produces **dev-actionable Jira artifacts** for the new Microbiology build on Labcorp's **Connect** LIMS platform. The Cyto LIMS already runs on Connect; Micro is being built on the same platform.

**Why:** Labcorp wants to standardize and accelerate LIMS development for new disciplines by leveraging patterns proven out in their existing Cytology Connect build — but without manually translating Cyto artifacts.

**Current architecture (v3.2 — Conditioned Discovery on top of the v3.1 multi-shape pipeline):**

- Cyto data is a **teaching corpus**, not a registry to match against. Curated exemplars (SOP excerpt → SME-validated story) train agents via few-shot prompting + dynamic exemplar retrieval.
- Jira hierarchy is **3 levels**: Epic → Story → Task. Agent's deliverable is **Epic + Story only**. Tasks are out-of-scope (impl-detail, dev-authored).
- Stories come in **4 shapes**: capability, workflow-stage-split, configuration-instance, cleanup. Per-SOP extraction **replicates the Cyto mix** (no in-SOP lifting).
- A **cross-SOP synthesis pass** runs after all SOPs are extracted; clusters concrete stories across SOPs by behavioral similarity; emits a capability-shaped story for clusters of size ≥ 2. Concrete + abstraction stories **coexist** with cross-links.
- **6 agents:** the v3.1 main pipeline (Epic Extractor → Story Extractor → Validator → Cross-SOP Synthesis → Validator → Dependency Resolver) is unchanged in shape; v3.2 adds a *new pre-flight* **Theme Discovery** agent that runs once per discipline before the main pipeline boots. The Epic Extractor now runs in **conditioned mode**.
- **Conditioned Discovery (v3.2 core principle):** both theme catalog and epic catalog are *warm-started* against existing Cytology structure. Pass 1 classifies inputs against the prior catalog at threshold `τ_match` (default 0.65); Pass 2 clusters only the residual at minimum size `ε_novelty` (default 3); Pass 3 routes novel candidates to SME (inherited bypass review); Pass 4 re-tags the corpus on catalog version bump.
- **Versioned catalog naming:** themes use `<discipline>_v<N>` (e.g. `cyto_v1`, `histo_v1`); epics use `<discipline>_epic_v<N>` (e.g. `cyto_epic_v1`, `micro_epic_v1`). Distinct artifacts that version independently. Stories carry `theme_catalog_version` for theme resolution.
- **Validator is type-aware:** classifies the story shape, then applies a shape-specific sub-rubric. Two revisions then SME escalation.
- **Three output streams:** Output A (Jira Epic/Story tree), Output B (per-culture YAML config profiles), Output C (versioned catalog artifacts: theme catalog, epic catalog, ANALOGY map). The ANALOGY map is the explicit cross-discipline link table that replaces v3.1's implicit shared-theme assumption — each link typed identical / partial / discarded_in_target / novel_in_target.
- **G0 / E0 unclassified buckets** are first-class on every catalog with a 5% alarm threshold over a rolling window; alarm trips re-run the appropriate Discovery agent.
- **Greenfield assumption:** POC generates all Micro stories needed, even where Connect-Cyto already implements similar capabilities. Extension-mode (diff-against-Connect) is deferred.

**Architecture history:**
- v1: chat-RAG-epic generation (rejected)
- v2: Cyto-as-anchor-registry with REUSE/ADAPT/NEW deltas (rejected — too much SME burden)
- v3: agent pipeline with single-shape stories (refined)
- v3.1: agent pipeline + 4 story shapes + cross-SOP synthesis + dual config output
- v3.2 (current): v3.1 + pre-flight Theme Discovery + conditioned-mode Epic Extractor + versioned catalogs + ANALOGY map artifact + G0/E0 first-class

**How to apply:**
- Repo at `https://github.com/Rajneesh-Tiwari/LabReq_agent` (public, sanitized name; content still references Labcorp internally — never push raw client Jira screenshots; .gitignore excludes `1000*.jpg/jpeg/png`).
- Working directory: `/home/rajneesh/optum_labreqs`.
- Read `PROGRESS.md`, `DECISIONS.md` (D1–D15 ratified; D16–D19 proposed in `V3_2_SPEC.md`), `OPEN_QUESTIONS.md`, `NEXT_STEPS.md` for current state.
- **Two parallel doc tracks:** (a) `microbio_lims_architecture_walkthrough.{tex,pdf,docx,md}` — the evolution-framed walkthrough showing v3.1+v3.2 deltas; (b) `microbio_lims_architecture_v32.{drawio,docx,md}` — the clean canonical v3.2-only deliverables for team sharing (no v3.1-vs-v3.2 contrast). User iterates on the canonical track (v33 is the latest user-edited iteration). See `feedback_clean_canonical_docs.md` for which track to default to.
- The 13-page drawio (`microbio_lims_architecture.drawio`) and the 13-page v3.2-only deck (`microbio_lims_architecture_v32.drawio`) are the visual references; the latter is reordered to follow execution order (Theme Discovery pre-flight → Agent Pipeline → Epic Extractor (conditioned) → …).
- Source artifacts (Cyto SOPs, Cyto Jira, Micro SOPs) are on Labcorp office systems — not accessible from dev environment. Plan around sanitized samples or move work into Labcorp AWS.
- Deployment target: Labcorp's AWS environment (Bedrock-Claude under the hood).

# What the system does

A subject-matter expert (SME) drops microbiology SOPs into S3. An agent
pipeline, grounded in a hybrid retrieval substrate (BM25 + dense), reads
them and emits two artifacts:

-   **Output A --- Jira-ready Epic / Story tree** for the dev team.
-   **Output B --- One YAML configuration profile per culture** (urine,
    blood, target-pathogen) carrying the concrete typed values.

The existing Cytology Jira backlog is used as a *teaching corpus* ---
example (SOP excerpt → Story) pairs the agent learns the house style
from. It is not a registry to match against. The agent stops at Story;
Tasks (test IDs, library versions, DB columns) are dev-authored once the
team has codebase visibility.

**v3.2 addition --- Conditioned Discovery.** v3.1 generated epics
from-scratch and treated themes G1--G8 as a closed Cyto-derived
vocabulary. v3.2 adds a *warm-start* step at both levels: a new
pre-flight **Theme Discovery agent** bootstraps a discipline's theme
catalog by classifying its SOPs against the prior taxonomy first and
surfacing only the residual as novel; the **Epic Extractor runs in
conditioned mode**, classifying drafts against the prior epic catalog
(`cyto_epic_v1`) before clustering anything new. The result: most themes
and epics inherit by construction with explicit lineage, and only
genuinely-novel structure (with cluster evidence) goes to SME for
ratification. See the v3.2 sections below.

# Key terms (glossary)

  ----------------------------------------------------------------------------------------------------
  Term                                Meaning
  ----------------------------------- ----------------------------------------------------------------
  **SOP**                             Standard Operating Procedure --- the source document the agent
                                      reads.

  **Epic**                            A capability domain. Maps to a Jira Epic. Example: *Microbiology
                                      Specimen Receipt*.

  **Story**                           A dev-actionable unit emitted by the agent. Each Story declares
                                      one of four `shape` values (see below). Maps to a Jira Story.

  **Shape**                           Categorization assigned to each Story at extraction time. Drives
                                      Validator routing and downstream interpretation. Four values:
                                      `capability`, `workflow-stage-split`, `configuration-instance`,
                                      `cleanup`.

  **Theme (G1--G8)**                  Eight content tags that span the LIMS workflow: G1 Pre-Analytic,
                                      G2 Analytic, G3 Post-Analytic, G4 Reporting, G5 QC, G6
                                      Compliance, G7 Instrumentation, G8 Platform. Multi-label per
                                      chunk (a chunk can carry multiple themes with confidence
                                      scores).

  **Teaching corpus**                 The curated set of SME-validated (SOP excerpt → Story) pairs
                                      from Cyto. Used as few-shot exemplars at extraction time.

  **Retrieval slot**                  A parallel retrieval channel scoped to a particular discipline +
                                      theme combination (e.g. PRIMARY = Micro/active-themes, ANALOGY =
                                      Cyto/active-themes). The chat layer fires up to 5 slots per
                                      query.

  **Intent**                          The system's structured interpretation of a user query:
                                      `{action, themes, discipline, granularity, refs, confidence}`.

  **τ (tau)**                         Intent-confidence threshold (default 0.7). Below this, the
                                      system asks a clarifying question rather than retrieving.

  **θ (theta)**                       Retrieval-relevance threshold (default 0.5). If every slot falls
                                      below this, the system refuses to generate.

  **Batch wait**                      The pipeline pause between Validator gate #1 and Cross-SOP
                                      Synthesis. Synthesis cannot run until every per-SOP Story has
                                      cleared gate #1, because cross-SOP recurrence cannot be detected
                                      mid-batch.
  ----------------------------------------------------------------------------------------------------

**v3.2 additions:**

  ----------------------------------------------------------------------------------------------------
  **Conditioned discovery**           A four-pass procedure (classify → cluster residual → SME ratify
                                      → re-tag) that warm-starts a new catalog against an existing
                                      prior, rather than clustering from scratch. Applied at both
                                      theme and epic levels.

  **Prior catalog**                   The existing themes (or epics) that conditioned discovery treats
                                      as the structure-to-reuse. Cyto's catalogs are the prior for
                                      both Micro and Histology bootstraps.

  **Residual**                        Inputs whose classification confidence falls below τ_match in
                                      Pass 1. Only residuals are clustered for novelty.

  **τ_match**                         Match-confidence threshold for Pass 1 (default 0.65). Distinct
                                      from the query-time τ above. Higher τ_match ⇒ eager-to-inherit.

  **ε_novelty**                       Minimum cluster size in Pass 2 (default 3). Higher ⇒ stricter
                                      evidence bar before admitting a novel theme/epic.

  **G0 / E0**                         First-class *unclassified* bucket on every theme catalog (G0)
                                      and epic catalog (E0). 5% alarm threshold over a rolling window
                                      triggers re-running discovery.

  **Catalog versioning**              Theme catalogs are named `<discipline>_v<N>` (e.g.
                                      `cyto_v1`, `histo_v1`); epic catalogs are named
                                      `<discipline>_epic_v<N>` (e.g. `cyto_epic_v1`,
                                      `micro_epic_v1`). They version independently. Stories carry a
                                      `theme_catalog_version` field for theme resolution.

  **ANALOGY map**                     Explicit cross-catalog link table. Each link typed: `identical`
                                      / `partial` / `discarded_in_target` / `novel_in_target`.
                                      Replaces v3.1's implicit shared-theme assumption.
  ----------------------------------------------------------------------------------------------------

# Agent pipeline --- five agents, Validator gates twice

![Agent pipeline. Five agents run as a single batch over the SOP cohort.
The same Validator agent is invoked at two call sites --- once per-SOP
(gate #1), once after synthesis (gate
#2).](diagrams/01_agent_pipeline.png){width="5.833333333333333in"
height="1.4421412948381451in"}

Agent pipeline. Five agents run as a single batch over the SOP cohort.
The same Validator agent is invoked at two call sites --- once per-SOP
(gate #1), once after synthesis (gate #2).

**What each box does and emits:**

1.  **Epic Extractor** --- identifies capability domains across the SOP
    cohort. *Output:* one Epic record per domain.
2.  **Story Extractor** --- runs once per SOP. Emits Stories with the
    `shape` field declared per element (so different elements of the
    same SOP can take different shapes).
3.  **Validator gate #1** --- verifies the declared shape, then applies
    a shape-specific sub-rubric. Two revision rounds; on exhaustion,
    escalate to SME with the failed-checks list visible.
4.  **Cross-SOP Synthesis** --- runs only after gate #1 has cleared the
    entire batch (the *batch wait*). Behavioral-similarity clustering
    over (title + AC + source excerpt). A cluster qualifies only if its
    members come from ≥ 2 *distinct* SOPs (two stories from the same SOP
    do not qualify). Lifts a capability-shaped Story per qualifying
    cluster, recording `cross_links[]` back to the contributing
    concretes. Concrete stories are kept; the capability story is added
    as a sibling, not a replacement.
5.  **Validator gate #2** --- same Validator agent as gate #1, second
    call site; applies the capability rubric only. Synthesized stories
    are a *new* artifact (not a derivative of validated input), so they
    re-pass the bar.
6.  **Dependency Resolver** --- final pass. Resolves story-to-story
    dependencies, stage-split sibling links, and capability-to-child
    links. Outputs Jira-ready artifacts.

**v3.2 modifications inside the main pipeline:** the Epic Extractor (1)
gains *conditioned mode* --- it classifies its drafts against the prior
epic catalog before clustering anything as novel. The other four agents
are unchanged in shape. A *new sixth agent* --- the **Theme Discovery
agent** --- runs as pre-flight (one-time per discipline), not on the
per-SOP critical path. Both are detailed in the next two sections.

# v3.2 Theme Discovery --- pre-flight, one-time per discipline

Theme Discovery runs *before* the main pipeline boots for a new
discipline (and again only when the G0 alarm trips). Its job: emit a
versioned theme catalog (e.g. `histo_v1`) by warm-starting against an
existing prior (e.g. `cyto_v1`). Most themes inherit; novel ones must
clear an evidence bar and an SME gate.

![Theme Discovery --- four passes, pre-flight per discipline. Pass 4
fires only when SME ratification changes the catalog (novel ratified or
theme discarded).](diagrams/09_theme_discovery.png){width="6.5in"}

**Algorithm.** Pass 1 scores each chunk against the prior centroids and
assigns it if `score ≥ τ_match` (default 0.65); otherwise it joins the
residual. Pass 2 clusters only the residuals (HDBSCAN); each cluster of
size `≥ ε_novelty` (default 3) becomes a candidate novel theme; smaller
clusters fall to G0. Pass 3 routes the novel candidates and the G0
sample to SME --- inherited themes bypass review. Pass 4 fires only when
the catalog version bumps, re-classifying the previously-tagged corpus
(including any chunks orphaned by a discarded theme) against
`catalog_v(N+1)`.

**Two knobs control the bias.** `τ_match` (higher ⇒ eager-to-inherit;
risk of forced fits) and `ε_novelty` (higher ⇒ stricter evidence bar
before admitting novelty). The user's stated motive --- "don't just end
up with entirely new ones" --- corresponds to a high `τ_match` and a
non-trivial `ε_novelty`.

**Worked example --- bootstrapping Histology from `cyto_v1`.** Pass 1
classifies 460/600 chunks into G1--G8 (residual = 140, including 12
chunks that fit G7 above `τ_match`). Pass 2 finds 4 clusters above
`ε_novelty`: H1 Tissue Processing (38), H2 Staining (32), H3 Block
Archive (25), H4 Frozen Section (23); 22 chunks → G0 (3.7%, below
alarm). Pass 3: SME confirms all 4 novel themes; flags G7 as redundant
in histo (instrument concerns fold into H1) --- discarded. Pass 4
re-classifies the 12 G7-orphaned chunks against the post-discard
taxonomy (most land in H1, consistent with the ANALOGY map's `G7 → H1,
partial` link). Final `histo_v1`: 11 active themes (7 inherited + 4
novel; G7 recorded in ANALOGY map only). Reuse rate: 7/11 ≈ 64%; 7/8 of
the prior themes (87.5%) survived.

# v3.2 Conditioned Epic Extractor --- match before generate

In v3.1 the Epic Extractor proposed Micro epics from-scratch and
optionally annotated `cyto_epic_analog` post-hoc when retrieval signal
happened to align. In v3.2 the order is reversed: drafts are classified
against the prior epic catalog *first*; matched drafts inherit the
analog by construction; only residuals get clustered for novelty.

![Conditioned Epic Extractor --- the "match?" decision is algorithmic
(not SME-gated; hence neutral coloring). Only the novel branch goes
through SME ratification.](diagrams/10_conditioned_epic_extractor.png){width="6.5in"}

**Result for the Micro POC.** Most Micro epics inherit Cyto's structure
with explicit `epic_analog` populated by construction; only genuinely
novel epics --- e.g. Antibiotic Susceptibility Testing (AST), if it has
no Cyto analog --- emerge with cluster evidence. The dev team reads
`micro_epic_v1` and immediately sees what's reused vs. new without
having to do the mapping themselves.

# Four story shapes --- what "shape" means

A **shape** is the categorization the Story Extractor assigns to each
Story. It tells the Validator which sub-rubric to apply, and tells
downstream consumers (devs reading the backlog, the YAML emitter) how to
interpret the AC. Per-SOP extraction picks one of four shapes per
element. Cross-SOP synthesis only ever emits the `capability` shape.

  --------------------------------------------------------------------------
  Shape                      Use when...             Validator rubric
  -------------------------- ----------------------- -----------------------
  `capability`               The SOP describes a     MUST/SHALL on AC;
                             configurable system     testable;
                             feature you can imagine configurability
                             multiple labs/cultures  boundaries explicit
                             parameterizing          

  `workflow-stage-split`     Same capability, but    Stage explicit in
                             the SOP describes       title; sibling stories
                             different behavior at   enumerated and
                             different workflow      cross-linked
                             stages (e.g. before /   
                             during / after results) 

  `configuration-instance`   Concrete data values    Typed values (units /
                             for one culture / lab.  enums / nullable); SOP
                             *No new feature ---     excerpt cited verbatim.
                             just data.*             *MUST/SHALL not
                                                     required.*

  `cleanup`                  Modify or remove an     Target artifact named;
                             existing artifact       before/after
                             (field, screen, table,  observable; regression
                             deprecated path). *No   risk acknowledged.
                             new feature.*           *MUST/SHALL not
                                                     required.*
  --------------------------------------------------------------------------

![The four story shapes, with example title, AC snippet, and rubric
pointer for each.](diagrams/02_story_shapes.png){width="5.170854111986002in"
height="2.2361800087489065in"}

The four story shapes, with example title, AC snippet, and rubric
pointer for each.

# Schemas --- deep dive

Code blocks below are illustrative JSON / YAML; the production
representation is JSON-schema-validated before persistence. IDs come in
two flavors: a draft ID assigned in-pipeline (e.g. `epic_draft_3`,
`story_draft_42`) and a final Jira-shaped ID (e.g. `EPIC-MICRO-001`,
`STORY-MICRO-1042`) assigned at Jira-push time by the Dependency
Resolver.

## Epic schema (v3.2)

    {
      "id": "EPIC-MICRO-001",
      "title": "Microbiology Specimen Receipt",
      "description": "All capabilities related to receiving and accepting microbiology specimens.",
      "discipline": "microbiology",
      "themes": ["G1", "G5"],
      "theme_catalog_version": "cyto_v1",
      "epic_analog": {
        "catalog_id": "cyto_epic_v1",
        "epic_id": "EPIC-CYTO-007",
        "equivalence": "identical"
      },
      "inheritance_basis": {
        "match_score": 0.78,
        "shared_themes": ["G1"],
        "auto_inherited": true
      }
    }

  ----------------------------------------------------------------------------
  Field                Type              Required          Notes
  -------------------- ----------------- ----------------- -------------------
  `id`                 string            yes               Final Jira-shaped
                                                           Epic ID (or
                                                           `epic_draft_*`
                                                           while in-pipeline).

  `title`              string            yes               Short
                                                           capability-domain
                                                           name.

  `description`        string            yes               One- to
                                                           three-sentence
                                                           scope statement.

  `discipline`         enum              yes               `microbiology` \|
                                                           `histology` \|
                                                           `cytology`.
                                                           Currently always
                                                           `microbiology` for
                                                           the POC.

  `themes[]`           array of G1--G8   yes               Multi-label; an
                                                           Epic can span
                                                           themes (e.g. G1 +
                                                           G5).

  `theme_catalog_version` string         yes               *(v3.2)* The theme
                                                           catalog these tags
                                                           resolve in (e.g.
                                                           `cyto_v1` for Micro
                                                           POC, `histo_v1` for
                                                           Histology).

  `epic_analog`        object            optional          *(v3.2 --- replaces
                                                           `cyto_epic_analog`)*
                                                           Cross-catalog link
                                                           `{catalog_id,
                                                           epic_id,
                                                           equivalence}`.
                                                           Populated by the
                                                           conditioned Epic
                                                           Extractor when
                                                           `match_score ≥
                                                           τ_match`.

  `inheritance_basis`  object            optional          *(v3.2)* Provenance
                                                           for inherited epics
                                                           `{match_score,
                                                           shared_themes[],
                                                           auto_inherited}`.
                                                           Absent for novel
                                                           epics; those carry
                                                           `novelty_basis`.
  ----------------------------------------------------------------------------

## Story schema

    {
      "id": "STORY-MICRO-1042",
      "epic_id": "EPIC-MICRO-001",
      "shape": "capability",
      "title": "Configurable specimen rejection rules engine",
      "description": "As an admin, I want configurable specimen rejection rules so that each lab can codify its own acceptance criteria.",
      "acceptance_criteria": [
        { "when": "rule is defined", "then": "rule has {predicate, threshold, action}" },
        { "when": "specimen received", "then": "applicable rules evaluated; rejection record emitted" }
      ],
      "source_citations": [
        { "doc_id": "doc_micro_014_v3", "section": "Procedure §3.2", "line_range": [41, 43] }
      ],
      "dependencies": ["STORY-MICRO-1018"],
      "cross_links": ["STORY-MICRO-1043", "STORY-MICRO-1044", "STORY-MICRO-1045"],
      "estimated_complexity": "M",
      "edge_cases_handled": ["operator override", "rule conflict resolution"],
      "status": "validated",
      "source_chunks": ["chunk_001", "chunk_017"]
    }

  ---------------------------------------------------------------------------------------------------------
  Field                     Type                              Required          Notes
  ------------------------- --------------------------------- ----------------- ---------------------------
  `id`                      string                            yes               Final Jira-shaped Story ID
                                                                                (or `story_draft_*` while
                                                                                in-pipeline).

  `epic_id`                 string                            yes               FK to parent Epic.

  `shape`                   enum                              yes               One of `capability`,
                                                                                `workflow-stage-split`,
                                                                                `configuration-instance`,
                                                                                `cleanup`. Drives Validator
                                                                                routing.

  `title`                   string                            yes               Concrete and unambiguous.
                                                                                For stage-split, must name
                                                                                the stage.

  `description`             string                            yes               User-story format preferred
                                                                                for capability/stage-split;
                                                                                descriptive prose for
                                                                                config-instance/cleanup.

  `acceptance_criteria[]`   array of                          yes               Capability/stage-split use
                            `{when, then, expected_value?}`                     MUST/SHALL phrasing;
                                                                                config-instance carries
                                                                                `expected_value`; cleanup
                                                                                carries before/after.

  `source_citations[]`      array of                          yes               Must resolve to indexed
                            `{doc_id, section, line_range}`                     chunks; verbatim excerpt
                                                                                for config-instance.

  `dependencies[]`          array of Story IDs                optional          Stories that must complete
                                                                                before this one is
                                                                                workable.

  `cross_links[]`           array of Story IDs                optional          Capability ↔ concrete
                                                                                contributors; stage-split
                                                                                sibling group. Backbone of
                                                                                the Story DAG.

  `technical_hints`         string                            optional          Dev-facing guidance
                                                                                (e.g. "consider extending
                                                                                the existing rules table").

  `estimated_complexity`    enum                              yes               `S` \| `M` \| `L`.
                                                                                Heuristic, used for sprint
                                                                                sizing.

  `edge_cases_handled[]`    array of strings                  optional          Surfaced corner cases.

  `status`                  enum                              yes               `draft` \| `validated` \|
                                                                                `ready`. Validated = passed
                                                                                the Validator gate; ready =
                                                                                SME-accepted.

  `source_chunks[]`         array of chunk IDs                yes               Audit trail back to
                                                                                retrieval-substrate chunks.
  ---------------------------------------------------------------------------------------------------------

## Cluster schema (intermediate, in Cross-SOP Synthesis)

Not persisted to Jira; lives only between gate #1 and gate #2 in memory.

    {
      "cluster_id": "clust_rejection_3sop",
      "member_story_ids": ["STORY-MICRO-1043", "STORY-MICRO-1044", "STORY-MICRO-1045"],
      "source_sops": ["doc_micro_014_v3", "doc_micro_022_v1", "doc_micro_037_v2"],
      "centroid_summary": "Reject specimen on a culture-specific predicate (turbidity / hemolysis / container).",
      "proposed_capability_title": "Configurable specimen rejection rules engine"
    }

A cluster qualifies for lifting **iff** `len(unique(source_sops)) >= 2`.
Two stories from the same SOP do not qualify, even if they cluster
tightly.

## Validator output schema

    {
      "story_id": "STORY-MICRO-1042",
      "verdict": "revise",
      "shape_declared": "capability",
      "shape_verified": "capability",
      "failed_checks": [
        { "rule": "must_shall_present", "severity": "error", "message": "AC 1 lacks MUST/SHALL phrasing." },
        { "rule": "ambiguous_quantifier", "severity": "error", "message": "AC 2 uses 'appropriate' — replace with concrete predicate." }
      ],
      "attempt": 1
    }

  -----------------------------------------------------------------------------
  Field                   Type                          Notes
  ----------------------- ----------------------------- -----------------------
  `story_id`              string                        The Story under review.

  `verdict`               enum                          `accept` (story
                                                        passes), `revise`
                                                        (return to extractor
                                                        with `failed_checks`,
                                                        attempt \< 2), or
                                                        `escalate` (after 2
                                                        failed revisions;
                                                        routed to SME).

  `shape_declared`        enum                          The shape the Story
                                                        Extractor assigned.

  `shape_verified`        enum                          The shape the Validator
                                                        believes is correct. If
                                                        it differs from
                                                        `shape_declared`, the
                                                        verdict is
                                                        automatically `revise`.

  `failed_checks[]`       array of                      Empty when
                          `{rule, severity, message}`   `verdict = accept`.

  `attempt`               integer                       1 or 2 (after 2, the
                                                        verdict becomes
                                                        `escalate`).
  -----------------------------------------------------------------------------

## Theme catalog schema (v3.2)

    catalog_id: histo_v1
    parent_catalog: cyto_v1
    discipline: histology
    inherited_themes:
      - { id: G1, name: Pre-Analytic, source: cyto_v1, match_count: 142 }
      ...
    novel_themes:
      - id: H1
        name: Tissue Processing
        source: histo_v1
        cluster_evidence: { n_chunks: 38, sample_excerpts: [...] }
        sme_confirmed: true
    discarded_themes:
      - { id: G7, reason: "Folded into H1 (partial)", chunks_re_tagged: 12 }
    unclassified_bucket: { count: 22, pct_of_total: 3.7 }

  -----------------------------------------------------------------------------
  Field                    Type             Required   Notes
  ------------------------ ---------------- ---------- -------------------------
  `catalog_id`             string           yes        `<discipline>_v<N>`.
                                                       Stories reference this in
                                                       `theme_catalog_version`.

  `parent_catalog`         string \| null   yes        The prior the discovery
                                                       was conditioned on.
                                                       `null` only for the very
                                                       first ever (`cyto_v1`).

  `inherited_themes[]`     array            yes        Themes that survived
                                                       `parent_catalog` after
                                                       Pass 1. Each has
                                                       `source: <parent>` and a
                                                       `match_count`.

  `novel_themes[]`         array            yes        SME-ratified novelties
                                                       from Pass 2. Each carries
                                                       `cluster_evidence`. May
                                                       be empty.

  `discarded_themes[]`     array            optional   Parent themes the SME
                                                       dropped. `chunks_re_tagged`
                                                       records the Pass 4 fixup
                                                       count.

  `unclassified_bucket`    object           yes        G0 stats: `{count,
                                                       pct_of_total,
                                                       sample_excerpts,
                                                       next_review_due}`.
                                                       Always present. 5% alarm
                                                       threshold.
  -----------------------------------------------------------------------------

## Epic catalog schema (v3.2)

    catalog_id: micro_epic_v1
    parent_catalog: cyto_epic_v1
    discipline: microbiology
    inherited_epics:
      - id: EPIC-MICRO-001
        title: Specimen Receiving
        epic_analog: { catalog_id: cyto_epic_v1, epic_id: EPIC-CYTO-014, equivalence: identical }
        inheritance_basis: { match_score: 0.78, shared_themes: [G1], auto_inherited: true }
    novel_epics:
      - id: EPIC-MICRO-007
        title: Antibiotic Susceptibility Testing (AST)
        epic_analog: null
        novelty_basis: { n_draft_epics: 4, sme_confirmed: true }
    unclassified_drafts: { count: 3, pct_of_total: 4.1 }

The epic catalog versions independently from the theme catalog and uses
the suffix `_epic_` to make the naming distinction explicit. The
`epic_analog` field, when populated, carries a struct (not a bare
string) so the catalog the analog points into is unambiguous.

## ANALOGY map schema (v3.2)

    source_catalog: cyto_v1
    target_catalog: histo_v1

    theme_links:
      - { source: G1,   target: G1, equivalence: identical }
      - { source: G7,   target: H1, equivalence: partial,
          note: "G7 has no top-level peer in histo_v1 (discarded);
                 concept partially absorbed by H1 for slide-prep instruments." }
      - { source: null, target: H2, equivalence: novel_in_target }
      ... (H3, H4)

    epic_links:
      - { source: EPIC-CYTO-014, target: EPIC-HISTO-002, equivalence: identical }

  -----------------------------------------------------------------------------
  `equivalence`              Meaning
  -------------------------- ---------------------------------------------------
  `identical`                Full equivalence; `match_score` above `τ_match`,
                             SME-confirmed by spot-check.

  `partial`                  Loose mapping or scope difference; SME-confirmed
                             each individually. Carries a `note`.

  `discarded_in_target`      Source has no top-level peer in target.

  `novel_in_target`          Target has no source ancestor (encoded as
                             `source: null`).
  -----------------------------------------------------------------------------

**Convention.** Each source theme appears at most once as `source`.
"Discarded with partial mapping" is a single `partial` entry whose note
explains the discard --- *not* two contradictory entries (`partial` plus
`discarded_in_target`). Similarly, a target theme covered by a `partial`
link does not also need a separate `novel_in_target` entry; the partial
link already records its origin.

# Story relationships (graph view)

The Story schema's flat `dependencies[]` and `cross_links[]` arrays
serialize a directed acyclic graph. Walking it answers operational
questions like "what's blocked by X?" or "if I deprecate the synthesized
capability story, which concretes need merging?" Below is a worked
sub-graph for one Epic.

![Worked example: one Epic with four Stories of different shapes, plus
three concrete contributors to the synthesized capability. Edge types:
parent_of (Epic→Story), cross_links (Cap1 → C1/C2/C3), depends_on (Cap1
→ Conf1).](diagrams/07_story_dag.png){width="5.407034120734908in"
height="1.8542705599300087in"}

Worked example: one Epic with four Stories of different shapes, plus
three concrete contributors to the synthesized capability. Edge types:
parent_of (Epic→Story), cross_links (Cap1 → C1/C2/C3), depends_on (Cap1
→ Conf1).

**Edge semantics:**

  -----------------------------------------------------------------------
  Edge                    Direction               Meaning
  ----------------------- ----------------------- -----------------------
  `parent_of`             Epic → Story            Implicit Jira hierarchy
                                                  (encoded in `epic_id`).

  `cross_links`           Story ↔ Story           Bidirectional
                                                  association. Used for
                                                  capability ↔ concrete
                                                  (synthesis) and
                                                  stage-split sibling
                                                  sets.

  `depends_on`            Story → Story           Directed prerequisite.
                                                  The Dependency Resolver
                                                  uses it to
                                                  topologically order the
                                                  backlog for sprint
                                                  planning.
  -----------------------------------------------------------------------

# Cross-SOP synthesis --- recurrence becomes capability

![Three concrete rejection stories --- one per SOP --- cluster
behaviorally and lift to a single capability story. Concrete stories
remain in the backlog; the capability is added as a sibling with
cross-links back.](diagrams/03_cross_sop_synthesis.png){width="5.326632764654418in"
height="1.5125623359580052in"}

Three concrete rejection stories --- one per SOP --- cluster
behaviorally and lift to a single capability story. Concrete stories
remain in the backlog; the capability is added as a sibling with
cross-links back.

The recurrence threshold (≥ 2 distinct SOPs) is tunable. With three SOPs
in the POC, this means anything seen in two of three lifts. The
synthesized capability story passes through Validator gate #2 before
persistence.

# Cyto → Micro lineage (graph view)

Three distinct mechanisms transfer information from Cyto to Micro. They
operate at different times in the system's life cycle.

![Three Cyto → Micro information transfer mechanisms, each operating at
a different time of use.](diagrams/08_cyto_micro_lineage.png){width="5.24623031496063in"
height="2.08040135608049in"}

Three Cyto → Micro information transfer mechanisms, each operating at a
different time of use.

  ---------------------------------------------------------------------------
  Mechanism             Direction         When it fires     What flows
  --------------------- ----------------- ----------------- -----------------
  `epic_analog`         Cyto Epic → Micro Epic Extractor    Just an ID
                        Epic              (annotation)      reference ---
                                                            Cyto Epic is
                                                            recorded on the
                                                            Micro Epic for
                                                            SME traceability
                                                            (D13).

  `exemplar_of`         Cyto Story →      Story Extractor   The Cyto (excerpt
                        Micro Story       (few-shot prompt) → Story) pair
                                                            lands in the
                                                            prompt as an
                                                            in-context
                                                            example.

  `retrieval_analogy`   Cyto chunks →     Per-query         Retrieved Cyto
                        chat prompt       retrieval (slot 2 excerpts populate
                                          ANALOGY)          the ANALOGY
                                                            context section
                                                            of the LLM
                                                            prompt. *Adapt,
                                                            don't copy.*
  ---------------------------------------------------------------------------

The same Cyto material thus serves three roles: a curated few-shot
teaching set, an indexed corpus for live retrieval, and a structural
reference at the Epic level.

# v3.2 ANALOGY map (graph view) --- explicit cross-discipline links

When a discipline's theme catalog diverges from its parent (Histology
drops G7, adds H1--H4), the ANALOGY map records the cross-catalog
correspondences explicitly. Each link is typed --- the legend in the
figure shows what each line style means.

![ANALOGY map (cyto_v1 ↔ histo_v1). 6 identical theme links, 1 partial
(G7 → H1), 4 novel-in-target (H1--H4). H1 has no separate
`novel_in_target` edge because the partial G7 → H1 link already records
its origin.](diagrams/11_analogy_map.png){width="6.5in"}

The ANALOGY map drives the ANALOGY retrieval slot for cross-discipline
queries: when a Histo question wants Cyto context, the map filters Cyto
chunks down to themes that have a target-side correspondent.

# Ingestion substrate --- S3 to indexed chunks

The substrate runs offline whenever a document lands in S3. It is the
same substrate the agent pipeline above retrieves from at every step.

![Ingestion pipeline: S3 → SQS → Parse → Doc Process → Chunk → Enrich →
Embed → Store. Original documents stay in S3 as the citation
target.](diagrams/04_ingestion.png){width="5.145728346456693in"
height="1.2311548556430447in"}

Ingestion pipeline: S3 → SQS → Parse → Doc Process → Chunk → Enrich →
Embed → Store. Original documents stay in S3 as the citation target.

**I/O trace --- one document through the pipeline
(**`SOP-MICRO-014_Gram-Stain_v3.docx`**):**

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Stage                               Output
  ----------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Parse**                           `text: 28,420 chars / 18 pages; format: docx; ocr_used: false; parse_ms: 320`

  **Doc Process**                     `doc_id: doc_micro_014_v3_abc12; discipline: Microbiology; version: v3; section_map: {Purpose:[200,450], Procedure:[721,2400], AC:[2401,3100], QC:[3101,3650]}`

  **Chunk**                           \~150 chunks; e.g. `chunk_001: section=Procedure §3.1, tokens=287`

  **Enrich (chunk_001)**              `entities: {organisms:["Gram-positive cocci"], specimens:["sputum"], codes:["87209"]}; phi_detected: false; themes: {G2: 0.84, G5: 0.41}`

  **Embed (chunk_001)**               `dense_vector: [0.0234, -0.1849, ..., 0.2891]` (1024-d, Bedrock Titan v2); `bm25_tokens_enriched: ["slide","preparation","87209","smear","primary","source",...]`

  **Store**                           `PUT chunk_001` → OpenSearch k-NN (vector), OpenSearch BM25 (sparse), DynamoDB chunk_metadata (entities, themes, phi_status, version)
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Retrieval substrate --- per query, real-time

![Per-query path: Query → Pre-process → Intent decode →
confidence/action decision → Expand → multi-slot hybrid retrieve →
Rerank → Assemble role-labeled context →
Generate.](diagrams/05_retrieval.png){width="5.833333333333333in"
height="1.925326990376203in"}

Per-query path: Query → Pre-process → Intent decode → confidence/action
decision → Expand → multi-slot hybrid retrieve → Rerank → Assemble
role-labeled context → Generate.

Two thresholds gate the chat to prevent hallucination:

-   **τ = 0.7** intent confidence --- below this, ask a clarifying
    question instead of retrieving.
-   **θ = 0.5** retrieval relevance --- if every slot falls below,
    refuse and offer the user three options (upload SOPs, draft from
    analogy with caveat, clarify scope).

**I/O trace --- one query: *"Generate epics for specimen rejection in
microbiology"***

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Stage                               Output
  ----------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Intent decode**                   `centroid_dist: {G1: 0.81, G5: 0.18}`; classifier: `{action: generate, themes: [G1, G5], discipline: Micro, granularity: epic, refs: [], conf: 0.91}`; decision: PROCEED (τ=0.7, 0.91 ≥ τ)

  **Retrieve**                        48 candidate chunks across 5 slots --- slot_1 PRIMARY (Micro/G1+G5): 20; slot_2 ANALOGY (Cyto/G1+G5): 10; slot_3 ADJACENT (Micro/G2 neighbors): 10; slot_4 EXEMPLAR (Jira, generate∧epic): 5; slot_5 REG (CLSI on G5): 3

  **Rerank + Assemble**               trim: 8/4/3/3/2 = 20 chunks (all slots ≥ θ=0.5); prompt sections: PRIMARY, ANALOGY, ADJACENT, EXEMPLAR, REG + session drafts + output schema; total tokens: 6,840

  **Generate**                        structured JSON:
                                      `{ id: "epic_draft_3", title: "Specimen Rejection Workflow", themes: ["G1", "G5"], citations: ["s3://.../SOP-MICRO-007 §AC", "s3://.../SOP-CYTO-021 §Procedure", "CLSI M22 §3.4"], stories: [{title: "Validate transport temp", ...}, {title: "Flag specimens older than 4h", ...}] }`.
                                      The `id` is a draft ID at this stage --- the Dependency Resolver replaces it with the final `EPIC-MICRO-*` form before Jira push.
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Validator --- shape-aware revise/escalate flow

![Validator flow: shape verification + sub-rubric → pass? → ACCEPT, or
Revise (up to 2 attempts) → SME escalate on exhaustion. Same flow at
both gates.](diagrams/06_validator_flow.png){width="4.015074365704287in"
height="1.0251246719160105in"}

Validator flow: shape verification + sub-rubric → pass? → ACCEPT, or
Revise (up to 2 attempts) → SME escalate on exhaustion. Same flow at
both gates.

**Sub-rubrics by shape (cheat sheet):**

-   **Capability:** MUST/SHALL on every AC; testable; no ambiguous
    quantifiers (`appropriate`, `relevant`, `necessary`);
    configurability boundaries called out; SOP citation present and
    resolves; complexity S/M/L; edge cases enumerated.
-   **Stage-split:** stage explicit in title; entry/exit observable per
    stage; siblings enumerated and cross-linked; transition contract
    clear (what changes between stages); boundary cases handled.
-   **Configuration-instance:** typed concrete values (units, enums,
    nullable rules); target table/profile named
    (e.g. `cultures/urine.yaml#centrifugation`); SOP excerpt cited
    verbatim; scope (culture/lab) stated. *MUST/SHALL not required ---
    this is data, not capability.*
-   **Cleanup:** target artifact named (id, screen path, file path);
    before/after observable (field present → absent, etc.); regression
    risk acknowledged (downstream readers); DoD includes a smoke test or
    QA path. *MUST/SHALL not required.*

# What ships --- Output A and Output B

## Output A --- Jira artifacts

A connected Epic / Story graph (the DAG above), pushed to Jira via REST.
The graph is what the dev team works against; the YAML profile (Output
B) is what their code consumes at runtime.

## Output B --- Per-culture YAML configuration profile

One YAML file per culture in scope. The profile carries the concrete
typed values that `configuration-instance` Stories' AC referenced.
Profiles are versioned, dated, and cite back to the SOPs they draw from.
**The Story body never duplicates these values** --- it references them
by `related_story_ac`, so a single source of truth is preserved.

The profile is partitioned by workflow stage so that an engineer can
find the right block at a glance:

-   `pre_analytic` --- what happens before the specimen reaches the
    bench: collection, transport, rejection predicates.
-   `analytic` --- the bench work itself: centrifugation, inoculation,
    incubation.
-   `post_analytic` --- what happens after the result: reporting
    thresholds, downstream notifications.

### Full profile structure

    profile:
      culture: urine                       # urine | blood | target_pathogen
      version: 3                           # bumps when any value changes
      effective_date: 2026-04-15
      source_sops: [doc_micro_014_v3, doc_micro_022_v1]

    pre_analytic:
      collection:
        container:    {value: "sterile cup", units: enum, citation: "doc_micro_014_v3 §1.2 L8"}
        volume_min:   {value: 10, units: mL, citation: "doc_micro_014_v3 §1.2 L11"}
      transport:
        temp_range:   {min: 2, max: 8, units: degC, citation: "doc_micro_014_v3 §1.4 L18-19"}
        time_max:     {value: 4, units: h, citation: "doc_micro_014_v3 §1.4 L20"}
      rejection_predicates:
        - id: REJ_TURBID
          condition: "turbidity > threshold"
          threshold: {value: 200, units: NTU}
          action: reject
          citation: "doc_micro_014_v3 §1.5 L24"

    analytic:
      centrifugation:
        speed:    {value: 1500, units: g,    citation: "doc_micro_014_v3 §3.2 L41-43"}
        duration: {value: 5,    units: min,  citation: "doc_micro_014_v3 §3.2 L44"}
        temp:     {value: 4,    units: degC, citation: "doc_micro_014_v3 §3.2 L45"}
      inoculation:
        media:
          - {type: BAP,   volume_uL: 10, citation: "doc_micro_014_v3 §4.1 L52"}
          - {type: MAC,   volume_uL: 10, citation: "doc_micro_014_v3 §4.1 L53"}
        incubation: {temp: 35, atmosphere: "5% CO2", duration_h: 18, citation: "doc_micro_014_v3 §4.3 L60"}

    post_analytic:
      reporting:
        cfu_threshold: {value: 100000, units: CFU_per_mL, citation: "doc_micro_014_v3 §6.1 L88"}

    related_story_acs:                     # back-references to Stories that consume this profile
      - STORY-MICRO-1042#AC-2              # Configurable rejection rules engine
      - STORY-MICRO-1077#AC-1              # Centrifugation step

### How a Story's AC references the profile

A `configuration-instance` Story's AC carries the citation; the profile
is what gets read by code. Example --- `STORY-MICRO-1077` (urine
centrifugation):

    acceptance_criteria:
      - when: "urine profile loaded"
        then: "centrifuge step uses cultures/urine.yaml#analytic.centrifugation"
        expected_value: "speed=1500g, duration=5min, temp=4degC"

### Where to put a value: Story body vs. profile

  -----------------------------------------------------------------------
  If the value is...                  Put it in...
  ----------------------------------- -----------------------------------
  The same across cultures and        Story body as parameter spec
  parameterizable in the rules engine (capability shape)

  Different per culture / different   YAML profile
  per lab                             (configuration-instance shape)

  A literal constant in the rejection Profile, with the Story's AC
  logic                               pointing at it
  -----------------------------------------------------------------------

# Cross-cutting

KMS encryption at rest and in transit; IAM least-privilege with VPC
endpoints (Bedrock calls stay in-VPC); DLQ for parse / OCR / embed
failures; CloudWatch metrics and alarms (e.g. OCR fail-rate \> 5%);
CloudTrail audit log on every API call; idempotent ingestion via
content-hash dedupe.

**Generalization (v3.2):** when Histology arrives, Theme Discovery runs
once as pre-flight to warm-start `histo_v1` from `cyto_v1` (most themes
inherited; novel ones SME-ratified). The main pipeline then runs
unchanged in shape, with the Epic Extractor in conditioned mode
bootstrapping `histo_epic_v1` from `cyto_epic_v1`. No model retraining
at any stage.

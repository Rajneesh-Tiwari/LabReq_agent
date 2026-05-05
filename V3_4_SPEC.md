# v3.4 Spec — Static Catalogs + SME-Free Operation

**Status:** Draft
**Layers on:** v3.2 (Conditioned Discovery). v3.3 is a documentation iteration, not an architectural step.
**Carries forward unchanged:** the 5-agent main pipeline, the four story shapes, cross-SOP synthesis, the type-aware Validator (with extended rubric), the per-culture YAML profile, Cyto's role as a teaching corpus, the conditioned-discovery algorithm shape, and the substrate (S3 / OpenSearch / Bedrock / DynamoDB).

---

## 1. Motivation

Two operational constraints land on top of v3.2 and force a re-think of every gate that assumes human-in-the-loop SME involvement:

1. **Tests and personas are static.** The discipline's lab tests (Gram stain, blood-culture incubation, MALDI identification, AST, etc.) and user personas (specimen receiver, micro tech, lead tech, supervisor, billing clerk, etc.) are known and frozen at project start. They cannot drift mid-flight; they don't grow as new SOPs land. They are received as pre-curated YAML inputs, not produced by the pipeline. v3.2's conditioned-discovery machinery doesn't apply to either dimension.

2. **No SME is available.** Every SME gate in v3.2 — theme novelty ratification, epic novelty ratification, Validator escalation, G0/E0 alarm response, exemplar curation, rubric calibration, scope confirmation — must be replaced with an automated mechanism. The pipeline must produce defensible output without any human-in-the-loop step.

These constraints are independent but they compose. Static tests/personas already remove two SME involvement points (catalog curation, novelty ratification at the test/persona level) and convert two retrieval/validation dimensions to closed enums. The SME-free constraint then dictates how to handle the remaining gates that v3.2 had assigned to a human reviewer.

The combined effect is a tighter, more constrained, more deterministic pipeline — at the cost of higher false-rejection rates at points where SME judgment was previously load-bearing. This spec describes how to absorb that cost defensibly.

---

## 2. Core principle

> **Pre-curate what was discoverable; automate what was reviewable.**

Two corollaries:

- **Pre-curate.** The two would-be discovery domains (tests, personas) become static reference inputs delivered at project start. No conditioned discovery; no τ_match / ε_novelty knobs for these dimensions; no SME ratification gate; no G0/E0-equivalent alarm. Closed-enum vocabularies feed both the agents and the Validator.
- **Automate.** Every remaining SME gate is replaced by one of four automated primitives, depending on the gate's nature:

| Original SME function | Replacement primitive |
|---|---|
| Ratify novel themes/epics from a discovery cluster | **Multi-agent quorum** |
| Curate exemplars from Cyto SOPs | **Cyto-as-oracle** (use existing Cyto Jira) |
| Calibrate Validator sub-rubrics | **Cyto-as-oracle** (Cyto holdout) |
| Escalation target for failed-twice Validator | **Auto-park** (rejected queue) |
| Review G0/E0 alarm trip | **Tightened thresholds + drift report** |
| Confirm out-of-scope SOPs | **Hard scope-check at intake** |
| Curate ANALOGY map links | **Static (test/persona) or automated (theme/epic)** |

§4 defines each primitive. §5 shows where each one lands phase by phase.

---

## 3. Glossary (delta vs v3.2)

- **Multi-agent quorum.** A panel of N independent classifier agents that vote on whether to admit a novelty candidate. Independence is enforced via prompt-frame diversity (different reasoning angles) and optionally model diversity. M-of-N agreement is required for admission. Default N=5, M=4.
- **Cyto-as-oracle.** A pattern that uses Cyto's existing SME-validated artifacts as ground truth for automated calibration: Cyto Jira stories serve as the exemplar pool (filtered by quality signals), and a Cyto holdout set drives Validator rubric calibration without an active SME.
- **Auto-park.** A terminal state for stories that fail Validator after 2 revision attempts. The story does not reach Output A (Jira tree); it lands in a `parked/` queue with the failed-checks list visible. The pipeline does not block.
- **Drift report.** A weekly auto-generated artifact summarizing novelty admissions and rejections (with quorum vote tallies), parked-story counts, G0/E0 bucket sizes, alarm trips, and threshold-tightening events. Reviewable by anyone but blocks nothing.
- **Intake scope-check.** A hard gate at SOP ingestion that compares the SOP's test-tag profile against the closed test catalog. SOPs with too high a fraction of out-of-catalog test references are rejected at intake.
- **Closed-enum field.** A schema field whose values are drawn from a fixed catalog (`tests[]` from `<discipline>_test_v<N>`, `persona` from `<discipline>_persona_v<N>`). Validator rejects values outside the catalog as a hard error (no revise loop).

Terms unchanged from v3.2 (shape, theme, intent, τ_match, ε_novelty, etc.) are defined in `microbio_lims_architecture_v32.md` and `V3_2_SPEC.md`.

---

## 4. The four SME-replacement primitives

### 4.1 Multi-agent quorum

Used at every place v3.2 said "SME ratifies a novelty candidate." Theme Discovery Pass 3 and Epic Discovery Pass 3 both invoke the quorum.

**Mechanism:**

```
INPUT:
  candidate_novel_entry: { description, members, evidence }
  prior_catalog
  N: panel size (default 5)
  M: agreement threshold (default 4)

For each agent in 1..N, run a distinct prompt frame:
  Agent 1: "Is this a coherent novel theme?" (binary, with reasoning)
  Agent 2: "Compare to existing themes — distinct or fold-in?"
  Agent 3: "Synthesize a one-line description; is it sharp?"
  Agent 4: "Are the cluster members behaviorally consistent?"
  Agent 5: "Would admitting this fragment the catalog into too-fine pieces?"

Each agent returns: admit | fold-in (with target) | reject.

Decision:
  if ≥ M agents return admit AND description-cosine-convergence ≥ 0.8
    on the synthesized one-liners:
    → admit, with the consensus description as the entry's name
  else if ≥ M agents return fold-in to the same existing entry:
    → fold-in (no novel entry; cluster members tagged to that existing entry)
  else:
    → park to G0/E0 (don't admit, don't fold-in; leave for next alarm cycle)
```

**Why it works:** independent prompts catch different failure modes — Agent 1 catches incoherent clusters, Agent 2 catches near-duplicates of existing entries, Agent 5 catches taxonomy fragmentation. Requiring M-of-N filters single-agent overconfidence.

**Cost:** 5× the discovery LLM calls. Acceptable because Discovery runs rarely (once per discipline + on alarm).

**Failure modes:**
- All N agents agree but agree wrongly (correlated error). Mitigated by prompt diversity, not eliminated. Audit log allows post-hoc human review.
- Agents agree on admission but disagree on description. Mitigated by description-convergence check; on disagreement, defer to G0.

**Tuning:** if first-run quorum admits too few (G0 explodes), lower M to 3-of-5. If it admits too many (catalog pollutes), raise to 5-of-5 or N to 7.

### 4.2 Cyto-as-oracle

Used at every place v3.2 said "SME curates" or "SME calibrates." Two applications:

**Exemplar bootstrap:**
- Cyto Jira already contains SME-validated stories (the existing dev backlog has been through Cyto's review process).
- Filter by quality signals: non-empty AC list, linked test cases, no `WIP` or `draft` tags, source citations resolve, status not new/backlog.
- Trace each surviving story to its source SOP excerpt via `source_citations[]`. If citations are missing, use retrieval over Cyto SOPs to find the most-likely originating excerpt.
- The resulting (excerpt → story) pairs become the exemplar corpus, tagged with their (test, persona, shape) tuple at ingestion for precision-targeted retrieval.

**Rubric calibration:**
- Hold out 20% of Cyto stories per shape as a calibration set.
- Run the Validator's shape-specific sub-rubric over the holdout.
- Tune thresholds (AC granularity cutoffs, "concrete value" detector thresholds, etc.) until acceptance rate on the holdout is ≥ 95%.
- This calibrates against Cyto's quality bar, not the dev team's actual Micro bar — acceptable proxy for POC.

**Failure modes:**
- Cyto Jira inaccessible or insufficiently sanitized for use outside Labcorp office network. Existing OPEN_QUESTIONS item that becomes load-bearing under v3.4. If unresolvable, the exemplar corpus has no source.
- Some shapes (cleanup, configuration-instance) may be under-represented in Cyto. For under-represented shapes, fall back to v3.2's manually-specified rubrics.

### 4.3 Auto-park

Used at every place v3.2 said "Validator escalates to SME after 2 revisions."

**Mechanism:**
- After 2 failed revision attempts, story status transitions to `quality: parked`.
- Parked stories carry the full failed-checks list and the original SOP excerpt.
- They are written to a `parked/` queue, not to Output A.
- The pipeline does not block; subsequent stories continue to extract.
- The drift report (§4.4) summarizes parked-story volume per run.

**Strict mode (default):** parked stories are visible only to architect/PM review, not to the dev team. Recall lost; precision preserved.

**Permissive mode:** parked stories reach Output A flagged `quality: review_needed`. Recall preserved; precision lost — dev team must triage.

**Recommended:** start strict for POC. Switch to permissive only if parked-story volume is below 5% (acceptable false-rejection rate).

**Failure modes:**
- Genuinely good stories may be parked when the rubric mishandles an edge case. Mitigation: rubric calibration via Cyto-as-oracle (§4.2) reduces edge-case failures; periodic batch review of the parked queue catches systematic mishandling.

### 4.4 Tightened thresholds + drift report

Used at G0/E0 alarm trip events. v3.2 said "SME re-runs Discovery on alarm." v3.4 says re-run automatically with adjusted thresholds, and emit a drift report for any reviewer.

**Mechanism on alarm trip:**
- G0 (theme) > 5% rolling-window chunk volume → re-run Theme Discovery.
- E0 (epic) > 5% rolling-window draft-epic volume → re-run Epic Discovery.
- On re-run, lower `τ_match` by 0.05 (more eager to inherit). This compensates for whatever made the bucket grow in the first place — usually that prior-catalog matches were too strict.
- Repeated tightening is bounded: floor at `τ_match = 0.50`. Below this, automated tightening stops; the drift report flags the discipline for manual catalog re-curation.
- New candidates from the re-run go through the multi-agent quorum (§4.1).

**Drift report contents (auto-generated weekly + on every alarm trip):**
- Quorum decisions: candidates admitted / folded-in / parked, with vote tallies.
- Parked-story counts per shape per culture.
- G0/E0 bucket sizes and trend (last 4 weeks).
- Alarm trips and threshold-tightening events.
- Catalog version bumps in the period.
- Per-SOP intake stats: accepted, scope-rejected, in-flight.

**Reviewer:** anyone — architect, PM, dev lead. Report is informational; nothing in the pipeline waits on it. A reviewer who spots a drift trend can request a manual re-curation, which is itself a code change to the catalog YAML, not a runtime SME action.

**Failure modes:**
- Compound drift: repeated alarm trips with τ_match repeatedly lowered may accept too much novelty without anyone catching it. Floor at 0.50 + drift report visibility are the two safeties.
- Quiet failure: drift report goes unread. Mitigated by emitting into a known channel (dashboard, Slack, Jira ticket) with the trend visible at a glance.

---

## 5. What changes at each phase

### 5.1 Phase 0 — Substrate (chunk enrichment gains two tagging passes)

Today: chunk enrichment tags each chunk with a soft theme.

With static tests + personas: enrichment runs three tagging passes per chunk:
- **Theme tag** — unchanged. Soft tag against the theme catalog. Theme Discovery still applies for new disciplines.
- **Test tag** — closed-enum lookup against `<discipline>_test_v1`. Cheap (regex + ontology, or short LLM prompt with the catalog inlined). Each chunk gets 0–N test tags.
- **Persona tag** — closed-enum lookup against `<discipline>_persona_v1`. Same mechanism.

The test/persona taggers are themselves calibrated via Cyto-as-oracle: run them over Cyto chunks (back-derived test/persona via citing Cyto stories), tune until ≥ 95% accuracy.

Result: chunks become facet-queryable along three axes (theme, test, persona) instead of one.

### 5.2 Phase 1 — Pre-flight (Theme Discovery runs with quorum; no Test/Persona Discovery)

**No Test Discovery, no Persona Discovery.** The catalogs are static SME-supplied YAML, committed once.

**Theme Discovery still runs** for new disciplines whose theme catalog isn't pre-supplied. Algorithm unchanged from v3.2 (4-pass: classify → cluster → admit → re-tag). Pass 3 is replaced by the multi-agent quorum (§4.1). Discarded themes (parent-catalog themes that don't apply) get a separate quorum prompt: "should this prior theme survive in the new catalog?" — 4-of-5 to discard.

For Micro POC specifically: theme catalog is `cyto_v1` reused wholesale; no Theme Discovery needed.

### 5.3 Phase 2 — Per-SOP run

**Intake scope-check (new):**
- SOP arrives → run the test tagger over the SOP.
- Compute the fraction of SOP test-references that resolve to entries in the test catalog.
- If fraction < 80% → reject at intake with reason "out of scope: too many out-of-catalog test references."
- If fraction ≥ 80% → SOP passes intake. Out-of-catalog test references in chunks are tagged `test: out_of_scope` and excluded from Story Extractor input (the agent only sees in-scope content).

**Epic Extractor (conditioned mode):**
- Same conditioning algorithm.
- Pass 3 (ratification of novel epics) replaced by quorum (§4.1). Same N=5, M=4 defaults.
- Inherited epics with match_score ≥ τ_match still bypass quorum (auto-inherited).

**Story Extractor:**
- Receives SOP + retrieved chunks + dynamic exemplars + **test catalog + persona catalog inlined as system context**.
- Each emitted story carries:
  - `tests[]` — selected from the closed enum.
  - `persona` — selected from the closed enum (required for capability/stage-split, optional for config-instance/cleanup).
- Exemplar retrieval becomes (test, persona, shape)-targeted via Cyto-as-oracle (§4.2).

**Validator (gate 1):**
- Closed-enum checks for `tests[]` and `persona` — hard reject on enum violation, no revise loop.
- Shape-specific sub-rubric (calibrated via Cyto holdout, §4.2) runs as before.
- 2 revision attempts allowed for shape/AC issues only.
- After 2 failed revisions → **auto-park** (§4.3). No SME escalation.

### 5.4 Phase 3 — Batch / synthesis

**Cross-SOP Synthesis:**
- Clustering tuple is **(test, persona, shape, behavior)** — three closed-enum facts plus a behavioral similarity signal.
- Cluster precision sharply higher than v3.2's behavior-only clustering.
- ≥ 2 distinct SOPs threshold (D11) unchanged.
- Capability stories' parameter lists are cleaner: dimensions constant across cluster members (test, persona, shape) become fixed labels; varying dimensions become parameters.

**Validator (gate 2):**
- Same extended rubric.
- Same auto-park behavior.
- No human-in-the-loop ratification of synthesized capability stories.

### 5.5 Phase 4 — Outputs

**Output A — Jira tree:**
- Every story carries `tests[]` and `persona`.
- Auto-parked stories are NOT in Output A in strict mode; they're in a separate `parked/` queue.

**Output B — Per-culture YAML profile:**
- Schema becomes deterministic because tests are static. Sections are pre-declared per test:

```yaml
cultures/blood.yaml:
  pre_analytic:
    specimen_receipt: { ... }
  tests:
    gram_stain:               { params, units, citations, persona_owner }
    blood_culture_incubation: { ... }
    maldi_identification:     { ... }
    ast:                      { ... }
  post_analytic:
    result_release: { ... }
```

`persona_owner` per section makes handoff explicit.

**Output C — Reference catalogs and audit:**
- Theme catalog (versioned, conditioned-discovery output).
- Epic catalog (versioned, conditioned-discovery output).
- ANALOGY map (theme_links + epic_links computed; test_links + persona_links static, SME-supplied).
- **Static test catalog** (`<discipline>_test_v1`).
- **Static persona catalog** (`<discipline>_persona_v1`).
- **Quorum decision log** (new) — per-novelty audit trail showing N agents' votes.
- **Parked stories queue** (new) — failed-checks list per parked story.
- **Drift report** (new, auto-generated) — see §4.4.

### 5.6 Phase 5 — Drift & feedback

**G0/E0 alarms** (5% threshold, rolling window) → auto-rerun Discovery with τ_match -0.05. New candidates go through quorum.

**Floor:** τ_match = 0.50. Below this, drift report flags the discipline; auto-rerun stops; manual re-curation needed.

**Drift report cadence:** weekly batch by default; immediate emit on any alarm trip.

**Reviewer:** anyone. Report is informational, not blocking.

---

## 6. Schema deltas

### 6.1 Story schema (v3.2 → v3.4)

```diff
{
  id, epic_id,
  shape ∈ {capability, workflow-stage-split, configuration-instance, cleanup},
  title, description,
  acceptance_criteria[],
+ tests[],                      // closed enum from <discipline>_test_v<N>
+ persona: string | null,       // closed enum from <discipline>_persona_v<N>;
+                               // null only for cleanup/config-instance shapes
  source_citations[],
  dependencies[],
  cross_links[],
  technical_hints?,
  estimated_complexity ∈ {S,M,L},
  edge_cases_handled[],
  status,
  source_chunks[],
  theme_catalog_version: string,
+ quality ∈ {passed, parked},   // parked means Validator failed twice
+ parked_reason?: string[],     // failed-checks list, populated only when quality=parked
}
```

### 6.2 Catalog schemas — `admission_decision` replaces `sme_confirmed`

```diff
novel_themes:
  - id: H1
    name: Tissue Processing
    cluster_evidence: { ... }
-   sme_confirmed: true
-   sme_notes: "..."
+   admission_decision:
+     mechanism: quorum
+     n_agents: 5
+     m_threshold: 4
+     votes:
+       - { agent_id: 1, vote: admit,   reasoning_excerpt: "..." }
+       - { agent_id: 2, vote: admit,   reasoning_excerpt: "..." }
+       - { agent_id: 3, vote: admit,   reasoning_excerpt: "..." }
+       - { agent_id: 4, vote: admit,   reasoning_excerpt: "..." }
+       - { agent_id: 5, vote: fold-in, fold_target: G2, reasoning_excerpt: "..." }
+     description_convergence_score: 0.87
+     decision: admit
```

Same shape applies to `novel_epics`. Inherited entries with `auto_inherited: true` skip the admission_decision block.

### 6.3 ANALOGY map — static for tests/personas; computed for themes/epics

```yaml
analogy_map:
  theme_links:   [ ... ]   # computed by Theme Discovery + quorum
  epic_links:    [ ... ]   # computed by Epic Extractor + quorum
  test_links:    [ ... ]   # static, supplied at project start, no runtime mutation
  persona_links: [ ... ]   # static, supplied at project start, no runtime mutation
```

### 6.4 New artifacts

**Quorum decision log** (`audit/quorum_decisions_<timestamp>.yaml`):

```yaml
run_id: 2026-05-15T10:00:00Z
discovery_type: epic
candidates:
  - candidate_id: ce_001
    proposed_name: "Antibiotic Susceptibility Testing"
    cluster_evidence: { n_drafts: 4, sample_drafts: [...] }
    quorum_result:
      votes: [admit, admit, admit, admit, admit]
      description_convergence: 0.91
      decision: admit
      decided_at: 2026-05-15T10:02:13Z
  - candidate_id: ce_002
    proposed_name: "Reflexive Reporting"
    cluster_evidence: { n_drafts: 2, ... }
    quorum_result:
      votes: [reject, fold-in, fold-in, reject, fold-in]
      decision: fold-in
      fold_target: EPIC-CYTO-008
```

**Parked stories queue** (`parked/<run_id>/<story_id>.yaml`):

```yaml
story_id: STORY-MICRO-DRAFT-042
attempt_count: 3
final_state: parked
last_attempt:
  generated_content: { title, description, ac, ... }
  failed_checks:
    - "AC #2 uses 'appropriate threshold' (ambiguous quantifier)"
    - "AC #4 cites SOP-MICRO-014:lines-89-97 but excerpt does not contain a threshold"
  validator_verdict: "Cannot pass capability-shape rubric without concrete threshold value"
sop_excerpt_id: SOP-MICRO-014:lines-89-97
created_at: 2026-05-15T11:32:00Z
```

**Drift report** (`reports/drift_<week>.md`): markdown summary as described in §4.4. Generated weekly + on alarm trip.

---

## 7. Pipeline diagram (v3.4 delta vs v3.2)

```
┌────────────────────────────────────────────────────────────────────────┐
│  STATIC INPUTS (received at project start; no discovery)               │
│   <discipline>_test_v1.yaml ──┐                                        │
│                               ├──► loaded into agent system context    │
│   <discipline>_persona_v1.yaml┘                                        │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PRE-FLIGHT (only when theme catalog needs discovery)                  │
│   Sample SOPs ──► Theme Discovery ──► QUORUM ──► theme catalog         │
│   prior catalog ─────────────────────────────────                      │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PER-SOP RUN                                                           │
│   SOP ──► Intake scope-check (≥80% in-scope tests?) ──► reject if not  │
│              │                                                         │
│              ▼                                                         │
│   Chunk enrichment: theme + test + persona tagging                     │
│              │                                                         │
│              ▼                                                         │
│   Epic Extractor (conditioned) ──► QUORUM on novelty ──► epic catalog  │
│              │                                                         │
│              ▼                                                         │
│   Story Extractor                                                      │
│     - SOP + chunks + (test,persona,shape)-targeted exemplars           │
│     - emits stories with tests[] and persona from closed enums         │
│              │                                                         │
│              ▼                                                         │
│   Validator (gate 1)                                                   │
│     - closed-enum checks (hard reject on enum violation)               │
│     - shape rubric, 2 revisions                                        │
│     - failed-after-2 → AUTO-PARK (no SME escalation)                   │
│              │                                                         │
│              ▼ (batch boundary)                                        │
│   Cross-SOP Synthesis                                                  │
│     - cluster on (test, persona, shape, behavior)                      │
│              │                                                         │
│              ▼                                                         │
│   Validator (gate 2) — same auto-park rule                             │
│              │                                                         │
│              ▼                                                         │
│   Dependency Resolver                                                  │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  OUTPUTS                                                               │
│   A: Jira tree (passed stories only)                                   │
│   B: per-culture YAML profiles (test-partitioned schema)               │
│   C: catalogs + ANALOGY map + parked queue + quorum log + drift report │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  CONTINUOUS                                                            │
│   G0/E0 alarm (5% rolling) → auto-rerun Discovery with τ_match −0.05   │
│   Drift report (weekly): parked counts, alarm trips, quorum decisions  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 8. I/O trace — Histology bootstrap with no SME (revised from V3_2_SPEC.md §7)

Same Histo example as V3_2_SPEC.md §7, with SME ratification replaced by quorum.

**Inputs:** prior_catalog `cyto_v1` (G1–G8); 20 sample Histology SOPs, ~600 chunks; τ_match=0.65, ε_novelty=3; N=5, M=4.

**Pass 1 — Classify against G1–G8:** unchanged. 7/8 themes inherit; G7 sparse (12 chunks); residual 140.

**Pass 2 — Cluster the residual:** unchanged. 4 clusters above ε_novelty=3 (sizes 38/32/25/23) plus 22 noise chunks → G0.

**Pass 3 — Multi-agent quorum on each candidate:**

| Candidate | Quorum votes | Description convergence | Decision |
|---|---|---|---|
| H1 Tissue Processing (38) | admit/admit/admit/admit/admit | 0.91 | **admit** |
| H2 Staining (32)          | admit/admit/admit/admit/admit | 0.94 | **admit** |
| H3 Block & Slide Archive (25) | admit/admit/admit/admit/fold→G6 | 0.86 | **admit** (4-of-5) |
| H4 Frozen Section (23)    | admit/admit/fold→G2/admit/reject | 0.78 | **park to G0** (3-of-5; convergence below 0.80) |

**Discard quorum on G7:** "Should G7 Instrumentation survive in `histo_v1`?" → discard/discard/discard/discard/keep → **discard** (4-of-5). ANALOGY map records `G7 → H1, partial`.

**Pass 4 — re-tag the 12 G7 chunks** against the post-discard taxonomy. Most land in H1; 2 fall to G0.

**Output: `histo_v1` theme config**
- inherited_themes: G1, G2, G3, G4, G5, G6, G8 (7)
- novel_themes: H1, H2, H3 (3 — H4 didn't clear quorum)
- discarded_themes: G7
- unclassified_bucket: 22 (Pass 2 noise) + 2 (Pass 4 fallout) + 23 (H4) = 47 chunks ≈ 7.8% of total

**G0 alarm trips** (7.8% > 5%):
- Auto-rerun Theme Discovery with τ_match=0.60.
- H4's 23 chunks come back in residual + a few re-classified prior chunks.
- Quorum re-evaluates. If H4 still doesn't clear, drift report flags it; if it clears (4-of-5 with revised description), it admits.

**Net result:** `histo_v1` ends with 10 active themes (7 inherited + 3 admitted), one candidate (H4) flagged in the drift report for non-SME human review. Pipeline does not block on H4.

---

## 9. Decisions (proposed for the log)

These would be added to `DECISIONS.md` after spec review. Companion file `V3_4_DECISIONS_LOG.md` provides them in lift-and-paste form.

### D20 — Static catalogs for tests and personas; no discovery on either dimension

**Decision:** Test catalog (`<discipline>_test_v<N>`) and persona catalog (`<discipline>_persona_v<N>`) are static SME-supplied YAML inputs, not discovered artifacts. Closed enums fed to agents and Validator. Story schema gains `tests[]` and `persona` fields drawn from these enums. No conditioned discovery, no τ_match/ε_novelty knobs, no novelty alarms for these dimensions. ANALOGY map's `test_links` and `persona_links` are also static one-time inputs.

**Rationale:** The discipline's tests and personas are stable organizational facts — they don't drift over POC timeframes, and they're enumerable upfront. Treating them as discoverable adds machinery without payoff. Closed enums sharpen Validator checks (hard rejects on enum violations) and tighten cross-SOP synthesis clustering (test + persona become explicit grouping axes).

**Alternatives considered:** Conditioned discovery for tests + personas (rejected — over-engineered). Free-text fields (rejected — loses Validator leverage).

### D21 — Multi-agent quorum replaces SME ratification at every novelty admission gate

**Decision:** Theme Discovery Pass 3 and Epic Discovery Pass 3 invoke a multi-agent quorum (default N=5, M=4) instead of an SME reviewer. Independence enforced by prompt-frame diversity. Admission requires M-of-N agreement plus description convergence ≥ 0.8 cosine on the synthesized one-liner. Disagreement → cluster goes to G0/E0 (deferred, not admitted).

**Rationale:** Discovery runs rarely, so 5× LLM cost is acceptable. Independent prompts catch different failure modes; M-of-N filters single-agent overconfidence. Quorum decision log is auditable; later human review can re-assess admissions without re-running the pipeline.

**Tuning knobs:** N (panel size), M (threshold), description-convergence threshold. Defaults are guesses; first-run telemetry calibrates.

**Alternatives considered:** Single-agent classifier (rejected — single point of failure). LLM-as-judge with one large agent (rejected — same).

### D22 — Auto-park replaces SME escalation at the Validator gate

**Decision:** After 2 failed Validator revisions, stories transition to `quality: parked` and land in a separate `parked/` queue with their failed-checks list visible. They do not reach Output A (strict mode default). Pipeline does not block. Periodic non-SME review (architect / PM) can triage parked queue volume.

**Rationale:** With no SME, escalation has no human target. Auto-park preserves precision (parked stories don't pollute Jira) at the cost of recall (some good stories may be parked). Strict-mode default reflects POC priority of "ship clean output" over "ship comprehensive output."

**Alternatives considered:** Permissive mode (kept available as a switchable mode for environments where recall matters more). Auto-revise to N>2 attempts (rejected — diminishing returns).

### D23 — Cyto-as-oracle for exemplar bootstrap and rubric calibration

**Decision:** Cyto Jira's existing SME-validated stories are the exemplar oracle. Filter by quality signals (non-empty AC, linked test cases, no draft tags, source citations resolve, status not new/backlog). Trace to source SOP excerpts via `source_citations[]` (or retrieval if missing). Use 20% holdout per shape to calibrate Validator rubrics; tune until ≥ 95% acceptance on the holdout.

**Rationale:** Cyto Jira has been through Cyto's own SME review; the surviving stories are by definition gold-standard. Eliminates active SME pairing on exemplar curation. Holdout-based calibration ports the Cyto quality bar to the automated Validator without per-story labels.

**Caveat:** depends on Cyto Jira accessibility — existing OPEN_QUESTIONS item that becomes load-bearing under v3.4.

### D24 — G0/E0 alarm: auto-rerun with τ_match −0.05; floor at 0.50; drift report

**Decision:** When G0 (theme) or E0 (epic) bucket exceeds 5% rolling-window volume, automatically re-run the appropriate Discovery with `τ_match` lowered by 0.05. Repeated trips compound the lowering, with a floor of `τ_match = 0.50`. Below the floor, auto-rerun stops and the drift report flags the discipline for manual re-curation. New candidates from the re-run go through standard quorum.

**Rationale:** v3.2 said SME re-runs Discovery on alarm. With no SME, the system must self-respond. Threshold-tightening is the natural response (the bucket grew because matches were too strict). Bounded tightening prevents drift compounding indefinitely.

### D25 — Intake scope-check: SOPs with <80% in-scope test references rejected at intake

**Decision:** SOP arrival triggers a test-tag scan against the closed test catalog. SOPs with <80% of their test references resolving to in-catalog entries are rejected at intake with reason "out of scope." Accepted SOPs may still have isolated out-of-scope test references; these chunks are tagged `test: out_of_scope` and excluded from Story Extractor input.

**Rationale:** Without an SME to confirm scope, intake must enforce it automatically. The 80% threshold balances false-rejection (legitimately in-scope SOPs that mention adjacent tests) against false-acceptance (out-of-scope SOPs dragging novel content into the pipeline). Threshold is tunable.

---

## 10. Migration from v3.2

For Micro POC, v3.4 layers on top of v3.2 additively. Migration steps:

1. **Receive `<discipline>_test_v1.yaml` and `<discipline>_persona_v1.yaml`** from architecture team. Commit as static reference inputs alongside the static `test_links` and `persona_links` of the ANALOGY map.
2. **Build the multi-agent quorum harness** for Theme Discovery + Epic Extractor (5 independent prompt frames; cosine on description convergence). Reuse the same harness for both — it's a generic novelty-admission service.
3. **Snapshot Cyto Jira** as the exemplar oracle. Filter for quality signals; tag each surviving story with its (test, persona, shape) tuple. Hold out 20% per shape for rubric calibration.
4. **Calibrate Validator sub-rubrics** against Cyto holdout until ≥ 95% acceptance per shape.
5. **Build chunk-enrichment additions:** test tagger and persona tagger as closed-enum classifiers. Calibrate against Cyto chunks (back-derived test/persona via citing Cyto stories).
6. **Implement intake scope-check** at the ingestion endpoint. Reject below-threshold SOPs with structured reason.
7. **Implement auto-park queue, quorum decision log, and drift report** as new output artifacts.
8. **Run conditioned Epic Extractor with quorum** over the 3 in-scope Micro SOPs. Generate `micro_epic_v1` with quorum decision log.
9. **Run main pipeline with extended Validator** (closed-enum checks + auto-park).
10. **Generate Outputs A/B/C plus drift report.**

For Micro POC, theme catalog stays `cyto_v1` (no Theme Discovery needed); only the epic catalog forks.

---

## 11. Open questions (v3.4-specific)

These extend `OPEN_QUESTIONS.md`.

- **Quorum size and threshold defaults.** N=5, M=4 are guesses. Need first-run telemetry. Too high M → G0 explodes; too low → catalog pollutes.
- **Quorum agent diversity.** Same model with different prompts vs. mixture of models? Same-model panels may exhibit correlated errors. Lean: same model (Haiku-class) with 5 prompts for POC; revisit if correlated errors appear in the audit log.
- **Description convergence threshold.** 0.8 cosine is a guess. First-run real values determine if too strict (admissions blocked on cosmetic phrasing) or too loose (semantic disagreement getting through).
- **Auto-park rate budget.** What % parked is acceptable? <5% rubric well-calibrated; 5–15% suggests rubric tightness; >15% suggests miscalibration or out-of-scope SOPs.
- **Cyto Jira accessibility.** Existing OPEN_QUESTIONS item now load-bearing. Without sanitized Cyto Jira outside the office network, the oracle has no source. Possible alternative: synthetic exemplars from Cyto SOPs constructed by an upfront LLM pass (lower quality, unblocks development).
- **Out-of-scope chunk handling within accepted SOPs.** Currently excluded from Story Extractor input. Alternative: include but mark, let agent decide. Lean: exclude (cleaner separation).

---

## 12. What v3.4 explicitly does NOT change

- The 5-agent main pipeline (Epic Extractor → Story Extractor → Validator → Cross-SOP Synthesis → Validator → Dependency Resolver). Theme Discovery remains the pre-flight 6th agent; no new agents added.
- The four story shapes and the type-aware Validator approach.
- Cross-SOP synthesis with the ≥ 2 distinct SOPs threshold (D11). Clustering tuple is sharper but the recurrence rule is unchanged.
- Cyto's role as a teaching corpus (D5).
- The hybrid retrieval substrate (BM25 + dense + RRF + rerank), the multi-slot retrieval, and the τ=0.7 / θ=0.5 query thresholds (these are query-time thresholds, distinct from the discovery-time τ_match).
- Conditioned Discovery algorithm shape (4-pass: classify → cluster → admit → re-tag). Pass 3 mechanism changes; the algorithm shape doesn't.
- The per-culture YAML configuration profile (D12) as an artifact. Schema becomes deterministic but the artifact's role is unchanged.
- Tasks remain out-of-scope (D14).
- Three output streams (A/B/C). Stream C gains static test/persona catalogs, quorum decision log, parked queue, and drift report; the artifact taxonomy is otherwise unchanged.

The v3.4 changes are concentrated at the **gates**: where humans were assumed to be in the loop, automated mechanisms now stand. The interior of the pipeline (algorithms, schema core fields, substrate) is unchanged.

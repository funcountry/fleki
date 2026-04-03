---
title: "Fleki - Temporal Knowledge Freshness And Operator Clarity - Architecture Plan"
date: 2026-04-03
status: complete
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: architectural_change
related:
  - /Users/agents/workspace/fleki/README.md
  - /Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md
  - /Users/agents/workspace/fleki/docs/CENTRALIZED_KNOWLEDGE_INSTALL_AND_ROOT_PLAN_2026-04-03.md
  - /Users/agents/workspace/fleki/src/knowledge_graph/models.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/repository.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/cli.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/validation.py
  - /Users/agents/workspace/fleki/skills/knowledge/SKILL.md
  - /Users/agents/workspace/fleki/tests/test_search_trace_status.py
---

# TL;DR

- **Outcome:** Keep Fleki LLM-first, but make time and freshness explicit enough on disk that recent authoritative truth does not compete equally with old ephemeral support, and make the operator-facing `install`, `save`, `search`, `trace`, and `status` surfaces understandable without reading source code.
- **Problem:** The current graph writes operational timestamps, but retrieval and status do not use them as freshness signals, stale or superseded knowledge has no clean public retirement path, and real testing exposed a wider operator-confusion stack: persistent shared state masquerading as a fresh install, a hidden `save` schema, hidden enums and topic-path rules, unclear `source_kind` vocabulary, install/package/import naming confusion, underspecified PDF/runtime expectations, search false positives, weak recent-status visibility, and no first-class recent-artifact discovery path.
- **Approach:** Promote the existing source timestamp input into a real persisted fact, add a minimal freshness lifecycle and supersession story to semantic pages, use those facts as ranking and visibility hints instead of a deterministic decay formula, and make the operator contract explicit enough that the testing-exposed issues are solved at the CLI/doc layer instead of being left buried in code.
- **Plan:** First lock the temporal vocabulary and operator contract, including the specific testing-exposed failure modes. Then thread temporal facts through source records, provenance notes, and topic metadata. Then teach `search`, `trace`, `status`, and `rebuild` to use freshness and cleanup state. Then finish the repo-owned docs, install wording, and verification.
- **Non-negotiables:**
  - No deterministic decay engine, background aging daemon, or hidden retrieval backend.
  - Authority and freshness are separate axes. Recency may sharpen ranking, but it must not silently flatten stronger doctrine.
  - Time facts must be inspectable on disk. The agent may reason about staleness, but the repository must persist the facts that justified that reasoning.
  - Fully superseded or explicitly stale knowledge must have a clean shared-contract path to be rehomed, retired, or deleted. Do not keep dead pages live "just in case."
  - A fresh install of the CLI or skill is not the same thing as an empty graph. Persistent root semantics must be stated plainly.
  - The `knowledge save` contract, enum vocabulary, topic-path rules, `source_kind` expectations, install/root semantics, naming, and PDF/runtime expectations must be visible without code spelunking.

<!-- arch_skill:block:implementation_audit:start -->
# Implementation Audit (authoritative)
Date: 2026-04-03
Verdict (code): COMPLETE
Manual QA: complete (non-blocking)

## Code blockers (why code is not done)
- None.

## Reopened phases (false-complete fixes)
- None.

## Missing items (code gaps; evidence-anchored; no tables)
- None.

## Non-blocking follow-ups (manual QA / screenshots / human verification)
- None.
<!-- arch_skill:block:implementation_audit:end -->

<!-- arch_skill:block:planning_passes:start -->
<!--
arch_skill:planning_passes
deep_dive_pass_1: done 2026-04-03
external_research_grounding: done 2026-04-03
deep_dive_pass_2: done 2026-04-03
recommended_flow: deep dive -> external research grounding -> deep dive again -> phase plan -> implement
note: This is a warn-first checklist only. It should not hard-block execution.
-->
<!-- arch_skill:block:planning_passes:end -->

# 0) Holistic North Star

## 0.1 The claim (falsifiable)
> If Fleki preserves a small set of explicit temporal facts across source records, provenance notes, and semantic pages, and if `save`, `search`, `trace`, `status`, and `rebuild` use those facts as agent-readable hints plus ranking and cleanup rules instead of a formulaic decay engine, then recent authoritative truth will stop competing equally with old ephemeral support, fully superseded knowledge can be retired cleanly, search/status will explain currentness instead of surfacing stale noise, and first-time operators will be able to understand the persistent-root, install, naming, `save`, and PDF/runtime contract without reading repository code.

## 0.2 In scope
- UX surfaces (what users will see change):
  - Search results that can prefer current, well-supported knowledge over stale or superseded historical pages when both match.
  - Trace output that makes source time, ingest time, and supersession state visible enough to explain why a result ranked where it did.
  - Status output that shows recent touches and persistent-root semantics instead of implying that "hot topics" are the same thing as recent truth.
  - A visible operator explanation of what `knowledge save` expects, including valid payload shape, enum vocabulary, topic-path rules, and what "fresh install" means when a shared graph already exists.
  - A repo-owned story for recent-artifact discovery that does not require manual date-globbing or code inspection.
- Technical scope (what code/docs/packaging will change):
  - A minimal temporal metadata contract for sources, provenance, and semantic pages.
  - A small page-lifecycle contract for current, historical, stale, and superseded knowledge.
  - Search, trace, status, and rebuild behavior that uses persisted freshness facts and supersession state.
  - CLI help and docs that surface the real `save` and install contract directly.
  - Repo-owned clarification of package name, CLI name, import name, centralized data root, and PDF/runtime expectations.
  - Explicit fixes for the testing-exposed confusion stack:
    - shared persistent graph state versus "fresh install" expectations
    - hidden `save` JSON shape
    - hidden enum values and forbidden topic roots
    - unclear canonical `source_kind` vocabulary
    - install/layout/package/import naming confusion
    - underspecified PDF/runtime path and dependency expectations
    - search false positives driven by noisy path/provenance overlap
    - status surfaces that show hot-topic frequency instead of recent truth
    - no first-class recent-artifact discovery path

## 0.3 Out of scope
- UX surfaces (what users must NOT see change):
  - A new product surface beyond the existing `knowledge save/search/trace/rebuild/status` verbs.
  - A full viewer or browse-model redesign.
  - A requirement for operators to memorize one more hidden helper or sidecar tool just to understand graph freshness.
- Technical scope (explicit exclusions):
  - A deterministic age-score pipeline, embeddings service, cron-driven garbage collector, or other hidden freshness subsystem.
  - Automatic deletion based on age alone.
  - Remote sync, multi-host coordination, or distributed retention policy in this pass.
  - A speculative package rebrand if plain naming and contract docs solve the operator problem.
  - Hand-editing graph files outside the shared repository contract.

## 0.4 Definition of done (acceptance evidence)
- A saved source can preserve both "when Fleki captured it" and "when the source was true or observed" when that second fact is known.
- Semantic pages can express enough freshness state that `search` and `trace` no longer treat an old ephemeral support page as equally current by default.
- Fully superseded or explicitly stale pages can be retired through the shared contract, not by ad hoc file deletion.
- `knowledge status --json --no-receipt` reports the resolved persistent root and recent-touch/freshness signals plainly enough for smoke validation.
- The `knowledge save` contract, enum vocabulary, topic-path rules, `source_kind` expectations, and persistent-root/install semantics are visible from repo-owned docs and CLI help without reading `authority.py` or `validation.py`.
- Search and status resolve the concrete testing complaints:
  - obvious current topics outrank stale provenance/path noise
  - recent touches are visible directly
  - the shared persistent graph is obvious from the operator surface
  - recent-artifact discovery no longer depends on manual date-globbing
- Smallest credible evidence for this plan:
  - targeted save/search/trace/status/rebuild tests for temporal metadata and supersession behavior
  - one older-source plus newer-source integration scenario that proves ranking and trace behavior
  - one operator smoke that confirms install/root semantics and the visible `save` contract

## 0.5 Key invariants (fix immediately if violated)
- The system stays LLM-led. The repository stores explicit freshness facts and outcomes; it does not replace agent judgment with a hidden formula.
- `captured_at` and source-observed time are different facts and must not be collapsed into one timestamp.
- Authority posture and freshness state are different facts and must not be collapsed into one field.
- Search may down-rank stale or superseded material, but it must not silently hide history when the operator is tracing or explicitly asking for historical support.
- Live doctrine and raw runtime truth may still outrank newer but weaker support. Recency sharpens ranking; it does not erase authority.
- Supersession must be explicit and inspectable. A page is not "gone" just because something newer exists somewhere else.
- Unknown temporal metadata must stay visibly unknown. Do not silently treat old untouched content as current truth merely because it exists.
- Fresh install semantics must be explicit: a newly installed binary/skill may still point at an already populated shared graph.
- Save/help semantics must be explicit enough that operators do not need to inspect Python code to discover schema, enums, topic-path rules, or accepted vocabulary.
- Secret-pointer and pointer-only handling must remain intact. Temporal metadata must not force copying sensitive source contents.

# 1) Key Design Considerations (what matters most)

## 1.1 Priorities (ranked)
1. Stop equally weighting recent authoritative truth and old ephemeral support.
2. Keep freshness reasoning LLM-led and artifact-supported, not formula-led.
3. Make freshness, supersession, and persistent-root semantics visible on disk and in the CLI.
4. Remove operator reverse-engineering from the `save` and install story.
5. Preserve the existing five-verb interface and the current markdown-first storage model.

## 1.2 Constraints
- The current implementation already has useful time facts:
  - `SourceBinding.timestamp` exists in `models.py`.
  - source records persist `captured_at`.
  - provenance notes persist `created_at`.
  - topic pages persist `last_updated_at`, `last_reorganized_at`, and `supersedes`.
- Those facts are currently scattered and underused:
  - `_persist_source_records()` writes `captured_at` but does not persist the binding timestamp.
  - `_score_page()` ranks by token overlap plus authority posture, not freshness.
  - `status()` reports `hot_topics` from receipt frequency, not recent touches.
- The graph is now centralized under `~/.fleki/knowledge` by default, so operator language must account for persistent machine state rather than repo-local emptiness.
- The user explicitly wants a minimal solution that leans on model judgment, not a deterministic decay subsystem.
- Existing graph and CLI users need one clear contract, not a split between code truth and docs truth.

## 1.3 Architectural principles (rules we will enforce)
- Organize by meaning first. Add time-aware hints to semantic knowledge, not a source-family-first retention layer.
- Persist explicit temporal facts, not derived mythology.
- Let the agent decide whether something is evergreen, time-bound, stale, or fully superseded. Let the repository enforce only explicit persisted outcomes and fail-loud boundaries.
- Prefer explicit cleanup through `rebuild` or an equivalent shared-contract path over keeping dead pages live.
- Make repo-owned docs and help text as authoritative as validation code. Operators should not have to inspect Python files to author a valid payload.
- Keep storage evolution additive and inspectable on disk.

## 1.4 Known tradeoffs (explicit)
- Page-level freshness fields are simpler, but may be too blunt if one page mixes evergreen doctrine and time-bound observations.
- A visible cleanup contract is slightly more surface area, but it is better than hidden manual file deletion.
- Clarifying naming and install semantics in docs is cheaper than renaming the package/import surface, but deep-dive should verify whether docs-only clarity is enough.
- Ranking hints are safer than hard filters, but they require clear trace/status surfaces so operators understand why a result moved.

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- This repo owns the `knowledge` skill, the bundled Python runtime, and the markdown/json knowledge graph format.
- Production installs resolve the mutable graph to `~/.fleki/knowledge`; tests inject temp roots through `resolve_knowledge_layout(...)`.
- `knowledge save` persists:
  - raw or pointer source records under `sources/**`
  - provenance notes under `provenance/**`
  - semantic topic pages under `topics/**`
  - receipts under `receipts/**`
- Search currently loads topic pages and ranks them with `_score_page()` using query overlap plus authority posture, then sorts by score, authority rank, and path.
- Status currently aggregates receipts and manifests, then reports counts plus `hot_topics` based on touched-topic frequency across save receipts.
- Rebuild can currently rename pages and append `supersedes`, but it does not yet model page retirement or deletion.
- The `knowledge save` help text exposes file-path flags for `--bindings` and `--decision`, but not the schema, enum vocabulary, or topic-path rules themselves.

## 2.2 What’s broken / missing (concrete)
- There is no persisted distinction between "when Fleki captured this source" and "when this source was true or observed" in the artifacts that search and trace actually use.
- Retrieval has no explicit notion of freshness or staleness, so old ephemeral information can remain competitively ranked as long as it matches textually.
- Topic pages have `supersedes`, but there is no clean shared-contract path to retire or delete pages that are fully superseded or plainly stale.
- Search trust is weaker than it should be because path/body token overlap can beat topical meaning when freshness and supersession are absent.
- Status is weak for smoke validation because `hot_topics` is not the same thing as recently touched or currently supported.
- Operators have to reverse-engineer the `save` contract, enum values, topic-path rules, install layout, package/import naming, and PDF/runtime assumptions from code and environment behavior.
- Markdown/text sources currently fall into `sources/other/`, which may be acceptable, but the current docs do not explain whether that is intentional taxonomy or accidental bucket naming.

## 2.3 Constraints implied by the problem
- The smallest viable fix must work with the current markdown/json artifact model rather than replacing it with a new backend.
- Temporal data should be additive and use the current source/provenance/topic layering.
- Freshness ranking must stay authority-aware and must not turn newer weak evidence into automatic doctrine.
- Cleanup must be explicit and fail loud. Silent retention and silent deletion are both bad outcomes here.
- Operator clarity is part of the product surface, not a separate documentation chore.

<!-- arch_skill:block:research_grounding:start -->
# 3) Research Grounding (external + internal “ground truth”)

## 3.1 External anchors (papers, systems, prior art)
- Elasticsearch Query DSL `function_score` and decay functions
  - Adopt: keep topical match primary, then add freshness and authority as later scoring inputs.
  - Reject: do not introduce a separate search backend or a formal decay-function engine. Reuse the ordering principle only.
- Algolia `customRanking` and re-ranking guidance
  - Adopt: freshness should be a secondary ranking hint layered on top of semantic match, not a replacement for it.
  - Reject: do not add analytics pipelines, event-driven reranking, or AI retrieval machinery for this pass.
- RFC Editor `Updates` / `Obsoletes` conventions
  - Adopt: distinguish clearly between knowledge that supplements current truth and knowledge that replaces it, and keep supersession discoverable in both directions.
  - Reject: do not silently rewrite or silently bury older pages.
- GitHub Docs single-source versioning guidance
  - Adopt: prefer one canonical page lineage plus lifecycle metadata over cloning many near-identical historical pages.
  - Reject: do not turn freshness into a copied-per-version tree unless a later product-doc requirement proves it necessary.
- AWS CLI `--generate-cli-skeleton` pattern
  - Adopt: ship or generate a valid `knowledge save` skeleton/example and point concise help text to it.
  - Reject: do not dump the full JSON schema inline into `--help`.

## 3.2 Internal ground truth (code as spec)
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` plus `/Users/agents/workspace/fleki/tests/test_layout.py`
    - These files define the real persistent-root contract: default config/data/state live under `~/.fleki`, install-manifest values take precedence when present, and legacy roots migrate into the centralized layout. This is the authoritative answer to the "fresh install" versus "shared persistent graph" confusion.
  - `/Users/agents/workspace/fleki/pyproject.toml` plus `/Users/agents/workspace/fleki/tests/test_skill_package.py`
    - These files define the current naming split: distribution name `fleki-knowledge-graph`, Python module `knowledge_graph`, console script `knowledge`, and skill key `fleki/knowledge`. This is the real import/package/CLI surface that docs must explain plainly.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`
    - `_build_parser()` is the actual operator surface. `save` only exposes `--bindings` and `--decision` as file paths, even though `_binding_from_dict()` already accepts extra input keys such as `timestamp` and `notes`. `_command_status()` in plain-text mode only exposes root/count fields and does not surface recent items.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py` plus `/Users/agents/workspace/fleki/src/knowledge_graph/authority.py` plus `/Users/agents/workspace/fleki/tests/test_contracts.py`
    - These files define the real save contract: required top-level keys, per-object required keys, render keys the caller must not supply, forbidden source-family topic roots, and the exact enum vocab for authority, reading mode, page kind, topic action, knowledge-unit kind, conflict handling, asset actions, and recommended-next-step actions. Today many of these rules are only visible after validation failure or code inspection.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`
    - `SourceBinding.timestamp` already exists as the smallest natural input for source-observed time. `RebuildPageUpdate` currently only supports `new_current_path`, `add_supersedes`, and `note`, which means the repo has no explicit retire/archive/delete lifecycle model yet.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `_persist_source_records()` stores `captured_at` and source metadata, but it does not persist `SourceBinding.timestamp`.
    - `_persist_provenance_notes()` already writes per-source metadata maps such as `source_ids`, `source_record_paths`, `source_reading_modes`, and `created_at`, which makes it the natural trace boundary for source-time facts.
    - `_apply_topic_actions()` already writes page metadata with `knowledge_id`, `current_path`, `aliases`, `section_support`, `authority_posture`, `last_updated_at`, and `supersedes`, but no freshness rollup or lifecycle state.
    - `search()` and `_score_page()` define the live ranking behavior: lexical match over path, aliases, title, and full body, then sort by score, `authority_rank(...)`, and path. There is no freshness input, supersession penalty, or stale-state handling in ranking.
    - `trace()` already walks the right inspection chain from page to provenance to source manifests and PDF render artifacts, but it does not surface source-observed time, page freshness, or supersession state.
    - `status()` exposes root info, rebuild backlog, contradiction counts, PDF render counts, and `hot_topics`, but `hot_topics` is receipt-frequency-based rather than recentness-based.
    - `_apply_page_update()` is the current page-reorganization boundary. It can rename a page, preserve aliases, append `supersedes`, and stamp `last_reorganized_at`, but it cannot mark a page historical, stale, or deleted.
    - `_refresh_indexes()` already writes `topics/indexes/recent-changes.md`, sorted by `last_reorganized_at` and `last_updated_at`. The repo already has a real recentness pattern; it is just not surfaced through `status()` as a first-class operator affordance.
    - `_source_family()` is the actual `source_kind` normalization behavior. It maps codex, paperclip, hermes, pdf, and image by substring/suffix and sends everything else to `other`, which is the strongest code explanation for why markdown/text inputs land under `sources/other/`.
  - `/Users/agents/workspace/fleki/README.md` plus `/Users/agents/workspace/fleki/skills/knowledge/install/README.md` plus `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py`
    - These files define the current human-facing install, `--dry-run`, centralized-root, and PDF smoke story. They are the right existing boundary for making persistent-root semantics and install targets explicit.
  - `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` plus `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md` plus `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md` plus `/Users/agents/workspace/fleki/skills/knowledge/references/examples-and-validation.md`
    - These files already define meaning-first topic paths, the required save-output shape, authority-aware search/trace expectations, and a compact validation matrix. They are the best repo-owned patterns for teaching agents and operators without introducing a second contract source.
  - `/Users/agents/workspace/fleki/tests/common.py` plus `/Users/agents/workspace/fleki/tests/test_save.py` plus `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` plus `/Users/agents/workspace/fleki/tests/test_rebuild.py` plus `/Users/agents/workspace/fleki/tests/test_cli.py`
    - These files define the live harness patterns and the current test gaps. The repo already has a strong temp-root integration harness and direct artifact assertions, but it does not yet test freshness metadata, stale/superseded ranking, help discoverability, or recent-artifact visibility.
- Existing patterns to reuse:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/authority.py`
    - Numeric precedence pattern.
    - Reuse: keep authority as one explicit ranking axis, then layer freshness on top instead of flattening them into one meaning.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `section_support` per-section evidence map.
    - Reuse: if page-level freshness proves too blunt, section support is the smallest existing boundary for finer-grained temporal evidence.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `last_updated_at` / `last_reorganized_at` plus `topics/indexes/recent-changes.md`.
    - Reuse: expose recentness from existing timestamps instead of inventing a separate recent-state subsystem.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - Forward `supersedes` plus alias-preserving rehome in `_apply_page_update()`.
    - Reuse: stale/superseded cleanup should likely extend this boundary instead of creating a second cleanup path.
  - `/Users/agents/workspace/fleki/README.md` plus `/Users/agents/workspace/fleki/tests/common.py`
    - Concrete `bindings.json` / `decision.json` examples.
    - Reuse: ship a general save skeleton/example instead of relying on reverse-engineering or PDF-only smoke documentation.
  - `/Users/agents/workspace/fleki/tests/test_save.py`
    - Direct artifact assertions.
    - Reuse: verify new temporal fields by reading stored manifests, provenance notes, topic pages, and receipts directly, rather than inventing a new harness.

## 3.3 Open questions from research
- What is the smallest correct granularity for freshness metadata?
  - Evidence needed: one mixed page where evergreen doctrine and time-bound observations coexist. If page-level rollups mis-rank that case, the next boundary is section-support metadata rather than a full knowledge-unit persistence model.
- How should freshness compose with authority in ranking?
  - Evidence needed: one test matrix covering newer weak support versus older strong doctrine, and newer doctrine versus older session support. That matrix should settle whether freshness sorts before or after authority within otherwise similar topical matches.
- Should status recentness come from page timestamps or receipt timestamps?
  - Evidence needed: decide whether operators care more about recently ingested source material or recently changed semantic pages. The repo already has both timestamp families; `status()` currently surfaces neither directly.
- Where should stale/superseded cleanup semantics live?
  - Evidence needed: decide whether cleanup is a page-lifecycle extension of rebuild or whether save-time topic actions need an explicit stale/superseded outcome. The smallest answer is the one that does not create two competing cleanup paths.
- Is docs/help clarity enough for `source_kind` and naming, or does the code contract need tightening?
  - Evidence needed: determine how much the repo actually relies on loose substring-based `source_kind` normalization and whether external consumers use the Python module directly or mostly use the CLI/skill/install surfaces.
- Should recent-artifact discovery live in `status`, `search`, or direct exposure of the existing index?
  - Evidence needed: the smallest operator surface that resolves the 72-hour/recent-ingest use case without creating a parallel interface.
<!-- arch_skill:block:research_grounding:end -->

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
- Repo-owned source paths:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/**`
  - `/Users/agents/workspace/fleki/skills/knowledge/**`
  - `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` as the generated bundled runtime
  - `/Users/agents/workspace/fleki/install.sh`
  - `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py`
  - `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py`
- Machine-level mutable graph root:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` resolves the production default to `~/.fleki/knowledge`.
  - If `install.json` exists, its paths win; explicit roots that disagree fail loudly.
- Graph subtrees created and owned by `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`:
  - `topics/**`
  - `topics/indexes/**`
  - `provenance/**`
  - `sources/**`
  - `assets/**`
  - `receipts/save/**`
  - `receipts/search/**`
  - `receipts/trace/**`
  - `receipts/rebuild/**`
  - `receipts/status/**`
  - `search/**`
- Current source-family routing:
  - PDF-like inputs route to `sources/pdf/**`
  - image-like inputs route to `sources/images/**`
  - codex/paperclip/hermes runtime-origin inputs route to matching family folders
  - everything else, including markdown/text, routes to `sources/other/**`
- Time-related fields on disk today:
  - source manifests store `captured_at`
  - provenance notes store `created_at`
  - topic pages store `last_updated_at`, `last_reorganized_at`, and `supersedes`
  - `SourceBinding.timestamp` exists in memory, but the repository currently drops it before persistence

## 4.2 Control paths (runtime)
- `knowledge save`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py:_command_save`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:apply_save`
  - Live flow:
    - parse `bindings.json` and `decision.json`
    - validate through `validate_save_decision(...)`
    - persist raw or pointer source records
    - render eligible PDFs
    - write provenance notes
    - apply topic actions to semantic pages
    - write a save receipt
- `knowledge search`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py:_command_search`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:search`
  - Live flow:
    - load topic pages
    - tokenize the query
    - score against `current_path`, aliases, title, and full body
    - fold authority rank into the page score inside `_score_page()`
    - sort by score, authority rank, and path, which means authority is currently counted both inside the score and again at final sort time
    - attach supporting provenance for the matched section
- `knowledge trace`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py:_command_trace`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:trace`
  - Live flow:
    - resolve a page or section by id, alias, or best-effort text
    - walk from page metadata to provenance notes to source manifests
    - surface PDF render manifests, render artifacts, and render omissions when present
- `knowledge status`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py:_command_status`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:status`
  - Live flow:
    - load save and rebuild receipts
    - aggregate rebuild backlog, reading limits, contradiction counts, hot-topic counts, PDF render counts, and runtime-agreement data
    - optionally write a status receipt
- `knowledge rebuild`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py:_command_rebuild`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:apply_rebuild`
  - Live flow:
    - parse rebuild-plan JSON
    - update page path and `supersedes`
    - refresh indexes
    - write a rebuild receipt

## 4.3 Object model + key abstractions
- `SourceBinding`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`
  - Binds `source_id`, `local_path`, `source_kind`, `authority_tier`, `sensitivity`, `preserve_mode`, optional `timestamp`, and optional `notes`.
- `KnowledgeRepository`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
  - The single graph-read and graph-write boundary for save, search, trace, status, rebuild, and index refresh.
- `RebuildPlan` / `RebuildPageUpdate`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`
  - The current reorganization abstraction.
  - Supports rehome via `new_current_path`, supersession via `add_supersedes`, and free-form note text.
  - Does not model current/historical/stale lifecycle or delete operations.
- `validate_save_decision(...)`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py`
  - Owns required keys, enum validation, helper policy, forbidden topic roots, and caller-owned render-key rejection.
- `authority_rank(...)` and `merge_authority_postures(...)`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/authority.py`
  - Own current precedence and rollup behavior; authority is already first-class and numeric for ranking.
- `sample_save_decision(...)`
  - `/Users/agents/workspace/fleki/tests/common.py`
  - The best executable summary of the live save payload shape.
- Missing abstraction today:
  - there is no explicit freshness lifecycle object
  - time is split across source manifests, provenance notes, topic pages, and receipts
  - there is no unified current/historical/stale/superseded model

## 4.4 Observability + failure behavior today
- Receipts are the main append-only evidence trail.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:_write_receipt`
- Search observability:
  - search returns `knowledge_id`, `current_path`, `page_kind`, `authority_posture`, match section info, snippet, provenance paths, `trace_ref`, and score
  - it does not return source time, freshness, or lifecycle state
- Trace observability:
  - trace exposes provenance files, source manifests, render manifests, render artifacts, and render omissions
  - it is the strongest current answer to "where did this come from?"
- Status observability:
  - status exposes `resolved_data_root`, `install_manifest_path`, install-manifest presence, legacy-graph detection, rebuild backlog, contradiction counts, hot topics, topic count, PDF render counts, and runtime agreement
  - `hot_topics` is receipt-frequency-based, not recentness-based
- Important fail-loud boundaries:
  - invalid or source-family-first topic paths are rejected in validation
  - unknown enums, unknown evidence source ids, and caller-owned render metadata are rejected in validation
  - missing local source paths raise `FileNotFoundError`
  - incomplete eligible PDF render bundles raise `ValidationError`
  - explicit roots that disagree with the install manifest raise `ValidationError`
  - unsafe legacy migration states raise `ValidationError`
- Executable proof of current behavior:
  - `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`
  - `/Users/agents/workspace/fleki/tests/test_save.py`
  - `/Users/agents/workspace/fleki/tests/test_rebuild.py`
  - `/Users/agents/workspace/fleki/tests/test_cli.py`
  - `/Users/agents/workspace/fleki/tests/test_layout.py`

## 4.5 UI surfaces (ASCII mockups, if UI work)
- This is CLI work, not GUI work.
- Current operator feel is intentionally narrow:

```text
$ knowledge save --help
... --bindings <json> --decision <json> ...

$ knowledge status --json --no-receipt
{
  "resolved_data_root": "/Users/agents/.fleki/knowledge",
  "hot_topics": [...],
  "topic_count": 6,
  ...
}
```

- The gap is not missing output volume. The gap is that the current operator surface hides:
  - source-observed time
  - lifecycle state
  - recent ingests versus recent semantic changes
  - the real save schema and enum vocabulary
  - the distinction between a fresh install and an already-populated shared graph
<!-- arch_skill:block:current_architecture:end -->

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
- Keep the same machine-level root and subtree layout:
  - `~/.fleki/knowledge`
  - `topics/**`
  - `topics/indexes/**`
  - `provenance/**`
  - `sources/**`
  - `assets/**`
  - `receipts/**`
  - `search/**`
- Extend source record manifests and pointer payloads with a new persisted source-truth field:
  - `source_observed_at`
  - meaning: when the source was true, observed, or authored, as supplied through `SourceBinding.timestamp`
  - keep `captured_at` unchanged as the ingest-time fact
- Extend provenance note metadata with per-source time maps:
  - `source_observed_at_by_source`
  - `captured_at_by_source`
  - `latest_source_observed_at`
- Extend topic-page metadata with section and page rollups:
  - `section_temporal`
    - keyed by `section_id`
    - stores `last_supported_at` and `temporal_scope`
  - page-level `last_supported_at`
  - page-level `temporal_scope`
    - derived rollup, allowed to be `mixed` or `unknown`
  - page-level `lifecycle_state`
    - stored values: `current`, `historical`, `stale`
    - omitted field means lifecycle is still unknown and must stay visible as unknown in read paths
  - keep forward `supersedes` as the only stored replacement link
- Derive, do not persist:
  - reverse replacement/supersession chains
  - `effective_lifecycle_state = superseded` when another active page lists the current page in `supersedes`

## 5.2 Control paths (future)
- `save`
  - Keep the current JSON envelope and extend it minimally.
  - `SourceBinding.timestamp` becomes the documented ISO-8601 source-observed-time input.
  - `knowledge_units[]` gains optional `temporal_scope` with input values:
    - `evergreen`
    - `time_bound`
    - `ephemeral`
  - `topic_actions[]` gains optional `lifecycle_state` with input values:
    - `current`
    - `historical`
  - `stale` is rebuild-only in this pass.
  - Missing temporal hints default to unknown, never silently current.
  - `_apply_topic_actions()` rolls unit-level temporal hints and evidence times into `section_temporal`, page `last_supported_at`, page `temporal_scope`, and page `lifecycle_state` when the caller explicitly supplies `current` or `historical`.
- `search`
  - Keep lexical and topical match primary, with lower weight for bare path and provenance-token overlap than for title, section, and body meaning.
  - Apply hard demotion buckets first for:
    - `effective_lifecycle_state = superseded`
    - `lifecycle_state = stale`
  - Within each bucket, order remaining matches by:
    - lexical and topical score
    - authority rank
    - page lifecycle (`current` before unknown before `historical`)
    - `last_supported_at`
    - stable path tiebreak
- `trace`
  - Surface:
    - `source_observed_at_by_source`
    - `captured_at_by_source`
    - page `last_supported_at`
    - stored `lifecycle_state`
    - derived `effective_lifecycle_state`
    - derived replacement chain when a page is superseded
  - Keep provenance, source manifests, and PDF render state as the canonical inspection chain.
- `status`
  - Expose both recent semantic changes and recent ingests, not one blended field:
    - `recent_topics` from the same page-timestamp rollup already used by `recent-changes.md`, keyed by `max(last_reorganized_at, last_updated_at)`
    - `recent_source_ingests` from save-receipt `created_at`, with receipt-linked source record paths as the displayed drilldown
  - Add:
    - `historical_topic_count`
    - `stale_topic_count`
    - `superseded_topic_count`
  - Keep `resolved_data_root` and install-manifest visibility explicit.
- `rebuild`
  - Own rehome, stale transitions, supersession-driven retirement, and explicit delete.
  - `RebuildPageUpdate` grows:
    - `lifecycle_state`
    - `delete_page`
  - `save` may mark a newly written page as `current` or `historical`. `rebuild` owns `stale` and delete.
  - Delete is allowed only when a page is already `stale`.
  - Superseded pages stay on disk as traceable historical pages in this pass; delete is not the first response to supersession.
  - `save` remains bounded knowledge filing. `rebuild` owns cleanup, retirement, and deletion.

## 5.3 Object model + abstractions (future)
- Keep the system LLM-led.
  - The repository persists explicit facts and explicit lifecycle outcomes.
  - The repository does not add a deterministic decay engine, a score daemon, or a hidden retrieval backend.
- Keep the save contract additive and small:
  - source-truth time comes from `SourceBinding.timestamp`
  - knowledge-level time-boundedness comes from `knowledge_units[].temporal_scope`
  - page lifecycle comes from optional `topic_actions[].lifecycle_state` for `current` or `historical`, plus later rebuild actions for `stale` and delete
- Keep `source_kind` tolerant in code.
  - Do not hard-enum `source_kind` in this pass.
  - Publish a canonical vocabulary and normalization guide instead.
  - Keep `_source_family()` substring/suffix routing as the implementation boundary.
- Search reads page rollups.
  - Trace remains the source/provenance truth surface.
  - Section-level rollups are the smallest correct sub-page structure.
  - Do not add a full persisted knowledge-unit store.
- Keep `knowledge save --help` concise.
  - Point it to a checked-in valid skeleton/example and the bundled runtime `README.md` instead of dumping the full schema inline.
  - Keep the checked-in example derived from the live contract used in tests and docs.

## 5.4 Invariants and boundaries
- Layout owns path resolution and install-manifest precedence.
  - Repository code consumes the resolved layout; it does not decide the root itself.
- Authority outranks freshness.
  - Explicit stale or superseded state demotes first.
  - Otherwise authority ordering remains ahead of currentness and recency.
- Unknown temporal data stays unknown.
  - Omitted `lifecycle_state` means unknown on disk and in read paths.
  - Do not silently treat old untouched pages as current.
- `save` writes evidence, temporal rollups, and optional `current` or `historical` lifecycle on the page it is updating.
  - `rebuild` owns `stale`, delete, and supersession-driven retirement.
- There is no age-only deletion path.
- Superseded pages remain traceable on disk in this pass.
  - Rebuild may retire them, but it does not delete them by default.
- Reverse supersession is derived, not stored.
  - `supersedes` remains the single stored replacement link.
- Generated runtime files are never hand-edited.
  - Repo source and skill docs change first.
  - `scripts/sync_knowledge_runtime.py` regenerates `skills/knowledge/runtime/**`.
- Validation, CLI help, README, and skill docs must tell the same story.

## 5.5 UI surfaces (ASCII mockups, if UI work)
- The future CLI stays compact, but it becomes explicit about lifecycle and contract shape:

```text
$ knowledge save --help
Apply a save decision from JSON inputs.
Source-observed time: use "timestamp" in each binding object (ISO 8601).
See bundled README.md for a valid save example, naming crosswalk, and install/root notes.

$ knowledge status --json --no-receipt
{
  "resolved_data_root": "/Users/agents/.fleki/knowledge",
  "topic_count": 42,
  "recent_topics": ["product/customer-io/current-setup"],
  "recent_source_ingests": ["sources/other/customer-io-notes.md.record.json"],
  "historical_topic_count": 6,
  "stale_topic_count": 3,
  "superseded_topic_count": 4
}

$ knowledge search "Customer.io" --json --no-receipt
{
  "results": [
    {
      "current_path": "product/customer-io/current-setup",
      "authority_posture": "live_doctrine",
      "lifecycle_state": "current",
      "last_supported_at": "2026-04-03T12:00:00+00:00"
    }
  ]
}

$ knowledge trace "product/customer-io/legacy-setup" --json --no-receipt
{
  "current_path": "product/customer-io/legacy-setup",
  "effective_lifecycle_state": "superseded",
  "replacement_paths": ["product/customer-io/current-setup"],
  "source_observed_at_by_source": {
    "note.customer_io.legacy": "2026-03-01T10:00:00+00:00"
  }
}
```
<!-- arch_skill:block:target_architecture:end -->

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## 6.1 Change map (table)

| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| ---- | ---- | ------------------ | ---------------- | --------------- | --- | ------------------ | -------------- |
| Source-truth time input | `/Users/agents/workspace/fleki/src/knowledge_graph/models.py` and `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | `SourceBinding.timestamp`, `_binding_from_dict()` | Typed field exists and the CLI accepts it implicitly, but help text never explains it and the repository drops it before persistence. | Make `timestamp` a documented ISO-8601 source-observed-time input and preserve the meaning all the way to disk. | Freshness cannot be reasoned about if the only source-time input is hidden. | Caller may supply `timestamp`; repository persists it as `source_observed_at`, distinct from ingest time. | `/Users/agents/workspace/fleki/tests/test_cli.py`, `/Users/agents/workspace/fleki/tests/test_contracts.py`, `/Users/agents/workspace/fleki/tests/test_save.py` |
| Temporal enums and validation | `/Users/agents/workspace/fleki/src/knowledge_graph/authority.py` and `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py` | enum sets, `validate_save_decision()` | Canonical enforcement for save shape, enum vocab, and topic-path rules lives in code, while the existing docs/examples still do not fully surface the enum vocabulary or validation-only rules. There is no temporal or lifecycle validation today. | Add canonical input enums for `knowledge_units[].temporal_scope` and `topic_actions[].lifecycle_state`; keep one enum source of truth and mirror it in docs/help. | The operator confusion came from reverse-engineering validation-only rules and incomplete docs. | Validator owns allowed temporal/lifecycle values; docs/help mirror that vocabulary exactly. | `/Users/agents/workspace/fleki/tests/test_contracts.py`, `/Users/agents/workspace/fleki/tests/test_save.py`, `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_rebuild.py`, `/Users/agents/workspace/fleki/tests/test_source_families.py`, `/Users/agents/workspace/fleki/tests/test_cli.py`, `/Users/agents/workspace/fleki/tests/test_skill_package.py` |
| Source manifest persistence | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_persist_source_records()` | Source manifests and pointer payloads store `captured_at`, storage mode, and hash; binding timestamp is dropped. | Persist both `captured_at` and `source_observed_at` in source manifests and pointer payloads. | Search, trace, and topic rollups need durable source-truth time facts. | Source record becomes the SSOT for source identity, storage mode, source-observed time, and capture time. | `/Users/agents/workspace/fleki/tests/test_save.py`, `/Users/agents/workspace/fleki/tests/test_source_families.py`, `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` |
| Provenance time maps | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_persist_provenance_notes()` | Provenance metadata stores reading modes, gaps, render info, and `created_at`; it has no per-source time map or freshness explanation. | Add `source_observed_at_by_source`, `captured_at_by_source`, and `latest_source_observed_at`. | Trace needs to explain why support is current, stale, or mixed. | Provenance note becomes the human-readable bridge from claim to time facts. | `/Users/agents/workspace/fleki/tests/test_save.py`, `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` |
| Topic temporal rollups | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_apply_topic_actions()` | Page metadata stores authority, support refs, update time, and `supersedes`; there is no temporal rollup or lifecycle state. | Add `section_temporal`, page `last_supported_at`, page `temporal_scope`, and page `lifecycle_state` rollups. | Old ephemeral evidence and newer authority currently collapse into one undifferentiated support layer. | Page metadata separates authority from lifecycle and freshness rollups without introducing a second knowledge store. | `/Users/agents/workspace/fleki/tests/test_save.py`, `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_rebuild.py` |
| Save receipt recentness | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_write_save_receipt()` | Save receipts record touched topics, pending rebuild scopes, and PDF info, but not enough recent-ingest detail to drive the operator use case directly. | Add minimal recent-ingest facts only if status continues to surface ingest recency from receipts. | Recent-artifact discovery needs a clear ingest trail. | Save receipts remain ingest audit evidence, not a second search surface. | `/Users/agents/workspace/fleki/tests/test_save.py`, `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` |
| Search ranking and noise control | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `search()`, `_score_page()` | Ranking is lexical over path, aliases, title, and full body, then authority. Path/provenance tokens can create false positives. | Keep topical title/section text primary, hard-demote stale/superseded pages, then order by authority, lifecycle, and `last_supported_at`; reduce bare metadata-token weight. | Current search can return metadata noise and treats stale support as equal current truth. | Search becomes relevance-first, lifecycle-aware, authority-aware, and freshness-aware. | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` plus a new false-positive regression case |
| Trace lifecycle visibility | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` and `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | `trace()`, `_resolve_trace_target()`, `_command_trace()` | Trace returns provenance, source records, and render artifacts, but no source-truth time or lifecycle chain. | Return page rollups, source-observed time maps, and derived replacement chains; expose the minimum lifecycle fields in plain text. | Trace is the inspection tool operators use when search is ambiguous. | Trace answers both provenance and currentness. | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_cli.py` |
| Status recentness and lifecycle counts | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` and `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | `status()`, `_command_status()` | `hot_topics` is receipt-frequency-based, `stale_knowledge_pages` really means pending rebuild scopes, and there is no first-class recent-topic or recent-ingest view. | Add `recent_topics`, `recent_source_ingests`, and explicit historical/stale/superseded counts; rename or remove the misleading `stale_knowledge_pages` field once real stale lifecycle counts exist; keep `hot_topics` secondary if it remains. | Smoke validation needs “what changed recently” and “is this shared persistent state?” more than popularity, and the old stale field name will conflict with the new lifecycle meaning. | Status tells the operator where the graph lives, what changed recently, and what is stale or superseded. | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_cli.py` |
| Recent index alignment | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_refresh_indexes()` | `recent-changes.md` sorts only by `last_reorganized_at` and `last_updated_at`; it does not show lifecycle or source-truth recency. | Align index generation with the same recentness and lifecycle semantics used by `status()` and `search()`. | The repo already has a recentness index; it just reflects edits rather than knowledge currentness. | `topics/indexes/recent-changes.md` mirrors the same lifecycle semantics the CLI exposes. | `/Users/agents/workspace/fleki/tests/test_rebuild.py`, `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` |
| Rebuild lifecycle contract | `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`, and `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `RebuildPageUpdate`, `_rebuild_plan_from_dict()`, `apply_rebuild()`, `_apply_page_update()` | Rebuild can rename pages and append `supersedes`; it cannot retire, archive, delete, or mark a page stale. | Add `lifecycle_state` and `delete_page` with fail-loud guards; keep cleanup ownership for `stale` and delete in rebuild, not save. | The plan needs an explicit, agent-driven way to remove fully superseded or stale knowledge without breaking the traceable history promise. | Save may write `current` or `historical`; rebuild performs `stale`, supersession-driven retirement, and delete for already stale pages only. | `/Users/agents/workspace/fleki/tests/test_rebuild.py`, `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_cli.py` |
| Save help and plain-text CLI clarity | `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | `_build_parser()`, `_command_search()`, `_command_trace()`, `_command_status()` | Help only exposes file-path flags for `save`; plain-text search/trace/status omit lifecycle and contract guidance. | Add direct help pointers to the checked-in save skeleton/example and print the minimum lifecycle/currentness fields in plain text. | First-time operators should not inspect repo code to use the tool correctly. | CLI help becomes self-explanatory for save authoring and lifecycle-aware output. | `/Users/agents/workspace/fleki/tests/test_cli.py`, `/Users/agents/workspace/fleki/tests/test_skill_package.py` |
| Persistent-root semantics and install wording | `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py`, `/Users/agents/workspace/fleki/README.md`, `/Users/agents/workspace/fleki/skills/knowledge/install/README.md`, `/Users/agents/workspace/fleki/skills/knowledge/install/bootstrap.sh`, and `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py` | `resolve_knowledge_layout()`, human-facing install docs, installer output, bootstrap output | The real graph root is install-manifest-driven `~/.fleki/knowledge`, but neither status nor installer messaging clearly says that a fresh install can attach to an existing shared graph. | Make persistent-root semantics explicit in installer output, bundle bootstrap output, status output, and docs; optionally surface non-empty graph state. | This was the biggest real testing confusion. | Install/update is tool deployment; graph cleanliness is a separate inspectable state. | `/Users/agents/workspace/fleki/tests/test_layout.py`, `/Users/agents/workspace/fleki/tests/test_cli.py`, `/Users/agents/workspace/fleki/tests/test_skill_package.py` |
| Naming and `source_kind` crosswalk | `/Users/agents/workspace/fleki/pyproject.toml`, `/Users/agents/workspace/fleki/src/knowledge_graph/__init__.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`, `/Users/agents/workspace/fleki/README.md`, and `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` | distribution name, module name, CLI name, skill key, `_source_family()` | Distribution/module/CLI/skill names are split, and `source_kind` normalizes by substring/suffix with markdown landing under `sources/other/`; this is real behavior but not one coherent operator story. | Publish one explicit name crosswalk and one explicit `source_kind` normalization guide; do not force a storage-family migration in this pass. | This solves naming and `sources/other/` ambiguity without unnecessary churn. | `fleki-knowledge-graph` is the distribution, `knowledge_graph` the Python package, `knowledge` the CLI, `fleki/knowledge` the skill key, and storage-family routing is documented. | `/Users/agents/workspace/fleki/tests/test_source_families.py`, `/Users/agents/workspace/fleki/tests/test_skill_package.py` |
| Generated runtime propagation | `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py` and `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` | runtime bundle generation | The bundled runtime mirrors repo source only after an explicit sync pass. | Regenerate the runtime bundle after any source or skill-contract change; do not hand-edit generated runtime files. | Installed skill behavior must match repo source and docs. | Runtime propagation stays source-first and generated. | `/Users/agents/workspace/fleki/tests/test_skill_package.py` |

## 6.2 Migration notes
- Deprecated APIs (if any):
  - None that require immediate removal.
  - `SourceBinding.timestamp` stays the public input name; only the persisted on-disk field becomes `source_observed_at`.
  - Existing rebuild plans remain valid; new lifecycle fields are additive.
- Delete list (what must be removed; include superseded shims/parallel paths if any):
  - no reverse `superseded_by` field
  - no age-only cleanup path
  - no manual edits under `skills/knowledge/runtime/**`
  - no `stale_knowledge_pages` field name once real stale lifecycle counts exist
  - rewrite or delete docs that imply:
    - fresh install means empty graph
    - `hot_topics` is the same thing as recent truth
    - enum vocabulary or validation-only save rules are only discoverable in code or failure output

## Pattern Consolidation Sweep (anti-blinders; scoped by plan)
| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| ---- | ------------- | ---------------- | ---------------------- | ------------------------------------- |
| Test fixture contract | `/Users/agents/workspace/fleki/tests/common.py:sample_save_decision()` | Add temporal defaults and the checked-in save skeleton shape | Every save/search/rebuild test fixture depends on this payload shape | include |
| Skill save contract | `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md` and `/Users/agents/workspace/fleki/skills/knowledge/references/examples-and-validation.md` | Mirror temporal inputs, lifecycle vocabulary, and schema pointer | Prevent docs from lagging validation again | include |
| Skill authority contract | `/Users/agents/workspace/fleki/skills/knowledge/references/storage-and-authority.md` | Mirror the rule that authority and freshness stay separate axes and explain the new ranking interplay plainly | Prevent the authority story from drifting when freshness lands | include |
| Skill search/trace/status contract | `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md` and `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` | Mirror lifecycle-aware search, trace, status, and cleanup guidance | Prevent agent instructions from drifting away from repository behavior | include |
| Install and root messaging | `/Users/agents/workspace/fleki/README.md`, `/Users/agents/workspace/fleki/skills/knowledge/install/README.md`, `/Users/agents/workspace/fleki/skills/knowledge/install/bootstrap.sh`, and `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py` | Make persistent-root semantics, naming, and recent-state expectations explicit | Prevent the fresh-install/shared-graph confusion from recurring | include |
| Recentness index | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:_refresh_indexes()` | Reuse the existing recent-changes artifact instead of inventing a parallel recentness store | Prevent status, index, and search from drifting apart | include |
| Runtime bundle propagation | `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py` and `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` | Regenerate bundled runtime from repo source after contract changes | Prevent repo source and installed runtime from diverging | include |
| Runtime manifest notes | `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py` | Surface deeper per-runtime graph-state messaging only if docs/status prove insufficient | Avoid broadening install-surface churn before core freshness logic lands | defer |
| PDF render timestamps | `/Users/agents/workspace/fleki/src/knowledge_graph/pdf_render.py` and `/Users/agents/workspace/fleki/tests/test_pdf_rendering.py` | Only surface render-created time if trace explicitly needs it | Render time is not the same as source-truth freshness | defer |
| Storage-family migration | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:_source_family()` | Keep docs-first normalization instead of introducing `sources/markdown/**` now | Avoid churn and backfill risk that does not solve the freshness problem | defer |
| Semantic page-body renderer | `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` | Do not move freshness logic into body rendering | Freshness belongs in metadata, ranking, trace, and lifecycle | exclude |
| ID generation | `/Users/agents/workspace/fleki/src/knowledge_graph/ids.py` | Do not couple stable ids to lifecycle work | ID semantics are unrelated to freshness | exclude |
<!-- arch_skill:block:call_site_audit:end -->

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan (tests optional). No fallbacks/runtime shims - the system must work correctly or fail loudly (delete superseded paths). Prefer programmatic checks per phase; defer manual/UI verification to finalization. Avoid negative-value tests (deletion checks, visual constants, doc-driven gates). Also: document new patterns/gotchas in code comments at the canonical boundary (high leverage, not comment spam).

## Phase 1 - Land the contract and shipped operator story

Status: COMPLETE

Completed work:
- Added temporal and lifecycle input validation for `knowledge save`.
- Added save-help guidance for `timestamp`, `temporal_scope`, `lifecycle_state`, and the bundled README.
- Updated the repo-owned README, skill refs, install docs, installer messaging, and runtime README template to say the same naming/root/save story.
- Updated shared test fixtures and CLI/contract tests to lock the Phase 1 contract.
- Added a minimal valid `bindings.json` and `decision.json` example to the generated runtime README so the installed help target is truthful.

Goal
- Make the agreed temporal and lifecycle contract real at the input, help, and docs layer before the repository starts persisting new fields.

Work
- Update the `save` input contract in:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/authority.py`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`
- Lock these caller-facing rules:
  - `SourceBinding.timestamp` means source-observed time
  - `knowledge_units[].temporal_scope` accepts the chosen vocabulary
  - `topic_actions[].lifecycle_state` only accepts `current` or `historical`
  - `stale` and delete remain rebuild-owned
  - omitted lifecycle means unknown, not current
- Update the checked-in contract surfaces together:
  - `/Users/agents/workspace/fleki/README.md`
  - `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md`
  - `/Users/agents/workspace/fleki/skills/knowledge/references/examples-and-validation.md`
  - `/Users/agents/workspace/fleki/skills/knowledge/references/storage-and-authority.md`
  - `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md`
  - `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`
  - `/Users/agents/workspace/fleki/skills/knowledge/install/README.md`
- Update install/help wording in both installer paths:
  - `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py`
  - `/Users/agents/workspace/fleki/skills/knowledge/install/bootstrap.sh`
- Make the help pointer actually shippable through the installed runtime:
  - either embed the minimal guidance directly in CLI help
  - or point to a bundled runtime path that is guaranteed to exist after `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py`
- Update shared fixtures first so later phases build on one contract:
  - `/Users/agents/workspace/fleki/tests/common.py:sample_save_decision()`

Verification (smallest signal)
- Run targeted contract and CLI tests:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_contracts tests.test_cli tests.test_skill_package -v`
- Confirm the installed/help-facing path named in `knowledge save --help` is real in the runtime bundle plan, not just in repo-only docs.

Docs/comments (propagation; only if needed)
- Add one short boundary comment in the save/input path only if the source-observed-time meaning would otherwise be easy to misread.

Exit criteria
- A new operator can discover the real `save` shape, naming crosswalk, persistent-root story, and lifecycle ownership without reading repository code.
- The repo has one coherent public story across CLI help, README, skill refs, and install surfaces.

Rollback
- If the shipped-help path cannot be made truthful in this phase, keep the contract clarification in repo docs only and do not point CLI help at a nonexistent runtime file.

## Phase 2 - Persist temporal facts at the source, provenance, and section boundaries

Status: COMPLETE

Completed work:
- Persisted `source_observed_at` in copied and pointer-backed source records.
- Added provenance time maps and `latest_source_observed_at`.
- Added `section_temporal`, page `last_supported_at`, page `temporal_scope`, and save-time `lifecycle_state` persistence.
- Locked the new storage fields with direct save-path assertions.

Goal
- Thread explicit time facts through the storage model so later ranking and lifecycle behavior can read real persisted evidence instead of inferring from receipts alone.

Work
- Update source-record persistence in `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`:
  - persist `source_observed_at` alongside `captured_at`
  - keep pointer and copied-source manifests aligned
- Update provenance-note persistence in the same file:
  - add `source_observed_at_by_source`
  - add `captured_at_by_source`
  - add `latest_source_observed_at`
- Update topic-page persistence in `_apply_topic_actions()`:
  - add `section_temporal`
  - add page `last_supported_at`
  - add page `temporal_scope`
  - add optional page `lifecycle_state`
- Preserve the chosen unknown semantics:
  - omitted lifecycle field stays unknown on disk
  - do not synthesize `current` for untouched legacy pages
- Keep storage additive:
  - no reverse `superseded_by`
  - no separate persisted knowledge-unit store

Verification (smallest signal)
- Run targeted persistence tests that inspect stored artifacts directly:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_save tests.test_source_families -v`
- Add or update direct assertions for source manifests, provenance notes, and topic-page frontmatter.

Docs/comments (propagation; only if needed)
- Add one short comment at the source-record persistence boundary explaining why `captured_at` and `source_observed_at` are intentionally separate.

Exit criteria
- A single save can write truthful source time, provenance time maps, section temporal rollups, and page rollups without changing search or rebuild behavior yet.

Rollback
- Revert additive storage changes if any one of the three persistence layers cannot carry the same truth consistently.

## Phase 3 - Make retrieval and visibility freshness-aware

Status: COMPLETE

Completed work:
- Re-ranked search to reduce metadata/path noise and to demote stale or superseded pages before authority and freshness tie-breaks.
- Extended trace and status to surface lifecycle, `last_supported_at`, replacement paths, and recentness lists.
- Updated the recent-changes index and plain-text CLI output to match the new currentness story.
- Added direct regressions for false-positive search noise and for authority winning over newer weak support.

Goal
- Use the persisted temporal facts to improve search, trace, status, and recentness visibility without introducing a deterministic decay engine.

Work
- Update search behavior in `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`:
  - reduce bare path and provenance-token weight
  - keep lexical and topical score primary within lifecycle buckets
  - hard-demote explicit `stale` and derived `superseded`
  - keep authority ahead of lifecycle and `last_supported_at` after demotion
- Update trace behavior in repository and CLI:
  - surface source-observed and capture-time maps
  - surface stored and derived lifecycle fields
  - show replacement chains for superseded pages
- Update status behavior in repository and CLI:
  - add `recent_topics` from the existing page timestamp rollup
  - add `recent_source_ingests` from save-receipt `created_at`
  - add historical, stale, and superseded counts
  - rename or remove the misleading `stale_knowledge_pages` field
- Update `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py:_refresh_indexes()` so the recent-changes artifact matches the same recentness and lifecycle story as `status`.

Verification (smallest signal)
- Run targeted flow tests:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_search_trace_status tests.test_cli -v`
- Add one explicit false-positive regression where metadata/path overlap used to beat topical meaning.
- Add one integration scenario where newer weak support does not outrank older strong doctrine.

Docs/comments (propagation; only if needed)
- Add one short comment near the ranking boundary explaining the intended order: demotion bucket, then lexical/topical score, then authority, then lifecycle/time tie-breaks.

Exit criteria
- Search results prefer current well-supported truth over stale or superseded matches.
- Trace can explain why a result is current, historical, stale, or superseded.
- Status answers “what changed recently?” without date-globbing.

Rollback
- Do not ship search re-ranking unless trace and status expose enough evidence to explain the changed ordering.

## Phase 4 - Add explicit rebuild-owned lifecycle cleanup

Status: COMPLETE

Completed work:
- Extended rebuild parsing and page updates to support `lifecycle_state` and `delete_page`.
- Added fail-loud delete guards so only already-stale pages can be removed.
- Kept superseded pages on disk while making them rank lower and stay traceable through replacement paths.
- Added rebuild regressions for stale-page deletion and superseded-page traceability.

Goal
- Give agents one explicit shared-contract path to retire stale knowledge and keep superseded history traceable without introducing silent deletion.

Work
- Extend rebuild input and model types in:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
- Add rebuild support for:
  - `lifecycle_state`
  - `delete_page`
  - fail-loud guards that only allow delete for already stale pages
- Preserve the chosen history rule:
  - superseded pages remain on disk in this pass
  - rebuild may retire them, but not delete them by default
- Ensure search, trace, and status all understand the rebuild-written lifecycle fields.

Verification (smallest signal)
- Run rebuild-focused tests:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_rebuild tests.test_search_trace_status tests.test_cli -v`
- Add one regression that proves a superseded page remains traceable.
- Add one regression that proves an already stale page can be explicitly removed through rebuild.

Docs/comments (propagation; only if needed)
- Update the rebuild-facing operator docs and skill wording only where the new lifecycle fields are actually used.

Exit criteria
- Cleanup has one clear owner.
- Agents can retire stale knowledge through rebuild.
- Superseded knowledge remains explainable through trace and replacement chains.

Rollback
- If rebuild cleanup cannot preserve the traceability invariant, ship retirement-only behavior first and defer delete.

## Phase 5 - Sync runtime, finish operator polish, and verify end to end

Status: COMPLETE

Completed work:
- Regenerated the bundled runtime from the repo source.
- Kept the runtime README and shipped help text aligned with the new save, naming, and persistent-root story.
- Ran the full unittest suite and `compileall` after the implementation landed.
- Ran an isolated CLI smoke for `save`, `status`, `search`, and `trace` against a temporary root.
- Closed the audit-found drift by shipping the valid save example in the generated runtime README and locking it with a package test.

Goal
- Make repo source, bundled runtime, installed behavior, and human docs say the same thing.

Work
- Regenerate the bundled runtime from repo source:
  - `.venv/bin/python scripts/sync_knowledge_runtime.py`
- Confirm the shipped runtime includes the help target and contract wording chosen in Phase 1.
- Finish remaining wording alignment across README, skill refs, install docs, and status/search/trace output examples.
- Run the full repo verification required by this repo for code changes.
- Do one final manual CLI smoke against the local environment.

Verification (smallest signal)
- Run:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
  - `.venv/bin/python -m compileall src`
- Manual CLI smoke:
  - `knowledge save --help`
  - `knowledge status --json --no-receipt`
  - `knowledge search ... --json --no-receipt`
  - `knowledge trace ... --json --no-receipt`

Docs/comments (propagation; only if needed)
- No new comments by default. Only keep the high-leverage boundary comments added in earlier phases.

Exit criteria
- Repo source, bundled runtime, installed CLI/help, and human docs agree on time, lifecycle, install root, naming, and recentness behavior.
- The full test suite and compile step pass.

Rollback
- Do not refresh the bundle or claim completion if repo docs, runtime contents, and live CLI help still diverge.
<!-- arch_skill:block:phase_plan:end -->

# 8) Verification Strategy (common-sense; non-blocking)

## 8.1 Unit tests (contracts)
- Validate the temporal save-input contract and any new lifecycle vocabulary.
- Validate persisted source/provenance/topic metadata directly.
- Validate ranking helper behavior at the smallest useful boundary.

## 8.2 Integration tests (flows)
- Save an older session-like source and a newer doctrine-like source into overlapping topic space, then assert search order, trace output, and status surfaces.
- Add one explicit false-positive regression where path or provenance-token overlap used to outrank topical meaning.
- Rebuild a page into superseded state, then assert that search and status no longer treat it as equally current.
- Rebuild an already stale page into deleted state, then assert that cleanup happens only through rebuild while superseded history remains traceable.

## 8.3 E2E / device tests (realistic)
- Manual CLI smoke only:
  - `knowledge save --help`
  - `knowledge status --json --no-receipt`
  - one freshness-aware `knowledge search ... --json --no-receipt`
  - one `knowledge trace ... --json --no-receipt` check that explains a ranking or lifecycle decision
- For repo code completion, follow the repo rule:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
  - `.venv/bin/python -m compileall src`

# 9) Rollout / Ops / Telemetry

## 9.1 Rollout plan
- Land additive metadata and operator-contract changes first.
- Land ranking and cleanup behavior after the metadata is visible enough to debug.
- Refresh the bundled runtime and installed skill only after the repo-owned docs and CLI help match live behavior.

## 9.2 Telemetry changes
- No external telemetry system is needed.
- Local evidence should come from:
  - visible `status` fields for recent topics, recent ingests, and current/stale/superseded counts
  - receipts as supporting ingest evidence
  - recent-topic indexes as supporting repo artifacts

## 9.3 Operational runbook
- Use `knowledge status` to confirm the real shared data root before assuming you are in a blank graph.
- Use `knowledge trace` when ranking looks surprising; it should expose source time and supersession state.
- Use `rebuild` to retire or delete fully superseded knowledge instead of hand-editing the graph.
- If recent-source discovery remains awkward after Phase 4, reopen this plan rather than teaching operators to rely on date-globbing again.

# 10) Decision Log (append-only)

## 2026-04-03 - Keep freshness LLM-led and artifact-supported

Context
- The user explicitly wants an elegant and minimal notion of time decay that leans on model judgment instead of deterministic preprocessing or retrieval infrastructure.

Options
- Add a deterministic decay engine or retrieval service.
- Store explicit temporal facts and let the agent decide freshness outcomes.

Decision
- Store explicit temporal facts and lifecycle outcomes on disk, then use those facts as ranking and cleanup hints.

Consequences
- The repository stays simple and inspectable.
- The plan must define the persisted facts clearly enough that different agents can make compatible decisions.

Follow-ups
- Deep-dive must confirm the smallest correct metadata granularity.

## 2026-04-03 - Treat operator clarity as part of the same change

Context
- Real testing already exposed confusion around fresh installs, hidden `save` schema, enum values, topic-path rules, naming, and PDF/runtime expectations.

Options
- Solve temporal freshness first and defer operator clarity.
- Fix the operator contract in the same architectural change.

Decision
- Keep operator clarity in scope for this plan.

Consequences
- The work is slightly broader than a pure ranking change.
- The resulting system is much more likely to be operable by someone who did not write the code.

Follow-ups
- Deep-dive should decide which naming or storage-taxonomy issues need code changes versus docs-only clarification.

## 2026-04-03 - Use section temporal rollups and page lifecycle, not a second knowledge store

Context
- The plan needs enough temporal precision to distinguish evergreen doctrine from time-bound or ephemeral support, but the repo should stay markdown-first and avoid introducing a parallel persisted knowledge-unit database.

Options
- Store freshness only at the whole-page level.
- Add a new persisted knowledge-unit store for per-claim temporal metadata.
- Reuse the existing section-support boundary and add section rollups plus page rollups.

Decision
- Reuse the existing section boundary.
- Store `section_temporal` by `section_id`, then roll that up to page `last_supported_at`, page `temporal_scope`, and page `lifecycle_state`.
- Do not add a second persisted knowledge-unit store in this pass.

Consequences
- Mixed pages can stay truthful without forcing a major storage redesign.
- Search can rank primarily at the page level while trace can still explain finer-grained support timing.
- The implementation has one new metadata pattern to thread through save, trace, search, and tests.

Follow-ups
- Phase 2 should persist and test section-level rollups directly.

## 2026-04-03 - Rebuild owns stale and superseded cleanup

Context
- The user wants agents to remove fully superseded or clearly stale knowledge, but the repo should not grow two competing cleanup paths or a hidden retention subsystem.

Options
- Let `save` also retire or delete pages.
- Let `rebuild` own lifecycle transitions and explicit deletion.
- Add an age-driven background cleanup path.

Decision
- Keep `save` limited to evidence filing and page rollup updates.
- Extend `rebuild` with explicit `lifecycle_state` and `delete_page` handling.
- Allow delete only when a page is already `stale` or derivably `superseded`.

Consequences
- Cleanup stays explicit, inspectable, and fail loud.
- Operators get one place to retire or delete knowledge instead of mixing filing and cleanup behavior.
- Rebuild tests and docs will need to grow beyond path moves and `supersedes`.

Follow-ups
- Phase 3 should wire the new rebuild behavior into search/status expectations and deletion guards.

## 2026-04-03 - Keep ranking authority-first after stale demotion

Context
- The core tension is that newer sources should help current truth win, but newer weak support must not outrank stronger doctrine simply because it is recent.

Options
- Sort by recency before authority.
- Sort by authority before recency, with special handling for stale or superseded pages.
- Collapse authority and freshness into one composite meaning.

Decision
- Hard-demote derived `superseded` pages and explicit `stale` pages first.
- Among the remaining matches, keep authority ahead of lifecycle and `last_supported_at`.
- Keep authority and freshness as separate facts in both storage and ranking.

Consequences
- Freshness sharpens retrieval without turning Fleki into a recency-first system.
- Trace and status must surface enough timing and lifecycle data to explain surprising rankings.

Follow-ups
- Phase 3 should add direct ranking regressions for newer weak support versus older strong doctrine.

## 2026-04-03 - Keep the operator contract docs-first and concise

Context
- Testing showed that operators were reverse-engineering `save`, `source_kind`, naming, and install semantics from source files and environment behavior.

Options
- Dump the full save schema inline into `knowledge save --help`.
- Tighten every loose naming and `source_kind` behavior in code before clarifying docs.
- Keep code behavior mostly stable, publish one explicit crosswalk and one valid skeleton, and point concise CLI help at those checked-in references.

Decision
- Keep `knowledge save --help` short and point it at a checked-in valid example and reference docs.
- Publish one naming crosswalk for distribution, module, CLI, and skill key.
- Keep `source_kind` tolerant in code and document the normalization behavior instead of forcing a storage-family migration in this pass.

Consequences
- The operator can discover the real contract without reading Python files.
- The repo avoids churn that does not materially help the freshness work.
- The checked-in example becomes a high-value contract artifact and must stay synced with validation and tests.

Follow-ups
- Phase 1 should align CLI help, skill refs, README wording, and sample fixtures with the same contract story.

## 2026-04-03 - Split lifecycle ownership and keep superseded history traceable

Context
- The first deep-dive draft let both `save` and `rebuild` own lifecycle changes, and it also allowed delete for derivably superseded pages even though the plan still promises history remains traceable.

Options
- Let both `save` and `rebuild` mutate all lifecycle states.
- Put all lifecycle mutation in `rebuild`.
- Let `save` set the initial active state while `rebuild` owns stale and delete.

Decision
- `save` may write `current` or `historical` on the page it is actively updating.
- `rebuild` owns `stale`, supersession-driven retirement, and delete.
- Superseded pages stay on disk as traceable historical pages in this pass.
- Delete is only allowed for already stale pages.

Consequences
- The artifact has one clear cleanup owner.
- The repo keeps a traceable path for superseded knowledge without introducing tombstones or a second history system.
- Agents still get an explicit path to remove clearly stale material.

Follow-ups
- Phase 3 should add rebuild and trace regressions that prove superseded pages stay explainable while stale pages can be explicitly removed.

## 2026-04-03 - Status is the primary recentness surface

Context
- Research left open whether recent discovery should live in `status`, `search`, or the existing recent-changes index. The deeper target design now needs one authoritative operator answer.

Options
- Use `search` as the recency-discovery surface.
- Add a new recent-artifacts command.
- Make `status` primary and keep receipts/indexes as supporting evidence.

Decision
- `status` is the primary operator surface for recent topics and recent source ingests.
- `recent_topics` should use the same page timestamp rollup already reflected in `recent-changes.md`.
- `recent_source_ingests` should use save-receipt `created_at`, with receipt-linked source records as drilldown.

Consequences
- The operator gets one obvious place to answer “what changed recently?” without date-globbing.
- Existing receipts and indexes remain useful evidence, but they stop being competing discovery surfaces.

Follow-ups
- Phase 3 should implement the fields, and Phase 4 should align the docs and recent-index wording with that same story.

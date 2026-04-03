---
title: "Fleki - Eliminate Heuristic Retrieval And Scripted Guesswork - Architecture Plan"
date: 2026-04-03
status: complete
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: phased_refactor
related:
  - /Users/agents/workspace/fleki/AGENTS.md
  - /Users/agents/workspace/fleki/README.md
  - /Users/agents/workspace/fleki/src/knowledge_graph/repository.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/text.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/ids.py
  - /Users/agents/workspace/fleki/skills/knowledge/SKILL.md
  - /Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md
  - /Users/agents/workspace/fleki/tests/test_search_trace_status.py
  - /Users/agents/workspace/fleki/tests/test_cli.py
---

# TL;DR

- **Outcome:** Fleki stops doing semantic interpretation in code. The app stores facts, resolves exact references, exposes where knowledge lives on disk, and lets the agent inspect meaning instead of guessing it in Python.
- **Problem:** The current runtime tokenizes text, strips stopwords, scores phrases and tokens, picks "best" sections, rescues free-text `trace` queries with heuristic matching, and guesses source families from substrings and file suffixes. The skill docs also drift toward sounding like a best-effort retriever instead of a guide to the on-disk graph. That is brittle harness work that conflicts with an agentic stack.
- **Approach:** Remove heuristic retrieval and guess-routing from the runtime, keep only exact ids, exact paths, exact section aliases, explicit schema validation, deterministic storage, and honest failures, and update `AGENTS.md` plus skill docs so future contributors are told plainly that the skill explains layout and navigation but never performs lexical or fuzzy reasoning in app code.
- **Plan:** First lock the repo doctrine and the skill contract in docs: explain the resolved external data root, where topics, provenance, sources, assets, receipts, optional search support state, and render artifacts live, and how to navigate them exactly. Then remove the heuristic `search` and `trace` code paths, replace substring family guessing with explicit normalized data, and update tests around exact resolution plus literal discovery. Then regenerate the bundled runtime and finish the repo-owned docs/install surface.
- **Non-negotiables:**
  - No tokenization, stopword filtering, phrase scoring, lexical ranking, "best match," or fuzzy section selection anywhere in the runtime.
  - No substring or suffix guess-routing where an explicit schema field or exact reference should exist.
  - The skill may explain the graph layout and inspection path, but it may not become a retriever machine, vectorized or otherwise.
  - No compatibility path that keeps the old heuristic behavior alive "just in case."
  - If the app cannot resolve an exact reference honestly, it must fail cleanly or return plain candidates. It must not invent the answer.
  - `AGENTS.md`, skill docs, runtime docs, and code must all say the same thing about this rule.

<!-- arch_skill:block:implementation_audit:start -->
# Implementation Audit (authoritative)
Date: 2026-04-03
Verdict (code): COMPLETE
Manual QA: n/a (non-blocking)

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
external_research_grounding: not started
deep_dive_pass_2: not started
recommended_flow: deep dive -> external research grounding -> deep dive again -> phase plan -> implement
note: This is a warn-first checklist only. It should not hard-block execution.
-->
<!-- arch_skill:block:planning_passes:end -->

# 0) Holistic North Star

## 0.1 The claim (falsifiable)
> If Fleki removes heuristic semantic resolution from runtime code, keeps only exact references, explicit schemas, deterministic candidate listing, and provenance plumbing, and teaches the skill to explain the on-disk graph instead of imitating a retriever, then `search` and `trace` will become predictable, the agent will use the graph as evidence instead of as a mini reasoning engine, and the repo will have a permanent rule that forbids reintroducing lexical guesswork.

## 0.2 In scope
- UX surfaces (what users will see change):
  - `knowledge search` returns deterministic candidate pages and exact refs without hidden semantic ranking.
  - `knowledge trace` accepts exact `knowledge_id`, exact `current_path`, and approved exact section forms such as `current_path#section_alias`, and otherwise fails cleanly.
  - Skill and runtime docs tell agents that the live graph resolves under the external data root, not the checked-in repo copy, how to move from topic page to provenance note to source record to render artifact, and how to use `search` for discovery and `trace` for exact inspection.
  - Skill and runtime docs do not promise free-text claim resolution, semantic rescue, or retriever-like behavior from the app.
  - Repo-local `AGENTS.md` says plainly that heuristic retrieval, scripted semantic reasoning, and bespoke harness work are forbidden when the agent can inspect candidates directly.
- Technical scope (what code/docs/packaging will change):
  - Remove tokenization, stopword, scoring, best-match, and claim-text narrowing logic from `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`.
  - Remove now-dead retrieval helpers from `/Users/agents/workspace/fleki/src/knowledge_graph/text.py`.
  - Replace substring-based `source_kind` family guessing with explicit normalized data at one owner boundary.
  - Tighten CLI, docs, and tests around exact ref resolution, literal discovery behavior, clean failures, and explicit on-disk navigation guidance across `topics/`, `provenance/`, `sources/`, `assets/`, `receipts/`, and `search/`.
  - Regenerate `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` from source after the repo change.

## 0.3 Out of scope
- UX surfaces (what users must NOT see change):
  - A new search backend, assistant service, or hidden retrieval subsystem.
  - A vectorized retriever, ranking service, or semantic retrieval layer under a different name.
  - A product redesign beyond the existing `knowledge save/search/trace/status/rebuild` verbs.
  - A second operator tool whose job is to "fix" missing reasoning in the main runtime.
- Technical scope (explicit exclusions):
  - Embeddings, vector search, rerankers, synonym expansion, or query-understanding pipelines.
  - Replacing the on-disk graph model or provenance/page/source layering.
  - Broad packaging or naming redesign unrelated to the doctrine change.
  - Keeping a compatibility switch that preserves heuristic behavior after the exact cutover.

## 0.4 Definition of done (acceptance evidence)
- No repo-owned runtime path performs semantic tokenization or lexical scoring to infer what a free-text query "probably means."
- `knowledge trace` resolves exact refs and exact section aliases only, or fails with a clear error.
- `knowledge search` returns exact or literal candidates, or an explicit no-hit result. It does not manufacture one semantically "best" answer.
- Source family handling is explicit, exact, and inspectable.
- The skill docs tell an agent where each knowledge artifact family lives under the resolved data root and how to navigate the evidence chain without guessing.
- `/Users/agents/workspace/fleki/AGENTS.md`, `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`, and `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md` all state the no-heuristics rule in plain English.
- Smallest credible evidence for this plan:
  - targeted tests for exact ref resolution, exact section alias resolution, literal search and no-hit behavior, and explicit source-family handling
  - one CLI smoke flow that saves a topic, searches for it, and traces the returned exact ref
  - one doc diff that removes the "best-effort claim text" promise and adds the repo ban

## 0.5 Key invariants (fix immediately if violated)
- The agent does meaning. Fleki stores facts, lists candidates, and follows exact references.
- The skill teaches exact navigation of the on-disk graph. It does not do retrieval magic.
- No hidden lexical heuristics or silent query reinterpretation.
- Ambiguity must surface as ambiguity. The runtime must not choose silently.
- Exact ids, exact paths, explicit aliases, explicit enums, and deterministic serialization are allowed and should be preferred.
- If a convenience layer can drift from ground truth, remove it instead of hardening it.
- The repo doctrine must forbid future reintroduction of heuristic reasoning.

# 1) Key Design Considerations (what matters most)

## 1.1 Priorities (ranked)
1. Remove runtime semantic guesswork completely.
2. Make failures honest, exact, and inspectable.
3. Keep the operator flow usable without inventing a new harness.
4. Make the skill a high-signal map of the on-disk graph for agents.
5. Keep code, skill docs, runtime docs, and `AGENTS.md` aligned.
6. Minimize new abstraction while deleting the old heuristic helpers in the same change.

## 1.2 Constraints
- The save path and the on-disk graph contract should stay intact.
- The bundled skill runtime under `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` must be regenerated from the source repo once the source changes.
- Tests should reuse the current unittest and temp-root patterns. Do not add a new harness just to prove the doctrine change.
- The change must cut over cleanly. No dual path that keeps both heuristic and exact resolution alive.
- The skill should become more concrete about file layout and navigation, not more clever about interpreting user intent.

## 1.3 Architectural principles (rules we will enforce)
- Exact lookup beats approximate lookup.
- Explicit schema beats inferred routing.
- Candidate listing beats silent selection.
- Agent reasoning beats repository heuristics.
- Navigation guidance beats scripted retrieval logic.
- Delete dead helper code in the same change that removes its last caller.

## 1.4 Known tradeoffs (explicit)
- Free-text trace convenience will disappear or be sharply reduced.
- Agents may need one more read step after search because the app will stop pretending to understand the claim for them.
- The skill docs will become more operational and file-layout-oriented, which is the right kind of convenience.
- Search recall may narrow, but trust in the returned result will increase.

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` `search()` tokenizes the query, scores page content, and emits a generated `trace_ref` for the highest-scoring section.
- `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` `trace()` falls back from exact refs into tokenized claim-text matching and supporting-provenance rescoring.
- `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` exposes `tokenize()`, which exists primarily to support retrieval heuristics.
- `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` `_source_family()` and `_manifest_source_family()` guess source family from substrings and suffixes.
- `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` still promises best-effort claim-text narrowing instead of behaving like a map to the actual on-disk graph.

## 2.2 What’s broken / missing (concrete)
- Short, obvious claims can fail unpredictably while longer sentences sometimes work. That is worse than an honest failure.
- Trace can return hollow or duplicated provenance because part of the path is exact lookup and part is heuristic narrowing.
- Search and trace hide important behavior behind scoring code instead of making the contract explicit to the agent.
- The top-level docs currently under-teach the runtime layout: the live graph is the resolved external data root, the runtime has six top-level directories, and the checked-in `knowledge/` tree is easy to mistake for the active graph even though it is legacy or reference state from the runtime's point of view.
- The repo has no standing doctrine in `AGENTS.md` that says heuristic semantic logic is banned, so contributors can keep adding clever little retrieval helpers instead of strengthening exact navigation.

## 2.3 Constraints implied by the problem
- Keep deterministic exact ref resolution for `knowledge_id`, `current_path`, and approved section aliases.
- Preserve the source record -> provenance note -> semantic page inspection chain.
- Replace guessy source-family routing with explicit normalized data or strict exact translation at one boundary.
- Do not ship a compatibility toggle that keeps the old path alive.

<!-- arch_skill:block:research_grounding:start -->
# 3) Research Grounding (external + internal “ground truth”)

## 3.1 External anchors (papers, systems, prior art)
- None adopted in this pass.
- This is a repo-doctrine correction, not a search-technology selection exercise.
- If later research is needed, it should focus on deterministic lookup UX, explicit-reference design, and navigation affordances for agents. It should not turn into a search for a smarter retriever.

## 3.2 Internal ground truth (code as spec)
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py`
    - `default_root()`, `default_data_root()`, and `resolve_knowledge_layout()` define the real machine-wide home under `$HOME/.fleki`, install-manifest precedence, and strict absolute-path normalization. This is the source of truth for where the graph lives on disk.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `KnowledgeRepository.__init__()` and `initialize_layout()` define the canonical tree roots the skill should teach directly: `topics/`, `provenance/`, `sources/`, `assets/`, `receipts/{save,search,trace,rebuild,status}`, and `search/`.
  - `/Users/agents/workspace/fleki/README.md`
    - `How data is stored` already describes the centralized mutable graph under `$HOME/.fleki/knowledge`, the artifact families, and the PDF render bundle chain. This is the current human-facing explanation of the live graph layout.
  - `/Users/agents/workspace/fleki/knowledge/README.md`
    - Names the artifact families, but it currently describes the checked-in repo tree as canonical without distinguishing it from the active resolved data root.
  - `/Users/agents/workspace/fleki/knowledge/topics/README.md`
    - Declares `topics/` as the primary semantic page surface.
  - `/Users/agents/workspace/fleki/knowledge/provenance/README.md`
    - Declares provenance notes as the explanation layer for what each source contributed and which semantic sections it supports.
  - `/Users/agents/workspace/fleki/knowledge/sources/README.md`
    - Declares `sources/` as traceability and recompilation support, not the primary browsing surface.
  - `/Users/agents/workspace/fleki/knowledge/assets/README.md`
    - Declares `assets/` as the derived-artifact bucket referenced by provenance or topic pages.
  - `/Users/agents/workspace/fleki/knowledge/search/README.md`
    - Declares `search/` as approval-gated support state only and explicitly says the core graph must remain readable and useful without hidden search machinery. This is direct repo evidence for the anti-retriever rule.
  - `/Users/agents/workspace/fleki/knowledge/receipts/README.md`
    - Declares receipts as append-only records of what each command did.
  - `/Users/agents/workspace/fleki/skills/knowledge/install/README.md` and `/Users/agents/workspace/fleki/skills/knowledge/runtime/README.md`
    - Already teach the centralized `~/.fleki` layout and the fact that install or refresh does not clear an existing graph. This is the right install-facing anchor to keep aligned with the skill.
  - `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`
    - The early non-negotiables already say local file access and native reasoning come first, but the `knowledge trace` section still promises best-effort claim narrowing. The skill currently mixes the right doctrine with the wrong retrieval promise.
  - `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md`
    - Still advertises best-effort claim-text trace and ranking-centric search language. This is the clearest doc/runtime drift to remove.
  - `/Users/agents/workspace/fleki/skills/knowledge/references/storage-and-authority.md`
    - Still teaches repo-relative storage layers and omits `assets/` and `search/`, so it under-describes the real runtime tree the skill should navigate.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `search()`, `_score_page()`, `_best_content_match()`, `_match_query_parts()`, `_text_match_details()`, `_is_eligible_text_match()`, `_text_match_score()`, and `_filter_support_for_claim()` are the concrete heuristic retrieval stack to remove.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/text.py`
    - `tokenize()` exists to feed the retrieval heuristics. If no exact-navigation path still needs it, it should disappear with the heuristic cutover.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - Exact routing already exists and should be preserved: direct `knowledge_id` lookup, exact `current_path` and stored `aliases`, emitted `trace_ref` values, stored `section_id` values, and explicit `supersedes` to `replacement_paths` mapping.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/ids.py`
    - `section_key()` is the current deterministic section-alias mechanism. It is the right general boundary to preserve, but its slugified form is lossy and may need explicit collision policy.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `_source_family()` and `_manifest_source_family()` still guess by substring and suffix. This is the remaining schema-ownership drift outside the search/trace scorer itself.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`
    - The current CLI already exposes a good exact-navigation backbone: `search` returns `trace_ref`, `trace` prints `current_path`, `matched_heading`, `matched_snippet`, provenance count, and source-record count, and miss behavior already fails cleanly.
  - `/Users/agents/workspace/fleki/tests/common.py`
    - `make_temp_repo()` is the right temp-root harness for future verification. It already exercises real layout resolution and install-manifest wiring without needing a new harness.
  - `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`
    - The test file already covers save -> search -> trace flows, zero-result search, trace-not-found behavior, render-chain tracing, and superseded-page ranking. It is the right place to rewrite expectations away from fuzzy matching and toward exact navigation.
  - `/Users/agents/workspace/fleki/tests/test_cli.py`
    - The CLI tests already verify help text, parseable JSON output, root resolution, and no-traceback failures. They are the right contract surface for doc/help wording changes after the heuristic cutover.
- Existing patterns to reuse:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py`
    - Strict install-manifest and absolute-path resolution is already a good exact-state pattern. Reuse it rather than adding more inferred routing.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - Exact page routing through `knowledge_id`, `current_path`, and stored `aliases` already exists.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - Exact section routing through stored `section_id` values and emitted `trace_ref` values already exists.
  - `/Users/agents/workspace/fleki/README.md` plus `/Users/agents/workspace/fleki/knowledge/*.md`
    - The repo already has the raw material for a skill that teaches the graph tree and the evidence chain. Reuse and tighten this material instead of inventing a new explanatory layer, but make the resolved external data root explicit and reconcile the repo-tree wording.
  - `/Users/agents/workspace/fleki/tests/common.py` plus `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` plus `/Users/agents/workspace/fleki/tests/test_cli.py`
    - The repo already has a good temp-root unittest pattern and CLI output assertions. Reuse them instead of introducing a bespoke verification harness.

## 3.3 Open questions from research
- No material research blockers remain for the exact-navigation cutover.
- Remaining uncertainty is implementation sequencing, not architecture:
  - whether checked-in receipt exemplars are regenerated after the cutover or explicitly marked as pre-cutover historical artifacts
  - whether the one-shot `source_family` repair lands as a dedicated repo maintenance script or another clearly named repo-owned repair entrypoint
<!-- arch_skill:block:research_grounding:end -->

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
- The live mutable graph resolves under the external data root from `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py`, defaulting to `$HOME/.fleki/knowledge` unless an install manifest overrides it.
- The runtime initializes six top-level graph directories under that resolved root:
  - `topics/`
  - `provenance/`
  - `sources/`
  - `assets/`
  - `receipts/`
  - `search/`
- `topics/indexes/**` is generated by rebuild/index refresh logic and is part of the live graph tree.
- The checked-in repo `knowledge/**` tree is currently a mixed role:
  - checked-in reference/exemplar content
  - legacy migration source for older installs
  - misleadingly described in one README as canonical live graph state
- `topics/indexes/**` and `search/` are support artifacts today, not runtime dependencies for `knowledge search` or `knowledge trace`.
- Runtime code lives under `/Users/agents/workspace/fleki/src/knowledge_graph/**`.
- Human-edited skill and reference docs live under `/Users/agents/workspace/fleki/skills/knowledge/**`.
- The bundled runtime mirror under `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` is generated from repo source through `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py`.

## 4.2 Control paths (runtime)
- `knowledge save`
  - `src/knowledge_graph/cli.py` parses bindings and decision JSON, builds `SourceBinding` objects, resolves the live layout, and calls `KnowledgeRepository.apply_save()`.
  - `apply_save()` stages source records first, guesses `source_family` in `_source_family()`, copies or pointers raw sources, renders PDF bundles as a fail-loud boundary, writes provenance notes, writes semantic topic pages, then writes the save receipt.
  - Topic-page writes assign or reuse `knowledge_id`, `section_id`, `current_path`, `aliases`, `section_support`, `section_temporal`, lifecycle, authority posture, and `supersedes`.
- `knowledge search`
  - `repository.search()` tokenizes the query, loads all topics, scores each page through `_score_page()` and `_best_content_match()`, sorts by score plus authority/lifecycle/freshness, and emits a generated `trace_ref`.
  - Search ranking is repo-owned heuristic logic, not explicit graph navigation.
  - Search reads live topic and provenance files directly. It does not depend on `search/` or `topics/indexes/**`.
- `knowledge trace`
  - `repository.trace()` first attempts exact `knowledge_id` and exact path-alias resolution in `_resolve_trace_target()`.
  - If the ref has no `/` and did not resolve exactly, trace falls back to heuristic page matching across the whole graph.
  - If that fallback succeeds, `_filter_support_for_claim()` heuristically rescoring locator text, notes, and full provenance bodies narrows the evidence set again before source records and PDF render artifacts are loaded.
  - If a fragment is present, current public trace resolution does not map a human section alias back to `section_id`. It only works reliably when the fragment is already the stored `section_id`.
- `knowledge status`
  - `repository.status()` computes graph state from saved receipts, pages, manifests, and render contracts. It is primarily a root/counter/queue/readiness view, not a retrieval path.
- `knowledge rebuild`
  - `repository.apply_rebuild()` and `_apply_page_update()` own path renames, alias preservation, supersession links, lifecycle changes, deletes, and index refresh.

## 4.3 Object model + key abstractions
- `SourceBinding`
  - Current save input fields are `source_id`, `local_path`, `source_kind`, `authority_tier`, `sensitivity`, `preserve_mode`, `timestamp`, and `notes`.
  - There is no explicit `source_family` field in the input contract today.
- Source-record manifests
  - Persist `source_family`, but that field is computed heuristically from `source_kind` substrings and file suffixes rather than written from an explicit single-writer contract.
  - Persist `captured_at` and optional `source_observed_at` separately.
- Topic pages
  - Durable page identity is `knowledge_id`.
  - Mutable human routing uses `current_path` plus `aliases`.
  - Durable section identity is `section_id`.
  - Alias metadata exists through `section_ids[section_key(heading)]`, but public trace resolution does not yet honor `#section_alias` fragments.
  - Support and freshness live in `section_support` and `section_temporal`.
- Traceability chain
  - `trace_ref` is already emitted as the machine ref `knowledge_id#section_id`.
  - Provenance notes point to source-record manifests.
  - PDF source records point to render manifests, render markdown, asset paths, or omission reasons.

## 4.4 Observability + failure behavior today
- The PDF render boundary already fails loudly for eligible copied PDFs. This is one of the cleaner existing hard-boundary patterns.
- Invalid path-like trace refs fail cleanly, but free-text trace refs can still guess a page or section based on scoring.
- Unknown `#fragment` values can still yield a hollow success payload with `matched_heading=None`, empty matched evidence, and page-level provenance traversal instead of a hard failure.
- Search and trace receipts show outputs, not the chain of heuristic choices that produced them.
- Search human output hides scores, but JSON still carries a scored/ranked result shape.
- Section aliasing is deterministic but not protected against normalization collisions. `section_key()` is lossy and current writes do not fail loudly on alias collision.
- The docs and skill surface overstate the runtime’s semantic helpfulness and understate the live root/layout truth.

## 4.5 UI surfaces (ASCII mockups, if UI work)
- This is a CLI-and-doc contract, not a visual UI.
- Current human-facing surfaces are:
  - `README.md`
  - `skills/knowledge/SKILL.md`
  - `skills/knowledge/references/*.md`
  - CLI help and flat text output in `src/knowledge_graph/cli.py`
  - checked-in `knowledge/**/*.md` reference content that currently teaches parts of the architecture
<!-- arch_skill:block:current_architecture:end -->

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
- The resolved external data root is the single source of truth for the live graph.
- The repo `knowledge/**` tree is treated explicitly as checked-in reference/example content and legacy migration source, not as the live mutable graph.
- `topics/indexes/**` and `search/` are explicitly non-authoritative support artifacts. Runtime correctness for `knowledge search` and `knowledge trace` must never depend on either one.
- The navigation story is standardized across docs:
  - start in `topics/`
  - follow section support into `provenance/`
  - follow source-record manifests into `sources/`
  - inspect PDF render artifacts or omissions adjacent to source records
  - use `receipts/` for append-only command evidence
  - treat `search/` as approval-gated optional support state that must remain unnecessary for correctness
- The generated runtime mirror remains a pure publication artifact regenerated from repo-owned source and docs. It is never edited directly.

## 5.2 Control paths (future)
- `knowledge save`
  - Save remains the write path for source records, provenance, semantic pages, and receipts.
  - `SourceBinding` gains explicit `source_family`.
  - The save path validates and persists `source_family` as authored input. It no longer guesses family from substrings or suffixes.
  - Validated `source_family` owns source storage placement, manifest persistence, provenance-family rollup, and read-side classification.
  - PDF render behavior stays fail-loud and source-adjacent.
- `knowledge search`
  - Search becomes a deterministic discovery surface, not a semantic resolver.
  - Allowed discovery classes:
    - exact `knowledge_id`
    - exact `knowledge_id#section_id`
    - exact `current_path`
    - exact page alias
    - exact `current_path#section_alias`
    - case-insensitive literal substring discovery across:
      - `current_path`
      - stored aliases
      - page title
      - section headings
      - literal section lines
  - Search returns candidate rows with explicit `match_kind`, exact `trace_ref`, and optional literal snippet.
  - Search does not tokenize, stem, drop stopwords, compute scores, or pick a semantically "best" section.
  - Stable ordering is deterministic by match class, then `current_path`, then section identity when needed.
- `knowledge trace`
  - Trace becomes exact-only.
  - Accepted public forms:
    - `knowledge_id`
    - `knowledge_id#section_id`
    - `current_path`
    - exact page alias
    - `current_path#section_alias`
  - `trace_ref` remains the machine form `knowledge_id#section_id` and is the preferred handoff from `search` to `trace`.
  - If a fragment is present, trace resolves it in this exact order: exact stored `section_id`, then exact persisted alias key from page metadata, else fail loudly.
  - Page-level trace is valid only when no fragment is present.
  - If a fragment is present, trace does not fall back to page-level provenance traversal.
  - Human-friendly `section_alias` is convenience only. The durable stable fragment remains `section_id`.
  - `matched_heading`, `matched_snippet`, and `matched_evidence_locators` come from the exact selected section support only.
  - Page-level trace remains valid for page identity and provenance/source traversal, but locator-bearing evidence is only first-class when a section ref is supplied.
  - Unknown refs or unknown section aliases fail loudly.
- `knowledge rebuild`
  - Rebuild remains the owner of rename, alias preservation, supersession, lifecycle changes, delete, and index refresh.
  - Any one-shot data repair needed for the schema cutover, such as backfilling explicit `source_family` on old manifests, happens through one repo-owned repair path, not through a permanent runtime fallback.
- Agent behavior
  - The agent reasons from candidate pages, provenance notes, source records, and render artifacts directly.
  - The skill explains where to look and how to traverse the graph. It does not try to resolve meaning on the agent’s behalf.

## 5.3 Object model + abstractions (future)
- Durable identity remains:
  - page: `knowledge_id`
  - section: `section_id`
  - source: `source_id`
  - provenance: `provenance_id`
- Save contract changes:
  - `source_family` becomes an explicit binding field and persisted manifest field.
  - `source_kind` remains a descriptive subtype. It no longer decides storage family routing.
  - One repo-owned repair path normalizes pre-cutover manifests instead of preserving inferential runtime logic.
- Search contract changes:
  - replace heuristic `score` semantics with explicit `match_kind`
  - keep `trace_ref` as the machine handoff
  - keep `snippet` only as the exact matched literal line or a simple page/section preview, never as a computed "best line"
- Section alias contract:
  - `section_key()` remains the human-friendly alias generator
  - alias generation happens once at write time
  - collisions fail loudly instead of silently reusing or overwriting a normalized key
  - alias keys are convenience refs derived from the current heading only; alias history across heading renames is not in scope
  - `knowledge_id#section_id` is the only stable ref across heading renames
  - human-friendly alias form is convenience only; durable machine trace remains `knowledge_id#section_id`

## 5.4 Invariants and boundaries
- No runtime semantic interpretation in Python.
- No tokenization, stopword removal, score math, or best-match ranking in search or trace.
- No trace fallback from exact ref failure into content guessing.
- No substring or suffix routing for `source_family`.
- `search/` remains optional and empty by default. The graph must stay readable and useful without hidden search machinery.
- `topics/indexes/**` may exist as browse aids, but runtime correctness must not depend on them.
- The resolved external data root is live truth. Repo docs must stop blurring that boundary.
- Runtime source, generated runtime, README, skill docs, storage docs, and `AGENTS.md` must all tell the same exact-navigation story.

## 5.5 UI surfaces (ASCII mockups, if UI work)
- Human CLI output stays flat and simple.
- `knowledge search` human output should add `match_kind=` and keep `trace_ref=` so the handoff stays obvious.
- `knowledge trace` help and docs should describe exact ref forms only.
- `README.md`, `skills/knowledge/SKILL.md`, and `skills/knowledge/references/search-and-trace.md` become the canonical operator explanation of:
  - the live root
  - the six artifact families
  - the exact search/trace contract
  - the page -> provenance -> source -> render inspection path
<!-- arch_skill:block:target_architecture:end -->

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## 6.1 Change map (table)
| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Search heuristic stack | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `search()`, `_score_page()`, `_best_content_match()`, `_match_query_parts()`, `_text_match_details()`, `_is_eligible_text_match()`, `_text_match_score()`, `_search_sort_key()` | Tokenizes input, scores page/title/heading/line matches, then sorts by score plus authority/lifecycle/freshness | Replace with deterministic exact-or-literal candidate discovery and stable `match_kind` ordering | Search must be navigation, not semantic retrieval | Search JSON carries `match_kind` + `trace_ref` and no heuristic score contract | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_cli.py`, `/Users/agents/workspace/fleki/tests/test_rebuild.py` |
| Trace heuristic fallback | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `trace()`, `_resolve_trace_target()`, `_filter_support_for_claim()`, `_section_support_entries()`, `_section_match_fields()` | Exact page refs resolve first, then free-text falls through to page scoring and provenance rescoring; unknown fragments can still degrade into hollow page-level success | Remove claim-text fallback, resolve fragments only from persisted `section_id` or alias metadata, and fail loudly on unknown fragments | Trace must inspect evidence, not infer meaning or silently widen scope | Accepted refs: `knowledge_id`, `knowledge_id#section_id`, `current_path`, page alias, `current_path#section_alias` | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_cli.py` |
| Retrieval helper cleanup | `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` | `tokenize()` | Generic token helper exists to feed retrieval heuristics | Delete if unused after cutover and remove imports/callers | Dead heuristic support should not survive the cutover | No runtime retrieval tokenizer remains | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` |
| Explicit source-family schema | `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py`, `/Users/agents/workspace/fleki/scripts/backfill_pdf_render_contract.py` | `SourceBinding`, `_binding_from_dict()`, `_stage_source_records()`, `_source_family()`, `_manifest_source_family()`, `_provenance_family()` | `source_family` is persisted but guessed from `source_kind` substrings and file suffixes; repair scripts and read-side checks still rely on inferred family behavior | Add explicit `source_family` to the binding/manifest contract, validate it, persist it unchanged, move storage placement and provenance-family rollup onto it, and replace guess-routing with one repo-owned repair path for old manifests | Family routing must be explicit and inspectable | Save bindings require `source_family`; manifest `source_family` is authoritative for storage placement, provenance-family rollup, and read-side classification | `/Users/agents/workspace/fleki/tests/test_source_families.py`, `/Users/agents/workspace/fleki/tests/test_cli.py`, `/Users/agents/workspace/fleki/tests/test_save.py`, `/Users/agents/workspace/fleki/tests/test_contracts.py`, `/Users/agents/workspace/fleki/tests/test_backfill_pdf_render_contract.py`, `/Users/agents/workspace/fleki/tests/test_skill_package.py` |
| Section-alias boundary | `/Users/agents/workspace/fleki/src/knowledge_graph/ids.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `section_key()`, `_apply_topic_actions()`, `_section_match_fields()` | Human alias is implicit through `section_key(heading)` and collisions are not guarded | Keep deterministic alias generation, but fail loudly on per-page alias collisions and resolve aliases only from persisted metadata | Human-friendly refs should be deterministic without hidden content lookup | Convenience ref is `current_path#section_alias`; machine ref stays `knowledge_id#section_id` | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, new alias-collision coverage |
| CLI contract | `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | `_build_parser()`, `_command_search()`, `_command_trace()`, `_command_save()` | Help and output still describe search/trace in fuzzy terms and save does not expose explicit `source_family` | Rewrite help text and flat output to the exact-navigation contract | Human CLI output is part of the public API | `search` prints `match_kind=` and `trace_ref=`; `trace` help teaches exact refs; `save` help teaches explicit `source_family` | `/Users/agents/workspace/fleki/tests/test_cli.py` |
| Repo doctrine | `/Users/agents/workspace/fleki/AGENTS.md` | repo rules | No explicit ban on heuristic semantic logic and no explicit statement that `resolved_data_root` is live truth while repo `knowledge/**` is reference or migration content | Add a permanent no-heuristics rule, anti-retriever rule, resolved-root truth rule, and “skill teaches navigation” rule | Prevent future harness drift and repo-vs-live confusion | Contributors are told plainly not to add fuzzy/scripted semantic logic and not to treat repo `knowledge/**` as the live graph | doc-only |
| Root/operator docs | `/Users/agents/workspace/fleki/README.md`, `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/storage-and-authority.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/examples-and-validation.md` | search/trace, storage, install, navigation, validation examples | Docs blur live root vs repo tree, omit parts of the runtime tree, and promise best-effort claim lookup or ranking-centric behavior | Rewrite docs together to teach the resolved data root, the six artifact families, the exact search/trace contract, and the evidence chain | The skill must be a map to the graph, not a retriever | One consistent operator story across repo docs and skill docs | doc-only |
| Save contract docs/examples | `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/examples/minimal-save-bindings.json`, `/Users/agents/workspace/fleki/skills/knowledge/runtime/README.md`, `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py` | save input examples and generated runtime README | Public save docs and examples still imply `source_kind`-driven family routing | Update the save contract and bundled examples to require explicit `source_family` and remove guess-routing language | Public examples are part of the contract and must not lag behind the schema cutover | Save docs and examples show explicit `source_family` as authored input | doc-only plus generated runtime refresh |
| Checked-in graph docs | `/Users/agents/workspace/fleki/knowledge/README.md`, `/Users/agents/workspace/fleki/knowledge/topics/README.md`, `/Users/agents/workspace/fleki/knowledge/provenance/README.md`, `/Users/agents/workspace/fleki/knowledge/sources/README.md`, `/Users/agents/workspace/fleki/knowledge/assets/README.md`, `/Users/agents/workspace/fleki/knowledge/receipts/README.md`, `/Users/agents/workspace/fleki/knowledge/topics/indexes/README.md`, `/Users/agents/workspace/fleki/knowledge/search/README.md` | graph tree explanations | Checked-in graph docs partly teach layout but currently blur live-vs-repo truth and do not fully align with the runtime tree | Tighten the checked-in reference docs so they explicitly describe their reference role, the live family under `<resolved_data_root>`, and the graph-relative navigation path | Reduce operator confusion about where to inspect real data | Checked-in graph docs support, but do not override, the live-root explanation | doc-only |
| Checked-in receipt exemplars | `/Users/agents/workspace/fleki/knowledge/receipts/**` | search/status/save receipt examples | Repo receipt examples currently expose pre-cutover search `score` fields and other historical shapes that do not match the target contract | Regenerate receipt examples after cutover or mark them explicitly as historical artifacts that do not define the current API | Prevent stale receipt examples from becoming shadow API docs | Checked-in receipt exemplars are either current, regenerated examples or clearly historical | doc-only or generated example refresh |
| Generated runtime + install propagation | `/Users/agents/workspace/fleki/install.sh`, `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py`, `/Users/agents/workspace/fleki/skills/knowledge/install/bootstrap.sh`, `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py`, `/Users/agents/workspace/fleki/skills/knowledge/runtime/**`, `/Users/agents/workspace/fleki/src/knowledge_graph/install_targets.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` | runtime sync, installer, bootstrap, manifest publication, legacy migration, copy/delete refresh | Runtime mirror copies source, renders the bundled README, publishes runtime manifests, migrates older roots, and `sync_tree` deletes target files absent from staged source | Update repo owners first, then regenerate runtime mirror and installer-facing docs through the existing sync path, including legacy-root and installed-skill refresh surfaces | Installed surfaces must match source truth and delete stale mirror files safely | `skills/knowledge/runtime/**` regenerated only from repo owners; installed skill dirs are refresh/delete-capable targets; legacy roots are migrated or removed through named install flows | `/Users/agents/workspace/fleki/tests/test_install_targets.py`, `/Users/agents/workspace/fleki/tests/test_runtime_manifests.py`, `/Users/agents/workspace/fleki/tests/test_layout.py`, `/Users/agents/workspace/fleki/tests/test_skill_package.py` |
| Test contract rewrite | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`, `/Users/agents/workspace/fleki/tests/test_rebuild.py`, `/Users/agents/workspace/fleki/tests/test_source_families.py`, `/Users/agents/workspace/fleki/tests/test_cli.py`, `/Users/agents/workspace/fleki/tests/test_skill_package.py`, `/Users/agents/workspace/fleki/tests/test_backfill_pdf_render_contract.py`, `/Users/agents/workspace/fleki/tests/test_install_targets.py`, `/Users/agents/workspace/fleki/tests/test_runtime_manifests.py`, `/Users/agents/workspace/fleki/tests/test_layout.py`, `/Users/agents/workspace/fleki/tests/test_contracts.py`, `/Users/agents/workspace/fleki/tests/common.py` | search/trace/rebuild/CLI/runtime tests | Several tests currently encode fuzzy claim-text success, best-line snippet selection, score-driven ranking, implicit family routing, repo-`src`-only execution, or only superficial generated-runtime checks | Reuse the temp-root harness and CLI patterns, but rewrite expectations to exact trace, deterministic literal search, explicit source family, generated-runtime parity, clean miss behavior, and real bundled-install verification | Verification must prove the new contract instead of preserving the old one | Temp-root save/search/trace flow stays; fuzzy expectations are deleted; generated-runtime parity and bundle-lane coverage become explicit | all listed files |

## 6.2 Migration notes
- Deprecated APIs (if any):
  - `knowledge trace "<free-text claim>"` as a supported lookup mode
  - search JSON semantics that imply heuristic ranking or `score` as part of the public contract
  - implicit `source_family` derivation from `source_kind` or local file suffix
- Delete list (what must be removed; include superseded shims/parallel paths if any):
  - `RETRIEVAL_STOPWORDS`
  - `_score_page()`
  - `_best_content_match()`
  - `_match_query_parts()`
  - `_text_match_details()`
  - `_is_eligible_text_match()`
  - `_text_match_score()`
  - `_filter_support_for_claim()`
  - `_source_family()` and `_manifest_source_family()` guess-routing
  - `tokenize()` if no non-retrieval caller remains
  - all doc promises of best-effort claim-text trace
- Data repair notes:
  - existing source-record manifests will need one repo-owned backfill or repair path to add/normalize explicit `source_family`
  - any existing section-alias collision found during migration should fail loudly and be repaired intentionally, not silently normalized
  - checked-in receipt exemplars must either be regenerated after the cutover or marked as historical pre-cutover artifacts
  - legacy-root deletion and installed-skill refresh remain part of the existing install and bootstrap flows, not ad hoc manual cleanup

## Pattern Consolidation Sweep (anti-blinders; scoped by plan)
| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| --- | --- | --- | --- | --- |
| Repo doctrine | `/Users/agents/workspace/fleki/AGENTS.md` | explicit no-heuristics / no-retriever rule | prevents future fuzzy helper creep at the repo root | include |
| Skill contract | `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` | teach live-root navigation and exact inspection path | keeps the agent-facing surface aligned with runtime behavior | include |
| Search/trace reference | `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md` | exact search/trace contract with no claim-text rescue | prevents docs from reintroducing fuzzy expectations | include |
| Storage reference | `/Users/agents/workspace/fleki/skills/knowledge/references/storage-and-authority.md` | resolved-root truth + full six-directory layout + explicit source-family schema | keeps storage docs aligned with runtime tree and save contract | include |
| Save/validation references | `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/examples-and-validation.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/examples/minimal-save-bindings.json` | exact save contract and exact search/trace examples | prevents examples from smuggling ranking or implicit family routing back into the public contract | include |
| Root README | `/Users/agents/workspace/fleki/README.md` | one canonical explanation of live root vs repo tree and exact operator flow | prevents top-level user confusion | include |
| Checked-in graph docs | `/Users/agents/workspace/fleki/knowledge/README.md`, `/Users/agents/workspace/fleki/knowledge/topics/README.md`, `/Users/agents/workspace/fleki/knowledge/provenance/README.md`, `/Users/agents/workspace/fleki/knowledge/sources/README.md`, `/Users/agents/workspace/fleki/knowledge/assets/README.md`, `/Users/agents/workspace/fleki/knowledge/receipts/README.md`, `/Users/agents/workspace/fleki/knowledge/topics/indexes/README.md`, `/Users/agents/workspace/fleki/knowledge/search/README.md` | reference-tree wording and navigation hints | prevents repo-tree/live-root ambiguity across every family surface | include |
| Checked-in receipt examples | `/Users/agents/workspace/fleki/knowledge/receipts/**` | current-or-historical labeling for example receipts | prevents stale examples from masquerading as live API docs | include |
| Generated runtime | `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py`, `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` | source-first regeneration only | prevents source/runtime doctrine drift | include |
| Install and runtime publication | `/Users/agents/workspace/fleki/install.sh`, `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py`, `/Users/agents/workspace/fleki/skills/knowledge/install/bootstrap.sh`, `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` | named install owners and legacy-root truth | prevents doctrine drift between repo source, bundle refresh, and installed runtime surfaces | include |
| Test harness | `/Users/agents/workspace/fleki/tests/common.py`, `/Users/agents/workspace/fleki/tests/test_cli.py` | temp-root harness + CLI contract checks | avoids inventing a new verification harness | include |
| Checked-in semantic topic pages | `/Users/agents/workspace/fleki/knowledge/topics/knowledge-system/*.md` | refresh architecture-topic content after runtime/docs cutover | prevents old architecture claims from lingering in exemplar graph content | defer |
| Broader status UX | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | redesign beyond exact root/layout truth | outside this doctrine-driven cutover | exclude |
<!-- arch_skill:block:call_site_audit:end -->

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan (tests optional). No fallbacks/runtime shims - the system must work correctly or fail loudly (delete superseded paths). Prefer programmatic checks per phase; defer manual/UI verification to finalization. Avoid negative-value tests (deletion checks, visual constants, doc-driven gates). Also: document new patterns/gotchas in code comments at the canonical boundary (high leverage, not comment spam).

## Phase 1: Lock doctrine, live-root truth, and public contract
- Status: COMPLETE
- Completed work:
  - Updated `AGENTS.md`, `README.md`, skill refs, and checked-in family READMEs to state that the live graph is `resolved_data_root`, that the repo `knowledge/**` tree is reference content, and that the skill teaches exact navigation instead of retrieval magic.
  - Removed public promises of best-effort claim-text trace and ranking-centric search guidance from the human-edited doctrine surfaces.
- Goal
  - Make every repo-owned human surface say the same thing about Fleki: live truth is `resolved_data_root`, `search` is deterministic candidate discovery, `trace` is exact inspection, and the skill is a map to the graph rather than a retriever.
- Work
  - Update `/Users/agents/workspace/fleki/AGENTS.md` with the hard no-heuristics rule, the anti-retriever rule, and explicit live-root-versus-repo-tree truth.
  - Update `/Users/agents/workspace/fleki/README.md`, `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/search-and-trace.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/storage-and-authority.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md`, and `/Users/agents/workspace/fleki/skills/knowledge/references/examples-and-validation.md` so they remove claim-text rescue, remove ranking-centric language, teach the live graph layout, and show the exact `search` -> `trace_ref` -> `trace` operator path.
  - Update the checked-in family READMEs under `/Users/agents/workspace/fleki/knowledge/**` so they explicitly identify themselves as checked-in reference content and point agents to the live `<resolved_data_root>/<family>/` paths.
  - Decide and document the approved exact ref examples for public use, including `knowledge_id#section_id` as the stable machine ref and `current_path#section_alias` as convenience-only.
  - Decide how checked-in receipt exemplars will be handled during cutover: regenerated as current examples or marked explicitly as historical pre-cutover artifacts.
- Verification (smallest signal)
  - Review the doc diff and confirm no public surface still promises best-effort claim-text trace, hidden ranking, or repo `knowledge/**` as live mutable truth.
  - Confirm the exact ref examples are identical across README, skill docs, and references.
- Docs/comments (propagation; only if needed)
  - Keep exact ref examples and live-root wording identical across `README.md`, `SKILL.md`, and `AGENTS.md`.
- Exit criteria
  - A contributor reading only repo docs can no longer mistake Fleki for a retriever or mistake the checked-in repo tree for the live graph.
- Rollback
  - Revert the docs-only phase as one unit if the doctrine wording is not accepted.

## Phase 2: Cut search and trace to exact navigation
- Status: COMPLETE
- Completed work:
  - Replaced the heuristic read path in `src/knowledge_graph/repository.py` with exact-ref resolution plus deterministic literal candidate listing, and removed tokenization, stopword filtering, lexical scoring, claim-text rescue, and best-match selection.
  - Updated `src/knowledge_graph/cli.py`, `src/knowledge_graph/text.py`, `tests/test_search_trace_status.py`, and `tests/test_cli.py` so the public contract, CLI wording, and regression coverage all match the exact-navigation behavior.
- Goal
  - Remove all heuristic meaning-making from the read path so `search` only lists deterministic candidates and `trace` only follows exact refs.
- Work
  - Replace the heuristic search stack in `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` with deterministic exact-or-literal candidate discovery and `match_kind` output.
  - Remove free-text `trace` fallback and implement exact fragment resolution in this order: stored `section_id`, then persisted alias key, else fail loudly.
  - Make page-level trace valid only when no fragment is present; unknown fragments must not widen into page-level provenance traversal.
  - Make per-page alias collisions fail before write and document that `knowledge_id#section_id` is the only stable ref across heading renames.
  - Update `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` so `search` help/output, `trace` help/output, and JSON payloads match the exact-navigation contract.
  - Delete dead retrieval helpers from `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` once the read path no longer needs them.
- Verification (smallest signal)
  - Run targeted read-path tests with `.venv/bin/python`:
    - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_search_trace_status tests.test_cli -v`
  - Prove one temp-root flow: save a topic, search it, trace the returned `trace_ref`, and confirm arbitrary claim text plus unknown fragments fail cleanly.
- Docs/comments (propagation; only if needed)
  - Add one short comment at the fragment-normalization boundary only if the exact resolution order would otherwise be easy to misuse.
- Exit criteria
  - No runtime read-path code interprets user intent through token scoring, best-match selection, or silent fragment widening.
- Rollback
  - Revert the read-path cutover fully. Do not leave a mixed exact/fuzzy search or trace surface behind.

## Phase 3: Make `source_family` explicit and repair legacy manifests
- Status: COMPLETE
- Completed work:
  - Added authored `source_family` to `SourceBinding`, save-path validation, CLI binding parsing, and the checked-in minimal save example, then removed runtime family routing from `source_kind` substrings and file suffixes.
  - Added the explicit repair entrypoint `scripts/backfill_source_family.py`, updated the PDF render backfill script to fail cleanly without source-family fallback, and rewrote save/schema tests around the exact contract.
- Goal
  - Remove all inferred family routing from the save path, maintenance flows, and read-side classification.
- Work
  - Add explicit `source_family` to `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`, and the persisted manifest contract.
  - Route storage placement, provenance-family rollup, and read-side family classification through validated `source_family` instead of `source_kind` substrings or file suffixes.
  - Replace `_source_family()` and `_manifest_source_family()` inference with one named repo-owned repair entrypoint for pre-cutover manifests.
  - Update the public save contract and examples in `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md`, `/Users/agents/workspace/fleki/skills/knowledge/references/examples/minimal-save-bindings.json`, and the generated runtime README path so new examples show authored `source_family`.
- Verification (smallest signal)
  - Run targeted save/schema tests:
    - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_source_families tests.test_save tests.test_contracts tests.test_backfill_pdf_render_contract tests.test_cli -v`
  - Confirm one legacy-manifest repair flow exists, is named in docs, and leaves no runtime dependence on inferred family routing.
- Docs/comments (propagation; only if needed)
  - Keep the public save example minimal and identical across the human-edited and generated surfaces.
- Exit criteria
  - New saves never infer family from `source_kind` or file suffix, and old manifests have exactly one sanctioned repair path.
- Rollback
  - Revert the schema cutover and repair entrypoint together. Do not leave mixed implicit and explicit family writers.

## Phase 4: Regenerate runtime, refresh reference artifacts, and prove the install surface
- Status: COMPLETE
- Completed work:
  - Regenerated `skills/knowledge/runtime/**` from repo owners, updated the runtime README generator to teach exact search/trace plus authored `source_family`, and refreshed package-level assertions around the new repair entrypoint.
  - Labeled checked-in receipt exemplars as historical reference content, ran source-vs-runtime parity plus install dry-run, fixed the one remaining rebuild test that still assumed fuzzy wording, and closed the full verification suite cleanly.
- Goal
  - Align repo source, generated runtime, install flows, checked-in reference artifacts, and verification receipts with the final exact-only contract.
- Work
  - Regenerate `/Users/agents/workspace/fleki/skills/knowledge/runtime/**` from repo owners and refresh installer/bootstrap/runtime-publication surfaces through the existing sync path.
  - Update or label checked-in receipt exemplars under `/Users/agents/workspace/fleki/knowledge/receipts/**` according to the policy chosen in Phase 1.
  - Refresh any remaining install/runtime docs so no bundled surface implies fuzzy trace, ranking, or inferred `source_family`.
  - Verify generated-runtime parity, one bundled execution lane, and one install-propagation dry-run lane instead of stopping at repo-`src` imports.
  - Run the full touched-surface verification suite and compile check before calling the change complete.
- Verification (smallest signal)
  - Run generated-runtime parity and install/publication checks:
    - `diff -rq src/knowledge_graph skills/knowledge/runtime/src/knowledge_graph`
    - `./install.sh --dry-run`
  - Run bundled/publication-focused tests:
    - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_skill_package tests.test_install_targets tests.test_runtime_manifests tests.test_layout -v`
  - Run the full repo checks required for touched runtime code:
    - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
    - `.venv/bin/python -m compileall src`
- Docs/comments (propagation; only if needed)
  - Keep generated/runtime/install docs short and literal. Do not let generated text become a shadow contract.
- Exit criteria
  - Repo source, generated runtime, install surfaces, checked-in reference artifacts, docs, and tests all tell the same exact-only story.
- Rollback
  - Revert source, generated runtime, docs, and install-surface changes as one unit. Do not publish a bundle that disagrees with repo source.
<!-- arch_skill:block:phase_plan:end -->

# 8) Verification Strategy (common-sense; non-blocking)

## 8.1 Unit tests (contracts)
- Add or update tests for exact page-id lookup, exact path lookup, exact section alias resolution, invalid free-text trace failure, and explicit source-family handling.
- Add parity checks that the generated runtime bundle stays in sync with repo owners and exposes the same contract fields.
- Add CLI contract checks for `search --help`, `trace --help`, search human output (`match_kind`, `trace_ref`, and no `score`), and save-help exposure of explicit `source_family`.
- Do not add proof tests that merely assert deleted heuristic helpers are gone. Trust behavior-level tests.

## 8.2 Integration tests (flows)
- Keep the current temp-root save/search/trace flow and update it to prove the new operator path:
  - save a topic
  - search for it
  - trace the returned exact ref
  - confirm that arbitrary claim text fails cleanly
- Add one generated-runtime parity lane that proves `skills/knowledge/runtime/**` matches repo owners and that sync deletes stale mirror files.
- Add one bundled execution lane that executes the bundled install path or bundled CLI/runtime entrypoint instead of only importing `src/knowledge_graph` directly.
- Add one install-propagation dry-run probe through `./install.sh --dry-run` or the named installer entrypoint so runtime publication and legacy-root refresh stay covered.

## 8.3 E2E / device tests (realistic)
- No device tests are needed.
- If install or runtime docs change in a meaningful way, use the existing dry-run or runtime-sync checks rather than creating a new harness.

# 9) Rollout / Ops / Telemetry

## 9.1 Rollout plan
- Land the doctrine and runtime cutover together, or land the docs-first warning only if the runtime change is explicitly approved as the immediate next step.
- Regenerate the bundled runtime before calling the change complete.
- If source-family ownership changes require artifact repair, run one repo-owned repair path instead of preserving guess logic forever.

## 9.2 Telemetry changes
- No new telemetry subsystem is needed.
- If any receipt field is added, keep it as plain exact-state output such as resolution mode. Do not add heuristic scoring explanation because the scores should no longer exist.

## 9.3 Operational runbook
- Use the existing Fleki verification commands only.
- If runtime packaging changes, run the existing runtime sync path and the installer dry run when relevant.
- Do not build a sidecar harness for rollout confidence.

# 10) Decision Log (append-only)

## 2026-04-03 - Ban heuristic semantic logic in Fleki runtime
- Context
  - Runtime code currently tokenizes and scores text to guess what the user meant in `search` and `trace`, and the docs promise best-effort claim resolution that the runtime does not deliver reliably.
- Options
  - Keep the heuristic path and try to harden it.
  - Replace it with embeddings or a stronger retrieval layer.
  - Remove heuristic reasoning from runtime code and make the agent own semantic judgment.
- Decision
  - Remove heuristic reasoning from the runtime and update repo doctrine so future contributors are told plainly not to add it back.
- Consequences
  - Some convenience behavior disappears, but traceability and trust improve.
  - Search and trace contracts must become more exact and more literal.
  - `AGENTS.md`, skill docs, runtime docs, and tests all need coordinated updates.
- Follow-ups
  - Confirm the approved exact search and trace contract.
  - Confirm where source-family normalization will live.

## 2026-04-03 - Choose deterministic search, exact-only trace, and explicit source family
- Context
  - The deep-dive pass found that exact identities already exist in page frontmatter and manifests, while the brittle behavior comes from the scoring layer, claim-text fallback, and substring-based source-family routing.
- Options
  - Make both `search` and `trace` exact-only.
  - Keep deterministic literal search for discovery, but make `trace` exact-only.
  - Preserve fuzzy search and just tighten the heuristics.
- Decision
  - Keep `search` as deterministic exact-or-literal discovery with explicit `match_kind`, keep `trace` exact-only, preserve `trace_ref` as the machine handoff, and move `source_family` to an explicit binding/manifest field.
- Consequences
  - Search remains useful for navigation without becoming a retriever.
  - Trace becomes narrower but more trustworthy.
  - Save examples, CLI help, source-family tests, and generated-runtime docs all need coordinated updates.
- Follow-ups
  - Define the final public exact ref examples in docs and help text.
  - Add the one-shot manifest repair path for explicit `source_family`.

## 2026-04-03 - Make section aliases convenience-only and support artifacts non-authoritative
- Context
  - The second deep-dive pass found that public trace behavior still blurs unknown fragments with page-level traversal, `section_key()` is a lossy convenience alias rather than a stable identity layer, and support artifacts such as `topics/indexes/**` and `search/` are already non-authoritative in code even though the docs did not say that sharply enough.
- Options
  - Make alias fragments part of a durable alias-history layer.
  - Keep aliases as convenience-only refs derived from the current heading and make `knowledge_id#section_id` the only stable section ref.
  - Keep support artifacts ambiguous and rely on implementation detail.
- Decision
  - Keep aliases as convenience-only refs derived from the current heading, fail loudly on alias collisions, make fragment resolution exact (`section_id` first, then persisted alias key, else fail), and explicitly demote `topics/indexes/**` and `search/` to non-authoritative support artifacts.
- Consequences
  - Human-friendly `current_path#section_alias` stays available, but it is not a stable ref across heading renames.
  - Unknown fragments become honest failures instead of hollow page-level success.
  - Docs, tests, and receipt examples must stop implying that support artifacts define runtime truth.
- Follow-ups
  - Add alias-collision coverage and fragment-failure coverage.
  - Decide whether checked-in receipt exemplars are regenerated or labeled historical during implementation.

## 2026-04-03 - Audit implementation complete with no reopened phases
- Context
  - The implementation pass landed the exact-only search/trace contract, explicit `source_family`, regenerated runtime bundle, and the planned verification receipts. The remaining question was whether the repo state actually matched the plan strongly enough to call complete.
- Options
  - Reopen any phase with missing code work.
  - Leave the plan active pending manual QA.
  - Mark the plan complete if the code-verifiable contract and verification receipts match the target architecture.
- Decision
  - Mark the plan complete. The audited repo state matches the target architecture and call-site audit, no forbidden heuristic or inferred-routing paths remain in the audited runtime surfaces, and no phase needs reopening for missing code work.
- Consequences
  - The canonical plan now reflects reality: code-complete, no reopened phases, and no manual-QA blocker for this CLI/runtime slice.
  - Any future follow-up should be treated as new scope, not unfinished work from this plan.
- Follow-ups
  - None.

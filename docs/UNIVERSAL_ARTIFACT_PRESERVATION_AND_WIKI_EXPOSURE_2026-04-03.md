---
title: "Fleki - Universal Artifact Preservation And Wiki Exposure - Architecture Plan"
date: 2026-04-03
status: complete
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: architectural_change
related:
  - /Users/agents/workspace/fleki/docs/INTERNAL_KNOWLEDGE_REVIEW_WIKI_DAEMON_PLAN_2026-04-03.md
  - /Users/agents/workspace/fleki/src/knowledge_graph/models.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/repository.py
  - /Users/agents/workspace/fleki/skills/knowledge/SKILL.md
  - /Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md
---

# TL;DR

- **Outcome:** Make Fleki always preserve every saved source into a traceable artifact form and make the review wiki always show those artifacts directly under the knowledge they support.
- **Problem:** The current save contract exposes caller-controlled `preserve_mode`, and the current review-wiki direction excludes artifacts from the human browse path by default. That leaves a confusing story where the semantic page is visible but the underlying artifact may feel hidden or optional.
- **Approach:** Hard-cut the save contract to one preservation policy: normal sources are always copied, `secret_pointer_only` sources are always preserved as pointer-backed artifact records, and every saved source always resolves to a valid artifact target. Then make the wiki export render an `Artifacts` section on topic and provenance pages and generate one simple artifact detail page per source from those sections.
- **Plan:** First remove `preserve_mode` from the public save surface and enforce one live preservation rule in the repository. Then make trace and provenance treat artifact references as universal, not optional. Then update the wiki export so knowledge pages read like articles with an `Artifacts` section directly below the semantic content.
- **Non-negotiables:**
  - Every saved source must produce one durable artifact target.
  - `preserve_mode` is deleted from the public save contract and the skill docs.
  - There is no generic caller choice between copy and pointer.
  - Non-secret sources are always copied.
  - `secret_pointer_only` remains allowed, but it must still produce a stable artifact detail page.
  - The wiki must always show artifacts in line with the knowledge, not as a separate hidden trace-only path.
  - The implementation stays minimal: article-level artifact links plus simple artifact detail pages, not a custom preview system.
  - This plan does not add any other feature, operational mode, compatibility mode, preview mode, or management surface beyond what is required to enforce universal artifact preservation and show artifacts directly under the knowledge.
  - No compatibility shim that keeps the old optional save behavior alive.
  - Where this plan conflicts with the older review-wiki daemon plan on artifact visibility, this plan wins until the two docs are folded together.
  - The `skills/knowledge/SKILL.md` text must stay timeless and current-state only. It must not narrate planning steps, migration history, or prior-state behavior.

<!-- arch_skill:block:implementation_audit:start -->
# Implementation Audit (authoritative)
Date: 2026-04-03
Verdict (code): COMPLETE
Manual QA: pending (non-blocking)

## Code blockers (why code is not done)
- none

## Reopened phases (false-complete fixes)
- none

## Missing items (code gaps; evidence-anchored; no tables)
- none

## Non-blocking follow-ups (manual QA / screenshots / human verification)
- Export one topic page, one provenance page, and one artifact detail page for copy, PDF, and `secret_pointer_only` cases and confirm the links read cleanly in a browser.
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
> If Fleki deletes caller-controlled `preserve_mode`, requires every save to leave behind one durable artifact target, and exports those artifact targets directly below the semantic article content in the review wiki, then operators and reviewers on this machine will always be able to move from knowledge to evidence without a second retrieval flow and without carrying split preservation modes in the save contract.

## 0.2 In scope
- UX surfaces:
  - Topic pages in the review wiki show an `Artifacts` section directly below the semantic article content.
  - Provenance pages in the review wiki show the same artifact references for the sources they cover.
  - Each saved source has a stable artifact detail page that a human can open from the wiki.
  - Pointer-backed secret material stays viewable as a policy-aware artifact detail page rather than disappearing from the browse flow.
- Technical scope:
  - Remove `preserve_mode` from the public save contract, skill surface, examples, and CLI parsing.
  - Make repository storage deterministic: copy by default, pointer-backed only for `secret_pointer_only`.
  - Make provenance and trace treat artifact references as universal for every source.
  - Add minimal review-wiki artifact export support so artifact links and artifact detail pages appear under semantic pages.
  - Reuse the existing review-wiki direction rather than introducing a second viewer, second service mode, or alternate artifact-browsing workflow.

## 0.3 Out of scope
- UX surfaces:
  - Rich inline media previews, carousels, or a custom artifact viewer UI in v1.
  - A generic source-browser UI that exposes the whole raw `sources/**` tree.
  - Public internet artifact serving.
- Technical scope:
  - Keeping `preserve_mode` alive as a deprecated compatibility field.
  - Reintroducing generic non-secret pointer mode.
  - A second retrieval or evidence index outside the graph.
  - A large preview system for PDF pages, image thumbnails, or asset galleries in v1.
  - Any new operational mode, artifact-management surface, feature flag, config surface, or alternate browse mode that is not required for the core invariant.

## 0.4 Definition of done (acceptance evidence)
- `knowledge save` no longer accepts or documents `preserve_mode`.
- Every saved source leaves behind one durable artifact target:
  - artifact detail page plus copied file for normal sources
  - artifact detail page plus copied file and render bundle for copied PDFs
  - artifact detail page backed by the preserved pointer record for `secret_pointer_only`
- Provenance metadata always contains enough artifact references for trace and wiki export to render them.
- Review-wiki topic and provenance pages always show an `Artifacts` section when evidence exists.
- Smallest credible evidence:
  - save-contract tests prove `preserve_mode` is rejected
  - repository tests prove copied and secret-pointer flows still preserve valid artifact targets
  - trace tests prove every saved source resolves to artifact references or pointer detail
  - review-wiki exporter tests prove artifact links appear under exported topic and provenance pages

## 0.5 Key invariants (fix immediately if violated)
- Every source has exactly one preservation policy determined by Fleki, not by the caller.
- Every saved source has a durable artifact target.
- `secret_pointer_only` is the only remaining pointer-backed path.
- Topic-first organization stays intact; artifacts support meaning, they do not replace it.
- Review-wiki article pages must lead with knowledge, then show artifacts immediately below.
- Every wiki-facing artifact reference resolves to one generated artifact detail page, even when the underlying preserved artifact is a copied file.
- The wiki feature stays minimal and deterministic; links and simple artifact pages come before previews.
- No extra feature, mode, or operator surface may be introduced unless it is strictly required to preserve one artifact target per source or to show that artifact directly below the knowledge.
- No fallback or runtime shim keeps the old optional preservation surface alive.
- The skill text stays timeless and current-state only. It does not explain planning process, migration steps, or repo history.

# 1) Key Design Considerations (what matters most)

## 1.1 Priorities (ranked)
1. Remove preservation ambiguity from the save contract.
2. Make evidence visibility obvious in the review wiki.
3. Keep secret handling intact without hiding the existence of the source.
4. Ship the smallest possible UI change that solves the problem.

## 1.2 Constraints
- The graph remains the only source of truth.
- Sensitive material cannot silently become raw copied content just to satisfy the UI.
- The current repo already depends on provenance metadata as the bridge between semantic pages and source records.
- The work must stay tightly scoped to contract simplification and direct artifact exposure, not general review-wiki feature growth.

## 1.3 Architectural principles (rules we will enforce)
- One preservation rule, not caller-selected modes.
- Every save yields a durable artifact target.
- Knowledge first, artifacts directly underneath.
- Pointer-backed artifacts are still real artifacts for trace and review purposes.
- One generated artifact detail page per source is the only human-facing artifact abstraction.
- If a proposed addition does not directly serve those four rules, it is out.

## 1.4 Known tradeoffs (explicit)
- v1 favors article-level links to artifact detail pages over inline previews or direct raw-file browsing.
- Secret-backed sources remain non-raw even though the UI will now surface them more consistently.
- Hard-cutting `preserve_mode` is simpler than compatibility, but it requires explicit rejection of old payloads.

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- `SourceBinding` still exposes `preserve_mode` in the core model.
- The repository currently chooses copy vs pointer from caller input plus sensitivity.
- Provenance already stores `source_record_paths` and PDF render metadata.
- The current review-wiki direction explicitly excludes raw artifacts from the human browse path.

## 2.2 What’s broken / missing (concrete)
- The caller-facing save shape implies preservation is optional or negotiable.
- The wiki separates semantic knowledge from the evidence a human naturally expects to open next.
- The artifact story is easy to understand only if you already know to use `trace`.

## 2.3 Constraints implied by the problem
- The fix must simplify both the save contract and the browse experience.
- The fix must preserve secret-handling rules.
- The fix should reuse existing provenance and source-record metadata instead of inventing a second artifact graph.
- The fix must not grow new operational surfaces just because they are convenient during implementation.

<!-- arch_skill:block:research_grounding:start -->
# 3) Research Grounding (external + internal “ground truth”)

## 3.1 External anchors (papers, systems, prior art)
- No new external system should be adopted for preservation policy or artifact exposure in this change.
  - Reject introducing a second storage layer, preview library, or artifact-serving subsystem.
  - Why: the actual ambiguity is in Fleki's own save contract and browse flow, not in missing third-party infrastructure.
- The existing Quartz direction remains sufficient for the human browse layer once artifacts are exported into it.
  - Adopt the existing review-wiki direction as the downstream renderer plan.
  - Why: this change is about what Fleki preserves and exports, not about picking a different site generator.
- Simplicity is itself a design constraint here.
  - Reject any external anchor that adds preview, gallery, or media-management features in v1.
  - Why: those additions broaden the product without removing the core ambiguity the user wants eliminated.

## 3.2 Internal ground truth (code as spec)
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`
    - `SourceBinding` still exposes `preserve_mode`, so preservation choice is currently part of the caller-facing contract.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py`
    - `_binding_from_dict` still accepts `preserve_mode` and defaults it to `"copy"`, so old payload shape is still live at the CLI boundary.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `_stage_source_records` currently branches on `binding.preserve_mode == "pointer"` or `sensitivity == "secret_pointer_only"`, which means preservation policy is partly caller-selected today.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `_persist_provenance_notes` already writes `source_record_paths`, `render_manifest_paths`, `render_paths`, and `render_omissions_by_source`, so the provenance layer already has enough information to drive a universal artifact section.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - `trace()` already walks semantic page -> provenance -> source record -> render manifests/artifacts/omissions, which makes trace the current canonical evidence chain.
  - `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`
    - The skill text still describes preservation in a way that leaves the old optionality alive and still frames artifact visibility as mostly a trace concern.
  - `/Users/agents/workspace/fleki/skills/knowledge/references/save-ingestion.md`
    - The save reference still lacks the simpler invariant that every source must resolve to a durable artifact target.
- Existing patterns to reuse:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - Source record manifests are already the durable artifact-reference bridge. Reuse them instead of inventing a second artifact registry.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`
    - Provenance metadata already aggregates per-source artifact paths. Reuse that metadata instead of recomputing a page-to-artifact index elsewhere.
  - `/Users/agents/workspace/fleki/tests/test_source_families.py`
    - The repo already has a copied-source path and a `secret_pointer_only` path with explicit expectations. Reuse those two policy lanes instead of inventing more.
  - `/Users/agents/workspace/fleki/tests/test_search_trace_status.py`
    - Trace already exposes render omissions and copied PDF render state. Reuse that evidence shape when the wiki starts surfacing artifacts directly.
  - `/Users/agents/workspace/fleki/docs/INTERNAL_KNOWLEDGE_REVIEW_WIKI_DAEMON_PLAN_2026-04-03.md`
    - The review-wiki direction already exists as a plan artifact. Keep that doc aligned with the shipped exporter so artifact visibility and daemon mechanics still tell one story.

## 3.3 Open questions from research
- No blocking research questions remain after the first deep-dive pass.
- Deep-dive resolved the earlier branches this way:
  - one artifact detail page per source manifest is the smallest shape that works for copied files, copied PDFs, and `secret_pointer_only` pointer records without inventing a second browse mode
  - both topic pages and provenance pages should show the `Artifacts` section, because the user wants the evidence immediately below the knowledge and not only on drill-down pages
  - artifact exposure lands in `src/knowledge_graph/review_wiki/` and nowhere else, so the browse path stays single-track instead of spawning a second exporter or sidecar viewer
<!-- arch_skill:block:research_grounding:end -->

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
- The live graph resolves through `ResolvedKnowledgeLayout` and normally lives under `~/.fleki/knowledge`, with sibling `config_root` and `state_root` under `~/.fleki`.
- Inside the live graph:
  - `topics/**` holds semantic pages
  - `provenance/**` holds source-backed notes
  - `sources/<family>/**` holds either copied artifacts or `.pointer.json` files plus a sibling `.record.json` manifest
  - `assets/**` holds auxiliary extracted assets
  - `receipts/**` holds command receipts
  - `search/**` is reserved support state
- The checked-in repo `knowledge/**` tree is reference content and a migration seed, not the live mutable graph.
- This branch now ships `src/knowledge_graph/review_wiki/` with the minimal exporter required by this plan. It does not yet add the daemon or install path from the older review-wiki plan.

## 4.2 Control paths (runtime)
- `knowledge save` currently flows through one path:
  - `cli._binding_from_dict()` parses JSON bindings and still accepts caller-owned `preserve_mode`
  - `KnowledgeRepository.apply_save()` validates bindings and the semantic decision
  - `_stage_source_records()` chooses copy vs pointer
  - `_stage_pdf_render_bundles()` generates render bundles for copied PDFs only
  - `_persist_provenance_notes()` writes note metadata that links provenance to source manifests and PDF render outputs
  - `_apply_topic_actions()` writes topic pages with provenance references
  - `_write_save_receipt()` records what was saved
- `knowledge trace` follows one exact-reference read path:
  - resolve topic or section
  - load linked provenance notes
  - load the source-record manifests named in `source_record_paths`
  - return source records, render manifests, render artifacts, render omissions, and render contract gaps
- There is no shipped wiki export path in this branch. Human artifact inspection today depends on `trace`, direct file inspection under `sources/**`, or manual reading of provenance metadata.

## 4.3 Object model + key abstractions
- `SourceBinding` mixes semantic input with a caller-owned storage choice through `preserve_mode`.
- A source record manifest is the real per-source storage summary. It records `storage_mode`, `relative_path`, `sha256`, timestamps, and PDF render metadata when relevant.
- A provenance note is the page-facing aggregation layer. It already stores `source_record_paths` plus per-source render metadata keyed by `source_id`.
- A PDF render bundle is repository-owned derived evidence. It is created only when the stored source is a copied PDF, not when the source is pointer-backed.

## 4.4 Observability + failure behavior today
- Save fails loudly when the local source path is missing, when the semantic decision is invalid, and when an eligible PDF render bundle is incomplete.
- Validation already forbids caller-authored render metadata in `source_reading_reports` and `provenance_notes`, so render fields are repository-owned today.
- Trace already exposes copied-vs-pointer outcomes indirectly through source manifests, `render_artifacts`, `render_omissions`, and `render_contract_gaps`.
- The weakest part of the current system is not storage durability. It is browseability. A human can trace to evidence, but artifacts are not shown in the primary reading flow.

## 4.5 UI surfaces (ASCII mockups, if UI work)
```text
TODAY

Topic Page
  semantic article
  provenance links

To see artifacts:
  use trace
  inspect source records separately

Provenance Page
  summary
  contribution notes
  source ids

Artifact access today
  copied source -> open under sources/**
  pointer-backed source -> open .pointer.json under sources/**
  copied PDF render -> follow trace fields manually
```
<!-- arch_skill:block:current_architecture:end -->

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
- The live graph roots stay where they are now. `topics/**`, `provenance/**`, `sources/**`, `assets/**`, and `receipts/**` remain canonical storage under `data_root`.
- Non-secret saves always copy the original source into `sources/<family>/**` and always write a sibling `.record.json` manifest.
- `secret_pointer_only` saves always write a `.pointer.json` artifact plus the usual `.record.json` manifest. That pointer artifact is the preserved source for secret material.
- Copied PDFs still write the copied PDF plus the existing render bundle.
- The review-wiki export under `state_root` grows one additional browse area beyond semantic pages:
  - exported topic pages
  - exported provenance pages
  - generated artifact detail pages under `artifacts/**`
  - selectively exported copied files that those artifact pages link to
- The exporter must not publish the entire raw `sources/**` tree. It exports only the copied files actually referenced by generated artifact pages.

## 5.2 Control paths (future)
- `knowledge save` rejects any binding that still includes `preserve_mode`. There is no deprecated field, ignore path, or quiet defaulting.
- Repository storage becomes policy-driven only:
  - if `sensitivity != "secret_pointer_only"`, copy the source
  - if `sensitivity == "secret_pointer_only"`, preserve a pointer-backed artifact record
- `_persist_provenance_notes()` keeps using `source_record_paths` as the universal bridge from knowledge to evidence. No second artifact registry is introduced.
- `trace()` keeps exact-reference semantics and adds one normalized `artifacts_by_source` summary derived from source manifests, so its returned evidence chain always leads to a valid artifact target for every saved source:
  - copied file path for normal sources
  - `.pointer.json` path for `secret_pointer_only`
  - render markdown and related assets as secondary PDF evidence when they exist
- The review-wiki exporter reads topic pages and provenance pages, follows `source_record_paths`, loads the source manifests, and appends an `Artifacts` section directly below the semantic article content.
- Every artifact link in exported topic and provenance pages resolves to one generated artifact detail page. That detail page then links to the copied file or shows the pointer-backed secret record and policy explanation.
- There is no second browse mode, no generic artifact browser, and no extra operator path beyond the existing review-wiki direction.

## 5.3 Object model + abstractions (future)
- `SourceBinding` becomes semantic-only input plus sensitivity. It no longer carries storage choice.
- The source record manifest stays the single source of truth for artifact type and location:
  - `storage_mode` says whether the preserved artifact is a copied original or a pointer record
  - `relative_path` is the primary artifact path in the graph
  - PDF render fields remain repository-owned secondary evidence, not a second preservation mode
- An artifact detail page is presentation only. It is derived from the source manifest and does not become a second artifact database.
- Topic pages remain the primary human surface. Provenance pages remain drill-down. Artifact pages exist only to give one stable human-readable target per source regardless of storage mode.

## 5.4 Invariants and boundaries
- `preserve_mode` is deleted from the live save contract and from the skill docs. Any reintroduction is a regression.
- There is one live preservation policy:
  - copy for non-secret sources
  - pointer-backed artifact for `secret_pointer_only`
- Every saved source must resolve to a valid artifact target without requiring a second retrieval workflow.
- This plan owns artifact preservation and artifact visibility. The older review-wiki daemon plan only owns the downstream daemon/build/service mechanics after it is updated to match this rule.
- Source manifests remain the only canonical bridge from knowledge to artifact storage.
- Review-wiki artifact exposure is selective, page-linked, and derived from source manifests. It is not a raw-source dump.
- The earlier review-wiki daemon plan must adopt this artifact-visible browse model. It may not keep a competing rule that hides artifacts from exported pages.
- No extra feature, preview system, config surface, compatibility branch, or alternate viewer is allowed under this plan.

## 5.5 UI surfaces (ASCII mockups, if UI work)
```text
TARGET

Topic Page
  semantic article
  provenance links
  Artifacts
    - Source A -> Artifact Detail
    - Source B -> Artifact Detail
    - Source C -> Artifact Detail

Provenance Page
  summary
  source contribution
  Artifacts
    - same artifact links as the supporting topic section

Artifact Detail Page
  source id
  source family
  sensitivity
  captured_at / source_observed_at
  primary artifact
    - copied file link
    - or pointer-backed record with policy note
  PDF extras when present
    - render markdown
    - render assets
```
<!-- arch_skill:block:target_architecture:end -->

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## 6.1 Change map (table)

| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| ---- | ---- | ------------------ | ---------------- | --------------- | --- | ------------------ | -------------- |
| Save model | `src/knowledge_graph/models.py` | `SourceBinding` | caller-owned `preserve_mode` keeps storage policy in the public model | delete `preserve_mode` from the dataclass | remove caller storage choice from the contract itself | bindings describe source semantics and sensitivity only | `tests/test_cli.py`, `tests/test_source_families.py`, `tests/test_search_trace_status.py` |
| CLI boundary | `src/knowledge_graph/cli.py` | `_binding_from_dict` | accepts `preserve_mode` and defaults it to `"copy"` | fail loudly if `preserve_mode` is present; stop constructing bindings with it | hard cutover, no silent compatibility lane | binding JSON no longer permits `preserve_mode` | `tests/test_cli.py` |
| Repository save path | `src/knowledge_graph/repository.py` | `apply_save()`, `_stage_source_records()` | storage mode can come from caller field or `secret_pointer_only` | derive storage mode from sensitivity only | one deterministic preservation rule | non-secret sources always copy; `secret_pointer_only` always writes pointer artifact | `tests/test_source_families.py`, `tests/test_save.py` |
| PDF omission logic | `src/knowledge_graph/repository.py` | `_pdf_render_omission_reason()` | can report `disallowed_by_storage_mode` from caller-selected pointer mode | only report pointer-backed omission when policy produced a pointer artifact | keep PDF render behavior aligned with the new storage rule | PDF omission comes from sensitivity-driven pointer storage only | `tests/test_source_families.py`, `tests/test_search_trace_status.py` |
| Provenance bridge | `src/knowledge_graph/repository.py` | `_persist_provenance_notes()` | already stores `source_record_paths`, render paths, and omission info | keep these fields universal and rely on them as the only page-to-artifact bridge | avoid inventing a second artifact registry | provenance always links knowledge to source manifests | `tests/test_save.py`, future exporter tests |
| Trace read path | `src/knowledge_graph/repository.py` | `trace()` | returns source-record paths and PDF render outputs, but artifact visibility is still trace-centric | emit one normalized `artifacts_by_source` summary derived from manifests and keep the existing exact-ref payload | one evidence story for trace and wiki | every traced source resolves to a manifest-backed artifact target through `artifacts_by_source` | `tests/test_search_trace_status.py` |
| Save validation | `src/knowledge_graph/validation.py` | `validate_save_decision()` and surrounding save guards | caller render metadata is forbidden, but caller storage-mode deletion is not enforced at this layer | keep render fields repository-owned and ensure save contract docs/tests align with deleted `preserve_mode` | prevent hidden second contracts from surviving in tests/docs | no caller-owned storage or render control | `tests/test_contracts.py` |
| Skill surface | `skills/knowledge/SKILL.md` | `knowledge save` rules and non-negotiables | describes pointer-level provenance and pointer-only PDF cases in a way that preserves caller-choice language | rewrite to one preservation rule plus one artifact target per source | stop the skill from reintroducing the deleted mode | non-secret copy, `secret_pointer_only` pointer artifact, artifacts visible in wiki | skill package tests if present |
| Save reference | `skills/knowledge/references/save-ingestion.md` | save contract wording | says “preserve the source first” but not the stronger invariant | state that every save leaves one durable artifact target and no caller storage choice exists | make the simplified rule explicit where agents read it | one artifact target per source is mandatory | doc assertions / downstream skill checks |
| Storage reference | `skills/knowledge/references/storage-and-authority.md` | storage wording around raw originals or pointers | still reflects the older optional storage story | rewrite to the policy-driven storage rule and artifact-target invariant | keep all user-facing docs aligned | storage mode is policy outcome, not user option | doc checks if present |
| Runtime mirror | `skills/knowledge/runtime/src/knowledge_graph/models.py` | mirrored `SourceBinding` | generated runtime still mirrors the old field | refresh from source after the source-tree change | avoid split live/runtime behavior | runtime mirror matches source tree exactly | `tests/test_skill_package.py` |
| Runtime mirror | `skills/knowledge/runtime/src/knowledge_graph/cli.py` | mirrored `_binding_from_dict` | generated runtime still accepts `preserve_mode` | refresh from source after CLI cutover | keep installed runtime aligned | runtime binding parser rejects the field too | `tests/test_skill_package.py` |
| Runtime mirror | `skills/knowledge/runtime/src/knowledge_graph/repository.py` | mirrored save and trace paths | generated runtime still branches on caller-selected pointer mode | refresh from source after repository cutover | keep installed runtime aligned | runtime storage path is policy-driven only | `tests/test_skill_package.py` |
| Runtime mirror | `skills/knowledge/runtime/src/knowledge_graph/validation.py`, `scripts/sync_knowledge_runtime.py` | mirrored validation and sync path | generated runtime will lag if source validation changes are not propagated | refresh the generated mirror as part of the same change and verify the sync path still covers it | prevent source/runtime validation drift | installed runtime enforces the same save rules as source | `tests/test_skill_package.py` |
| Review wiki integration | `src/knowledge_graph/review_wiki/exporter.py` | `export_review_wiki()` | exports topic pages, provenance pages, generated artifact pages, and only the linked preserved files | keep artifact-section export and artifact detail generation here, not in a second viewer | keep one implementation path for human browsing | exported topic/provenance pages include `Artifacts`; generated artifact pages derive from manifests | `tests/test_review_wiki_exporter.py` |
| Review wiki plan alignment | `docs/INTERNAL_KNOWLEDGE_REVIEW_WIKI_DAEMON_PLAN_2026-04-03.md` | artifact exclusion rules | older plan explicitly excludes artifacts from the exported review tree | rewrite or fold in the artifact-visible rule before implementation | avoid two docs telling implementers opposite things | one review-wiki story: knowledge first, artifacts directly below | doc update in same change set |
| Existing tests | `tests/test_cli.py`, `tests/test_source_families.py`, `tests/test_search_trace_status.py`, `tests/test_contracts.py`, `tests/test_save.py` | preserve-mode fixtures and artifact expectations | several tests still pass `preserve_mode` explicitly and assume trace-centric artifact discovery | rewrite fixtures to the new save shape and add direct artifact-target assertions | implementation audit needs concrete proof of cutover | tests no longer mention deleted field; artifact target is always asserted | these files themselves |

## 6.2 Migration notes
- Deprecated APIs (if any):
  - none; `preserve_mode` is deleted, not deprecated
- Delete list (what must be removed; include superseded shims/parallel paths if any):
  - `SourceBinding.preserve_mode`
  - CLI examples, fixtures, and docs that send `preserve_mode`
  - repository branches that honor caller-selected generic pointer mode
  - review-wiki text that says artifacts stay outside the exported reading flow
- Existing stored `.pointer.json` and `.record.json` files remain valid artifacts. That is persisted data, not a live caller-selected storage mode.
- Refresh `skills/knowledge/runtime/**` from source with the runtime sync script instead of hand-editing the mirror.
- Artifact-visible pages now land in `src/knowledge_graph/review_wiki/`. Do not create a second exporter or sidecar site builder on top of it.
- Authority note:
  - this doc is authoritative for artifact preservation and artifact visibility
  - if `docs/INTERNAL_KNOWLEDGE_REVIEW_WIKI_DAEMON_PLAN_2026-04-03.md` still says artifacts stay out of exported pages, that older statement is superseded and must be repaired before implementation starts

## Pattern Consolidation Sweep (anti-blinders; scoped by plan)
| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| ---- | ------------- | ---------------- | ---------------------- | ------------------------------------- |
| Save contract | `src/knowledge_graph/models.py`, `src/knowledge_graph/cli.py`, `skills/knowledge/SKILL.md` | no caller-owned storage choice | prevents the deleted mode from surviving in one entry point or doc | include |
| Evidence bridge | `src/knowledge_graph/repository.py::_persist_provenance_notes`, `trace()`, `review_wiki/exporter.py` | source manifests are the only bridge from page to artifact | prevents a second artifact registry or ad hoc page annotations | include |
| PDF evidence | `src/knowledge_graph/repository.py`, `tests/test_search_trace_status.py`, future artifact detail pages | render bundle is secondary evidence only for copied PDFs | prevents render metadata from becoming a second preservation mode or UI branch | include |
| Runtime distribution | `skills/knowledge/runtime/src/knowledge_graph/*`, `scripts/sync_knowledge_runtime.py` | one source tree, one generated mirror | prevents source/runtime behavior drift after contract deletion | include |
| Review wiki planning | `docs/INTERNAL_KNOWLEDGE_REVIEW_WIKI_DAEMON_PLAN_2026-04-03.md` | knowledge-first pages must still show artifacts directly below | prevents plan drift between preservation work and wiki work | include |
| Source browsing | any future artifact UI beyond manifest-derived pages | no generic raw-source browser in this plan | prevents scope growth beyond what the user asked for | exclude |
<!-- arch_skill:block:call_site_audit:end -->

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan (tests optional). No fallbacks/runtime shims - the system must work correctly or fail loudly (delete superseded paths). Prefer programmatic checks per phase; defer manual/UI verification to finalization. Avoid negative-value tests (deletion checks, visual constants, doc-driven gates). Also: document new patterns/gotchas in code comments at the canonical boundary (high leverage, not comment spam).

## Phase 1 — Delete caller-owned preservation mode

* Goal:
  Make the save contract single-path and fail loud before any wiki work begins.
* Status:
  COMPLETE
* Completed work:
  - Deleted `preserve_mode` from the source model, CLI binding parser, and repository storage-policy path.
  - Made the CLI reject legacy `preserve_mode` payloads with a clear validation error.
  - Rewrote the owning skill/storage docs to state the single preservation rule.
  - Refreshed `skills/knowledge/runtime/**` from source.
* Work:
  - Delete `preserve_mode` from `SourceBinding` in source and generated runtime code.
  - Update `cli._binding_from_dict()` to reject any binding that still includes `preserve_mode`.
  - Change repository storage policy and PDF omission logic to derive pointer-vs-copy behavior from `sensitivity` only.
  - Rewrite the live save docs and tests that still mention or send `preserve_mode`, including the skill docs and storage reference.
  - Refresh `skills/knowledge/runtime/**` from source with `scripts/sync_knowledge_runtime.py`.
* Verification (smallest signal):
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_cli tests.test_contracts tests.test_source_families -v`
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_skill_package -v`
* Docs/comments (propagation; only if needed):
  - Add one short code comment at the repository storage-policy branch or helper stating that `sensitivity` alone owns storage mode.
* Exit criteria:
  - No live source or generated runtime code accepts `preserve_mode`.
  - Non-secret saves always copy the source.
  - `secret_pointer_only` saves always preserve a pointer-backed artifact record.
  - User-facing save docs no longer imply caller-owned storage choice.
  - `skills/knowledge/SKILL.md` describes only the current contract and behavior, with no planning-process or history narration.
* Rollback:
  - Revert the whole cutover if any live path still depends on `preserve_mode`; do not ship mixed accept/reject behavior.

## Phase 2 — Normalize the artifact chain in repository reads

* Goal:
  Make every saved source resolve to one manifest-backed artifact summary that both humans and the future exporter can consume.
* Status:
  COMPLETE
* Completed work:
  - Added one manifest-derived artifact summary helper in the repository and kept source manifests as the only artifact bridge.
  - Extended `trace()` with `artifacts_by_source` without changing its exact-ref behavior or removing the existing evidence fields.
  - Added repository tests that prove copied files, copied PDFs, and `secret_pointer_only` sources all resolve to one stable artifact summary.
  - Refreshed the generated runtime repository so the installed skill bundle now exposes the same `artifacts_by_source` trace summary and artifact helper as source.
* Work:
  - Add one repository-owned helper that converts a source manifest into a normalized artifact summary without creating a second registry.
  - Keep `source_record_paths` as the only page-to-artifact bridge and derive everything else from source manifests.
  - Extend `trace()` to emit `artifacts_by_source` while preserving its exact-reference semantics and existing evidence fields.
  - Tighten save and trace behavior so copied files, copied PDFs, and `secret_pointer_only` sources all produce one stable artifact summary.
* Verification (smallest signal):
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_save tests.test_search_trace_status tests.test_source_families -v`
* Docs/comments (propagation; only if needed):
  - Add one short code comment at the manifest-to-artifact helper explaining that source manifests are the single source of truth for artifact presentation.
* Exit criteria:
  - Every saved source resolves to one normalized entry under `artifacts_by_source`.
  - `trace()` exposes enough data for the wiki exporter without re-deriving storage policy elsewhere.
  - No second artifact registry or page annotation scheme has been introduced.
* Rollback:
  - Revert the helper and trace-shape changes together if the normalized artifact summary is incomplete or diverges from source manifests.

## Phase 3 — Export artifact-visible wiki pages and align the older review-wiki plan

* Goal:
  Add the smallest artifact-visible review-wiki export path and leave one consistent plan story behind it.
* Status:
  COMPLETE
* Completed work:
  - Added `src/knowledge_graph/review_wiki/exporter.py` and the package entrypoint for the minimal review-wiki export path.
  - Exported topic pages, provenance pages, generated artifact detail pages, and only the linked preserved files.
  - Added `tests/test_review_wiki_exporter.py` to prove artifact sections, artifact detail pages, and selective file export.
  - Repaired the older review-wiki daemon plan so it no longer contradicts this doc on artifact visibility.
  - Updated the runtime sync path and package test so the generated skill bundle stays aligned on graph behavior without absorbing the review-wiki package.
  - Ran the full repo suite and `compileall`.
* Work:
  - Create `src/knowledge_graph/review_wiki/` if it is still absent, but only with the exporter pieces required by this plan.
  - Export topic and provenance pages with appended `Artifacts` sections that point to generated artifact detail pages.
  - Generate one artifact detail page per source under `artifacts/**` from the normalized manifest-backed artifact summaries.
  - Export only the copied files and PDF render bundle files actually referenced by artifact detail pages; never dump the raw `sources/**` tree.
  - Repair or fold in `docs/INTERNAL_KNOWLEDGE_REVIEW_WIKI_DAEMON_PLAN_2026-04-03.md` so it matches this artifact-visible browse rule before code lands.
  - Refresh the generated runtime if source-package changes require it, then run full repo verification.
* Verification (smallest signal):
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_review_wiki_exporter -v`
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
  - `.venv/bin/python -m compileall src`
* Docs/comments (propagation; only if needed):
  - Add one short code comment at the exporter boundary explaining that artifact detail pages are derived views over source manifests, not a second artifact database.
* Exit criteria:
  - Exported topic and provenance pages include `Artifacts` sections.
  - Every exported artifact link resolves to one generated artifact detail page.
  - Artifact detail pages link to the copied file or preserved pointer record and include PDF render links when present.
  - The exporter excludes unrelated raw sources and receipts.
  - The older review-wiki plan no longer contradicts this doc on artifact visibility.
* Rollback:
  - Remove the incomplete exporter package and keep Phases 1 and 2 only; do not ship half-visible artifact pages or conflicting review-wiki plans.
<!-- arch_skill:block:phase_plan:end -->

# 8) Verification Strategy (common-sense; non-blocking)

- Prefer targeted existing tests while the contract is moving:
  - Phase 1: `tests.test_cli`, `tests.test_contracts`, `tests.test_source_families`, `tests.test_skill_package`
  - Phase 2: `tests.test_save`, `tests.test_search_trace_status`, `tests.test_source_families`
  - Phase 3: new `tests.test_review_wiki_exporter`, then the full suite
- Use the full suite plus `compileall` only after the exporter phase lands, because that is the first point where the end-to-end shape exists.
- Manual finalization can stay short:
  - save one normal file source
  - save one copied PDF
  - save one `secret_pointer_only` source
  - confirm `trace` exposes `artifacts_by_source`
  - open one exported topic page, one provenance page, and one artifact detail page for each storage case
- Explicitly avoid preview-system tests, deletion-only tests, doc inventory gates, or a second harness just for artifact pages.

# 9) Rollout / Ops / Telemetry

- This change should be a hard cutover in the save contract rather than a staged migration.
- The main operator-facing rollout risk is old bindings that still send `preserve_mode`; fail loudly with a clear error.
- Existing stored `.record.json` and `.pointer.json` files remain valid, so there is no graph-data backfill for preserved source artifacts.
- Do not enable artifact-visible review-wiki output until Phases 1 and 2 are complete; the exporter should consume the normalized artifact summary, not duplicate preservation logic.
- Review-wiki ops stay simple if artifact export remains selective and page-driven rather than exposing the entire raw tree.

# 10) Decision Log (append-only)

- 2026-04-03: Created this new plan instead of stretching the existing review-wiki daemon plan. Reason: the real change is not just wiki export polish; it is a save-contract simplification plus a new invariant that every source must have a durable artifact target.
- 2026-04-03: Drafted the North Star around deleting `preserve_mode` entirely. Reason: the user explicitly wants one preservation rule and does not want a compatibility-shaped contract.
- 2026-04-03: Chose links and simple artifact detail pages as the default first version. Reason: the user asked for the smallest elegant solution and explicitly said not to overbuild.
- 2026-04-03: Locked the plan against extra features, extra operational modes, and optional management surfaces. Reason: the user explicitly confirmed the direction and explicitly rejected any additional feature growth beyond universal artifact preservation and direct artifact visibility in the wiki.
- 2026-04-03: Resolved the first deep-dive pass by choosing the source-record manifest as the only artifact bridge and a manifest-derived artifact detail page as the one stable human-facing target. Reason: this keeps copied files, copied PDFs, and `secret_pointer_only` sources on one browse path without inventing a second registry or preview system.
- 2026-04-03: Resolved the browse shape so both topic pages and provenance pages show `Artifacts` directly below the knowledge. Reason: the user explicitly wants the evidence visible in line with the article, not hidden behind trace-only workflows.
- 2026-04-03: Declared that artifact-visible review-wiki work must land in the future `src/knowledge_graph/review_wiki/` package and that the earlier review-wiki daemon plan must be updated to match. Reason: this branch has no shipped review-wiki code yet, so the implementation path must stay single-track instead of spawning a second exporter.
- 2026-04-03: Tightened the artifact UI shape to one generated artifact detail page per source instead of a mix of detail pages and direct links. Reason: one stable human-facing target is simpler, more consistent, and easier to enforce than mixed link behavior.
- 2026-04-03: Sequenced implementation as contract cutover first, normalized trace artifact summaries second, and review-wiki exporter work third. Reason: the exporter should consume one settled repository artifact shape instead of baking preservation logic into the UI layer.
- 2026-04-03: Locked the skill-writing rule to timeless current-state language only. Reason: the user explicitly rejected planning-process exposition, migration narration, and historical commentary inside the skill text.
- 2026-04-03: Kept `review_wiki` out of the generated skill runtime bundle and enforced that in runtime sync and package tests. Reason: the review wiki is an operator feature, while the generated skill bundle should stay focused on the graph CLI runtime.

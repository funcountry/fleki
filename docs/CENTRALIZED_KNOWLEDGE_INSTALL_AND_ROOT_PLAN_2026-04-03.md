---
title: "Fleki - Centralized Knowledge Install And Root Plan - Architecture Plan"
date: 2026-04-03
status: active
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: architectural_change
related:
  - /Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md
  - /Users/agents/workspace/fleki/src/knowledge_graph/repository.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py
  - /Users/agents/workspace/fleki/skills_or_tools/knowledge/SKILL.md
  - /Users/agents/workspace/fleki/tests/test_runtime_manifests.py
  - /Users/agents/workspace/agents/agents/_shared/skills/knowledge
  - /Users/agents/workspace/paperclip_agents/skills/knowledge
---

# TL;DR

- **Outcome:** Package the `knowledge` system once inside Fleki, cut the machine data root over to platform-standard application-data/config locations, and expose a reusable install framework: one managed install, optional operator-provided external discovery roots, optional compatibility links, and one generated worktree compatibility overlay.
- **Problem:** The current implementation proves the shared skill and on-disk graph model, but the earlier install story overreached in two directions. It treated sibling repos as Fleki publication targets, and it assumed one managed skill root would automatically match every runtime. That blurred repo ownership and made runtime support claims too broad.
- **Approach:** Use platform-standard per-user application-data directories for mutable graph state, a small installer-managed manifest for root/config resolution, one Fleki-managed install root for the bundle, explicit operator-provided external discovery roots for Hermes-like runtimes, explicit compatibility targets for Codex-like runtimes, and a stable `fleki/knowledge` key for Paperclip-like managed imports.
- **Plan:** First land the explicit layout/status contract in the core library. Then normalize an installer-native `skills/knowledge` bundle and self-contained local install assets. Then finish the Fleki-owned managed install, compatibility-link, and root cutover work. Then audit the support matrix honestly so Hermes-like and Paperclip-like runtimes are described as compatible, handoff-only, or out of scope based on Fleki-owned behavior alone.
- **Non-negotiables:**
  - There is exactly one canonical knowledge root per host unless an installer-managed override is explicitly configured.
  - Mutable graph data lives in platform-standard app-data locations, not in repo working trees, skill install directories, or runtime publication caches.
  - Reuse existing standardized installer/discovery surfaces where they already exist; do not invent per-agent installers just because multiple runtimes consume the same package.
  - Runtime discovery may be native to each surface, but storage semantics and the resolved graph root must stay shared.
  - Fleki must not write into sibling repos or live runtime homes as part of its ordinary install/update story. Those surfaces are research inputs and downstream adoption targets, not Fleki-owned publication outputs.
  - Hermes, Paperclip, and other external agent configs or repos are off limits in this plan. Fleki must adapt to them or explicitly stop claiming support; it may not require edits there.
  - Hermes-like external-dir runtimes are supported only through operator-provided discovery roots that already belong to that runtime. Fleki must not guess or hardcode one repo-specific path.
  - Root resolution is explicit and deterministic, never inferred from repo cwd, current shell directory, or which agent happened to run first.
  - The public `knowledge` verbs and storage semantics stay shared across runtimes.
  - The shipped install surface must be self-contained and must not depend on ad hoc Python environments, package managers, or undocumented sibling-repo setup.
  - Failure to resolve the canonical root or a required local install target must fail loudly with an actionable fix.

<!-- arch_skill:block:implementation_audit:start -->
# Implementation Audit (authoritative)
Date: 2026-04-03
Verdict (code): NOT COMPLETE
Manual QA: temporary-home installer smoke passed; external-runtime human QA pending (non-blocking)

## Code blockers (why code is not done)
- Final Fleki cleanup of the legacy repo-local graph and dual package-authoring paths is still open.

## Reopened phases (false-complete fixes)
- None. The local Fleki-owned blockers from the previous audit were fixed in this implement pass.

## Resolved in this implement pass
- Fleki now has a reusable install-target model instead of one hardcoded shared skill root.
  - Evidence anchors:
    - `/Users/agents/workspace/fleki/src/knowledge_graph/install_targets.py`
    - `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py`
    - `/Users/agents/workspace/fleki/skills_or_tools/knowledge/install/codex/install.sh`
  - Code reality:
    - Fleki now records one managed install root, optional operator-provided external discovery roots, optional compatibility skill paths, and one generated worktree overlay path.
- Paperclip-like managed imports now have a stable Fleki-owned skill identity.
  - Evidence anchors:
    - `/Users/agents/workspace/fleki/skills_or_tools/knowledge/SKILL.md:1`
    - `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py`
  - Code reality:
    - The bundle now declares `key: fleki/knowledge`, and the Paperclip runtime manifest exposes that canonical skill key.
- The worktree overlay is now modeled honestly as compatibility state, not as the canonical install or data root.
  - Evidence anchors:
    - `/Users/agents/workspace/fleki/skills_or_tools/knowledge/SKILL.md:101`
    - `/Users/agents/workspace/fleki/skills_or_tools/knowledge/install/README.md:7`
    - `/Users/agents/workspace/fleki/tests/test_runtime_manifests.py`

## Missing items (code gaps; evidence-anchored; no tables)
- Final Fleki cleanup is still open after the install-framework repair.
  - Evidence anchors:
    - `/Users/agents/workspace/fleki/knowledge`
    - `/Users/agents/workspace/fleki/skills_or_tools/knowledge/SKILL.md:101`
    - `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md:101`
  - Plan expects:
    - The legacy repo-local graph should be deleted from production use, and the package should collapse from export-first migration to one human-edited path.
  - Code reality:
    - The generic install framework is in place, but the repo-local graph and the `skills_or_tools/knowledge` to `skills/knowledge` migration split still remain.
  - Fix:
    - Finish the remaining Fleki-owned cleanup in Phase 5.

## Non-blocking follow-ups (manual QA / screenshots / human verification)
- Verify that an operator-provided external discovery root works end to end without changing runtime config.
- Verify that the shipped bundle imports cleanly into a managed-import runtime with the stable `fleki/knowledge` key.
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
> If Fleki moves the `knowledge` graph from a repo-relative proof layout to one logical root resolved through platform-standard application-data directories, and if Fleki ships one reusable package plus a Fleki-owned install/root contract without mutating or depending on changes to Hermes or Paperclip configs, then operators will have one place to inspect and back up the graph on disk, Codex can use a real shared install on the host immediately, and Fleki can truthfully state whether the fixed Hermes/Paperclip setups are compatible or out of scope.

## 0.2 In scope
- UX surfaces (what users will see change):
  - One clear answer to "where does the knowledge directory live on this machine?"
  - One standardized install story for the reusable package, with only thin native discovery adapters where a runtime requires them.
  - A self-contained skill package that explains install, update, repair, and ordinary usage without relying on repo memory.
  - Runtime-facing usage that still feels like one shared interface:
    - `knowledge save`
    - `knowledge search`
    - `knowledge trace`
    - `knowledge rebuild`
    - `knowledge status`
  - A visible configured-root story so operators can confirm that multiple surfaces point at the same graph.
- Technical scope (what code/docs/packaging will change):
  - A canonical platform-standard root contract for the knowledge graph.
  - Root-resolution precedence that is explicit and shared across runtimes.
  - A self-contained packaging layout for the `knowledge` skill and its install assets.
  - Explicit compatibility rules for runtime-owned surfaces Fleki does not own, while treating their current configs and repos as fixed inputs.
  - Clear migration rules from the current repo-local `knowledge/**` tree to the centralized root.
- Verification that the Fleki-owned install/cutover path converges on one root locally, plus a clear answer about whether the fixed Hermes/Paperclip setups are compatible or explicitly out of scope.

## 0.3 Out of scope
- UX surfaces (what users must NOT see change):
  - New end-user verbs beyond the existing `knowledge save/search/trace/rebuild/status` contract.
  - A viewer/publishing redesign.
  - A manual multi-step setup ritual that requires remembering hidden repo paths.
- Technical scope (explicit exclusions):
  - Redesigning the semantic knowledge model itself.
  - Multi-host sync, fleet deployment, or networked storage in this pass.
  - Runtime-specific storage forks, separate per-runtime graph roots, or separate per-agent installers for the same package.
  - A daemon, service layer, or retrieval backend introduced just to make install work.
  - Dependency-heavy installers that require non-standard package managers or ambient virtualenv state.
  - Fleki-owned publication into sibling repos or live runtime homes as part of ordinary install/update flow.
  - Any edits to Hermes, Paperclip, or other external agent configs, repos, or vendored runtime code.

## 0.4 Definition of done (acceptance evidence)
- A canonical platform-standard root path is documented and used consistently by supported runtimes.
- The package installs through a standardized shared-skill/discovery surface instead of a repo-workspace mirror being treated as the primary install.
- Fleki-owned surfaces consume the same installed package/root locally, and downstream runtime-owned surfaces have explicit native-adoption contracts without forking the shared contract.
- A same-host Codex smoke shows that `knowledge status` reports the canonical root path and graph counts after install/cutover.
- Hermes and Paperclip have explicit downstream-native adoption contracts that preserve the same root/package model without forking storage semantics.
- The install surface is self-contained enough that a fresh operator can follow the package instructions without missing Python/package-manager dependencies.
- Migration from the current repo-local `knowledge/**` tree to the centralized root is explicit, idempotent, and fail-loud if the root is ambiguous.
- Smallest credible evidence for this plan:
  - contract tests for root resolution and install manifest shape
  - local install/migration/status/search/trace smoke inside Fleki-owned surfaces
  - downstream-native adoption contracts for Hermes and Paperclip

## 0.5 Key invariants (fix immediately if violated)
- There is one canonical knowledge root per host.
- Supported runtimes must all resolve the same root by default.
- Repo cwd is never the deciding factor for canonical root selection.
- Install location and data location are different concerns and must never be collapsed into one path.
- Runtime-native discovery is allowed; runtime-native storage semantics are forbidden.
- The shared `knowledge` skill remains the public interface across runtimes.
- The install/update surface is self-contained and documented inside the package.
- Installer actions must be idempotent and verifiable.
- A runtime either resolves the configured canonical root or fails loudly with repair instructions.
- Migration from repo-local storage must be explicit; no silent dual-write or hidden shadow root is allowed.
- If an override root exists, it must be installer-managed, visible, and singular. Ad hoc per-runtime overrides are not allowed.
- `~/.agents/skills`, workspace `.agents/skills`, `/etc/codex/skills`, plugin caches, and runtime publication mirrors are distribution/discovery locations, not the canonical graph root.
- Sibling repos and live runtime homes are reference inputs or downstream adoption sites. They are not Fleki publication targets.
- Hermes and Paperclip configs and repos are fixed constraints for this plan. Fleki may adapt to them, but it may not require or implement edits there.
- Fallback policy (strict):
  - Default: **NO runtime shims or silent fallback roots**.
  - If an exception is required later, it must be explicitly approved, timeboxed, and recorded in the Decision Log.

# 1) Key Design Considerations (what matters most)

## 1.1 Priorities (ranked)
1. Single-root correctness across runtimes.
2. Reuse standardized installer/discovery surfaces before inventing runtime-specific installers.
3. Self-contained packaging that agents can execute without dependency drift.
4. Simple, explicit operator understanding of install, update, repair, and root location.
5. Minimal disruption to the existing five-verb `knowledge` contract.

## 1.2 Constraints
- The current repo implementation is already real and tested; the plan must build from it rather than replace it with a speculative new backend.
- Codex, Hermes, and Paperclip currently discover skills through different native publication surfaces.
- The sibling `../skills` repo already uses an upstream shared-skill installer to place durable shared skills in `~/.agents/skills`, which is evidence that we do not need a repo-local bespoke installer for this package.
- The existing `KnowledgeRepository` derives its graph path from a supplied root and currently assumes repo-local layout, so centralization will require an explicit root contract rather than documentation alone.
- Same-host behavior matters first; remote/distributed behavior is intentionally deferred.
- The user explicitly wants fully self-contained install behavior, so packaging cannot assume ambient dependency managers or repo-local tribal knowledge.
- The user explicitly clarified that sibling repos are pattern research inputs, not Fleki publication targets. Any Hermes or Paperclip adoption work must be framed as downstream-native follow-through, not as Fleki writing into those repos by default.
- The user explicitly clarified that Hermes and Paperclip configs and repos are off limits. Fleki must adapt to their current behavior or stop claiming support in this plan.

## 1.3 Architectural principles (rules we will enforce)
- Prefer one explicit host-level source of truth over convenience-local repo storage.
- Keep runtime discovery native, but keep runtime behavior and storage contract-shared.
- Put configuration at the boundary and make it inspectable on disk.
- Separate package-install location from mutable graph-data location.
- Prefer a tiny explicit configuration contract over path inference heuristics.
- Keep installation/update actions idempotent and reversible where practical.
- Make the safe path the easy path: agents should not need to improvise commands or discover hidden prerequisites.

## 1.4 Known tradeoffs (explicit)
- A host-level root improves correctness across runtimes, but it reduces the convenience of treating the repo checkout itself as the canonical graph.
- Platform-standard per-OS paths are less uniform to memorize than a single `~/.fleki/...` dotdir, but they align better with existing installer and OS conventions.
- Reusing an existing shared-skill installer reduces new machinery, but it constrains the package to the shapes that installer and documented discovery surfaces already understand.
- Self-contained install assets reduce dependency drift, but they force the package boundary and update flow to be much clearer than the current mirror-only publication approach.

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- The canonical skill source lives at `/Users/agents/workspace/fleki/skills_or_tools/knowledge`.
- The local implementation now has an installer-native bundle at `/Users/agents/workspace/fleki/skills/knowledge`, a generated worktree compatibility overlay at `/Users/agents/workspace/fleki/.agents/skills/knowledge`, and a managed install at `~/.agents/skills/knowledge` plus operator-configured compatibility paths.
- The runtime-manifest layer now exposes managed install roots, operator-provided external discovery roots, compatibility skill paths, a generated worktree overlay path, and a stable Paperclip import key instead of direct sibling-repo publication paths.
- The live knowledge graph in this repo is stored under `/Users/agents/workspace/fleki/knowledge`.
- The sibling shared-skills repo at `../skills` already uses `npx skills add ...` through `scripts/install-global.sh` to install durable shared skills into `~/.agents/skills`, then adds Codex/OpenClaw compatibility links where needed.
- The implementation has already proved same-host graph usage, managed install plus app-data-root cutover, and a self-contained importable bundle. Live activation still depends on whether a runtime already reads a Fleki-owned path, an operator-provided external root, or a runtime-owned import flow.

## 2.2 What’s broken / missing (concrete)
- There is no locked machine-level answer for where the canonical graph should live outside this repo.
- Root selection is still too implicit. A second repo checkout or a runtime launched from a different working directory can plausibly produce another `knowledge/**` tree.
- Installation is publication-oriented rather than package-oriented: mirrors exist, but the operator story for install/update/repair is not yet the primary contract.
- The current plan draft ignored standardized app-data paths and existing shared-skill install surfaces that already solve part of the package-placement problem.
- The current skill package is not yet the whole install story. It tells agents how to use the graph, but not yet how downstream runtime owners should adopt it natively without Fleki reaching into their repos.
- A prior implementation attempt overreached by treating sibling repos as publication targets. That approach was wrong, has been reverted, and must now be explicitly excluded by the plan.

## 2.3 Constraints implied by the problem
- We need a packaging/install design that preserves native runtime discovery instead of bypassing it.
- We should reuse existing shared-skill installer/discovery surfaces where they already exist instead of inventing a new per-agent installer.
- We need one shared root-resolution contract that can be used from Codex, Hermes, and Paperclip without branching storage semantics.
- We need a migration plan that avoids silent data divergence between the repo-local graph and the new canonical host root.

<!-- arch_skill:block:research_grounding:start -->
# 3) Research Grounding (external + internal “ground truth”)

## 3.1 External anchors (papers, systems, prior art)
- XDG Base Directory Specification — adopt platform-standard user data/config/state roots on Linux-like hosts; reject relative-path or cwd-based root resolution; applies because the plan is moving mutable graph data out of repo-local storage.
- Apple File System Programming Guide — adopt `Library/Application Support` for app-managed support data on the current macOS host; reject repo-local or user-visible document locations for canonical graph storage; applies because the current host is macOS.
- OpenAI Codex configuration/skills/plugins docs — adopt documented user/admin skill scopes and config layers as the primary Codex install/discovery surfaces; treat workspace `.agents/skills` as a repo-local authoring overlay and plugin packaging as an optional richer distribution surface; applies because the current Codex path is still workspace-published.

## 3.2 Internal ground truth (code as spec)
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `KnowledgeRepository.__init__` derives `knowledge_root = root / "knowledge"` and every persistence/search/rebuild entry point writes beneath that tree. This is the current SSOT boundary for graph storage semantics.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `initialize_layout()` defines the canonical subtrees `topics/`, `provenance/`, `sources/`, `assets/`, `receipts/`, and `search/`. Any install-layout change must preserve this subtree contract even if the parent root moves.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py` — the manifest helpers hardcode publication targets for the Codex workspace mirror, Hermes shared/trusted skill dirs, and the Paperclip repo-owned skill path. This is the current adapter boundary and the main place where install-surface assumptions are encoded.
  - `/Users/agents/workspace/fleki/tests/common.py` — `make_temp_repo()` constructs `KnowledgeRepository(root)` directly and initializes layout in a temp directory. This proves the core library is already injectable by path and can stay easy to test if root resolution moves to a higher boundary.
  - `/Users/agents/workspace/fleki/tests/test_runtime_manifests.py` — tests currently assert exact repo/workspace/publication strings. These tests will need to move from “repo mirror is the install” to “install-layout and thin adapters are correct.”
  - `/Users/agents/workspace/fleki/tests/test_save.py` and `/Users/agents/workspace/fleki/tests/test_rebuild.py` — tests assert concrete writes under `root/knowledge/**`. This means migration to a platform-standard data root should preserve the subtree contract while changing only how `root` is resolved.
  - `/Users/agents/workspace/fleki/skills_or_tools/knowledge/references/storage-and-authority.md` — identity rules say `knowledge_id`, `section_id`, and `source_id` are durable while paths are mutable aliases. This is the strongest current internal reason the graph can be relocated without changing semantic identity.
  - `/Users/agents/workspace/fleki/.agents/skills/knowledge/SKILL.md` — the skill explicitly prefers mutating canonical graph state through the shared `knowledge` contract or repo-local core library, not by hand-editing `knowledge/**`. This is the package boundary that install changes must preserve.
  - `/Users/agents/workspace/skills/README.md` and `/Users/agents/workspace/skills/scripts/install-global.sh` — existing shared-skill installation already uses `npx skills add ...` into `~/.agents/skills` plus compatibility sync. This is current internal evidence that a standardized shared install surface already exists.
- Existing patterns to reuse:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — boundary-injected root pattern — keep storage semantics in `KnowledgeRepository`, but move root resolution into a separate install-layout resolver.
  - `/Users/agents/workspace/fleki/tests/common.py` — temp-root test injection pattern — preserve direct constructor injection for tests while production code resolves platform-standard roots before instantiation.
  - `/Users/agents/workspace/fleki/skills_or_tools/knowledge/references/storage-and-authority.md` — durable-id / mutable-path pattern — use stable ids to migrate or rehome graph data without semantic churn.
  - `/Users/agents/workspace/skills/scripts/install-global.sh` — shared installer wrapper pattern — prefer a small wrapper over an existing installer surface instead of inventing a new package manager or per-agent bespoke flow.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py` — thin-adapter pattern, but currently hardcoded — keep runtime manifests thin and declarative, with root resolution pulled out of them.
- Likely code implications (plan only; no implementation):
  - Add an install-layout/root-locator layer above `KnowledgeRepository` rather than teaching the repository about OS-specific paths directly.
  - Update runtime manifest schema so it describes shared install surfaces and thin adapters instead of repo mirrors as primary installs.
  - Split tests between storage semantics and install-layout/adapter resolution so path portability is explicit.

## 3.3 Open questions from research
- Should the install-layout resolver live as a tiny library module inside `knowledge_graph` or as a package-level installer boundary above it?
  - Evidence needed: the smallest design that preserves temp-root test injection and keeps OS-specific path logic out of pure storage tests.
- For Paperclip `codex-local`, which runtime-owned injection path is the cleanest replacement for workspace `.agents/skills` once the adapter stops mutating worktrees?
  - Evidence needed: compare managed `CODEX_HOME` injection against any existing Paperclip runtime-owned path that preserves current adapter behavior.
<!-- arch_skill:block:research_grounding:end -->

<!-- arch_skill:block:external_research:start -->
# External Research (best-in-class references; plan-adjacent)

> Goal: anchor the plan in idiomatic, broadly accepted practices where applicable. This section intentionally avoids project-specific internals.

## Topics researched (and why)
- Platform-standard app data/config/state directories — the plan needs one centralized graph root that should not be an ad hoc dotdir if the OS already provides a standard location.
- Codex standardized skill/plugin install and config surfaces — the plan must stop treating repo-workspace mirrors as the main install path if documented user/admin/plugin surfaces already exist.

## Findings + how we apply them

### Platform-standard app data/config/state directories
- Best practices (synthesized):
  - Linux/XDG splits user data, config, state, and cache into separate standard base directories and requires absolute paths.
  - macOS expects app-managed support files to live under `Library`, especially `Application Support`, with an app- or company-specific subdirectory.
  - Mutable support data should not live in user-visible document folders, repo working trees, or transient cache locations.
- Recommended default for this plan:
  - Replace the fixed `~/.fleki/knowledge` draft with a logical knowledge root resolved from platform-standard app-data locations.
  - On the current macOS host, default to `~/Library/Application Support/Fleki/knowledge`.
  - On Linux, default to `${XDG_DATA_HOME:-$HOME/.local/share}/fleki/knowledge`.
  - Keep installer/config metadata in platform-standard config/support locations rather than inside repo state.
- Pitfalls / footguns:
  - Mixing config, state, cache, and canonical graph data into one arbitrary home dotdir.
  - Treating relative environment-variable paths as valid.
  - Making repo cwd or runtime install location determine the graph root.
- Sources:
  - XDG Base Directory Specification — https://specifications.freedesktop.org/basedir-spec/latest/ — authoritative Linux/Unix data/config/state placement rules.
  - Apple File System Programming Guide — https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html — authoritative Apple guidance for `Library` / `Application Support` placement.

### Codex standardized install and discovery surfaces
- Best practices (synthesized):
  - Codex already documents user, admin, system, and repo skill scopes.
  - For reusable distribution, Codex also has a documented plugin model, plugin directory UI/CLI, and standardized config layers.
  - Workspace skill folders are good for repo-local authoring, not the only install surface.
- Recommended default for this plan:
  - Stop treating repo workspace `.agents/skills` mirrors as the primary installed Codex surface.
  - Use documented shared install locations for reusable local skills (`$HOME/.agents/skills` user scope, `/etc/codex/skills` admin scope) or a Codex plugin when we need richer distribution.
  - Keep Codex config in documented config layers, not hidden inside repo-local install scripts.
- Pitfalls / footguns:
  - Coupling reusable install to `$CWD/.agents/skills`.
  - Using runtime discovery directories as the data root for the knowledge graph.
  - Creating separate per-agent copies when documented shared user/admin scopes already exist.
- Sources:
  - Codex Config Basics — https://developers.openai.com/codex/config-basic — authoritative config precedence and standard config paths.
  - Codex Skills — https://developers.openai.com/codex/skills — authoritative skill scope and user/admin skill locations.
  - Codex Plugins — https://developers.openai.com/codex/plugins — authoritative reusable plugin distribution surface.
  - Build plugins — https://developers.openai.com/codex/plugins/build — authoritative local marketplace and install-cache behavior.

## Adopt / Reject summary
- Adopt:
  - Platform-standard app-data roots for canonical graph storage.
  - Standard shared-skill install/discovery surfaces before inventing custom installers.
  - Repo workspace skill folders only as generated worktree overlays, not as the installed production surface.
- Reject:
  - Fixed `~/.fleki/knowledge` as the default cross-platform root.
  - Per-agent install logic when shared user/admin/plugin surfaces already exist.
  - Canonical graph data under repo checkouts, skill install directories, or plugin caches.

## Open questions (ONLY if truly not answerable)
- None that block v1. The deep dive now selects the existing shared-skill installer into user scope; Codex plugin packaging is deferred until a concrete distribution need appears.
<!-- arch_skill:block:external_research:end -->

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
- The current host-local canonical graph is now the app-data root resolved through `install.json`: `/Users/agents/Library/Application Support/Fleki/knowledge/**`.
- The legacy repo-local graph still exists at `/Users/agents/workspace/fleki/knowledge/**` as migration input and rollback material, which is why `legacy_repo_graph_detected` remains visible in `status`.
- The canonical reusable skill source is still repo-scoped at `/Users/agents/workspace/fleki/skills_or_tools/knowledge/**`.
- An installer-native bundle exists at `/Users/agents/workspace/fleki/skills/knowledge/**`.
- A second repo-local copy exists at `/Users/agents/workspace/fleki/.agents/skills/knowledge/**`. It is now intended as a generated worktree compatibility overlay only, never as the canonical install or data root.
- `runtime_manifests.py` now exposes the real Fleki-owned install facts: managed install root, compatibility link targets, operator-provided external discovery roots, generated worktree overlay path, and Paperclip canonical key.
- A separate, already-standardized installer seam exists in the sibling skills repo. `../skills/scripts/install-global.sh` installs skills into `~/.agents/skills`, and `../skills/scripts/sync-codex-skills.sh` then symlinks `${CODEX_HOME:-$HOME/.codex}/skills/<skill>` to that installed source. Fleki now reuses that same upstream seam locally through its own package-local install asset rather than depending on the sibling repo as a publication target.

```text
fleki/
|-- knowledge/                      # legacy repo-local graph after cutover
|-- skills_or_tools/knowledge/      # canonical reusable package source today
|-- skills/knowledge/               # shipped installer-native bundle
`-- .agents/skills/knowledge/       # workspace publication mirror, also treated as contract
```

## 4.2 Control paths (runtime)
- Core library and tests now resolve an explicit layout first, then instantiate `KnowledgeRepository(layout)` or `KnowledgeRepository(data_root)`.
- Codex has two different stories today:
  - managed install through `~/.agents/skills` plus configured compatibility skill paths such as `${CODEX_HOME}/skills/knowledge`
  - repo-local direct use through `.agents/skills/knowledge` as a generated worktree compatibility overlay
  Fleki now proves the managed install path locally and keeps the overlay only as non-canonical runtime compatibility state.
- Hermes-like external-dir runtimes are supported only through operator-provided discovery roots that runtime config already scans.
- Paperclip-like managed-import runtimes are supported only through shipped-bundle import plus runtime-owned materialization; Fleki does not try to replace that with a direct install.
- Ownership is split across repos:
  - Fleki owns storage semantics, the shared package source, the shipped bundle, the managed install/root contract, the generated worktree overlay, and the stable Paperclip key
  - `../skills` is a research/reference pattern for the generalized shared-skill installer seam
  - Hermes owns external-dir discovery configuration
  - Paperclip owns managed import/materialization and Codex adapter behavior

## 4.3 Object model + key abstractions
- `KnowledgeRepository.__init__` is now the main storage seam over explicit layout/data-root inputs. It accepts either a `ResolvedKnowledgeLayout` or a direct `data_root`, then derives:
  - `knowledge_root = data_root`
  - `topics_root`, `provenance_root`, `sources_root`, `assets_root`, `receipts_root`, and `search_root` beneath it
- Path serialization is now graph-relative to the canonical data root. `_relative()` converts paths relative to `self.data_root`, and that behavior flows into:
  - source record manifests
  - provenance notes
  - topic page metadata
  - save/rebuild receipts
  - `search()` and `trace()` payloads
- `runtime_manifests.py` now carries install/layout metadata such as:
  - resolved canonical data root
  - install manifest path
  - managed install root, operator-provided external discovery roots, and compatibility targets
  - adapter mode, worktree overlay path, and Paperclip canonical key
- `repository.status()` now composes graph health with:
  - resolved `data_root`
  - install-manifest presence/path
  - legacy repo-graph detection
  - runtime-manifest agreement on root and manifest path
- The public shared contract lives in `skills_or_tools/knowledge/SKILL.md`, but that package is still usage-oriented. Install, update, repair, and root-location behavior are not yet the authoritative package-local contract.

## 4.4 Observability + failure behavior today
- The current host-local layout is inspectable through the canonical app-data root and `install.json`, which is a real improvement over the original repo-local proof shape.
- Root drift is now visible locally through `knowledge status`, but downstream runtime adoption is still incomplete, so same-root correctness is fully proved only for Fleki-owned local surfaces today.
- Install drift is now detectable for the Fleki-owned local install path through the install manifest and runtime-agreement surface, but live activation still depends on external-dir ownership or runtime-owned imports outside Fleki.
- Paperclip’s `codex-local` docs are already stale relative to code: docs still mention `~/.codex/skills`, while the adapter currently injects into workspace `.agents/skills`. Code wins, which means worktree mutation is the real current behavior.
- Because Fleki now owns layout resolution locally but not downstream runtime adoption, the dominant remaining failure mode is cross-repo ownership drift rather than silent local root inference.

## 4.5 UI surfaces (ASCII mockups, if UI work)
- No UI surface is in scope for this plan.
<!-- arch_skill:block:current_architecture:end -->

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
- The architecture separates three physical concerns:
  - `data_root`: mutable graph data only
  - `config_root`: install manifest and operator-visible configuration
  - `state_root`: optional runtime publication state and repair receipts
- Default host-level roots:
  - macOS current host:
    - `data_root = ~/Library/Application Support/Fleki/knowledge`
    - `config_root = ~/Library/Application Support/Fleki`
    - `state_root = ~/Library/Application Support/Fleki/state`
  - Linux:
    - `data_root = ${XDG_DATA_HOME:-$HOME/.local/share}/fleki/knowledge`
    - `config_root = ${XDG_CONFIG_HOME:-$HOME/.config}/fleki`
    - `state_root = ${XDG_STATE_HOME:-$HOME/.local/state}/fleki`
  - Windows, if later supported:
    - `data_root = %LocalAppData%\\Fleki\\knowledge`
    - `config_root = %LocalAppData%\\Fleki`
    - `state_root = %LocalAppData%\\Fleki\\state`
- `config_root/install.json` becomes the single installer-managed manifest. It records the resolved absolute `data_root`, install metadata, and runtime discovery targets. It may override the default root, but only through this one manifest.
- The graph subtree contract stays exactly the same under `data_root`:

```text
<data_root>/
|-- topics/
|-- provenance/
|-- sources/
|-- assets/
|-- receipts/
`-- search/
```

- The shippable reusable package must exist in an installer-native skill directory shape so all three runtime families can consume the same bundle:

```text
skills/knowledge/
|-- SKILL.md
|-- references/
`-- install/
    |-- codex/
    |-- hermes/
    `-- paperclip/
```

- During migration, `skills_or_tools/knowledge/**` may remain only as a one-way source precursor if phase planning chooses export instead of a direct move. Dual-authoring is forbidden; only one package directory may be edited by humans.
- Installed/discovery surfaces after packaging:
  - canonical managed installed package: `~/.agents/skills/knowledge`
  - compatibility skill paths: explicit full target paths such as `${CODEX_HOME:-$HOME/.codex}/skills/knowledge`
  - external discovery roots: optional operator-provided parent directories already scanned by Hermes-like runtimes
  - managed-import runtimes: shipped bundle plus stable `fleki/knowledge` identity
- Repo-local `knowledge/**` and repo-local `.agents/skills/knowledge/**` become development or migration surfaces only, not authoritative runtime storage or install locations.

## 5.2 Control paths (future)
- One packaging/install pipeline for v1:
  1. Produce one self-contained installer-native `knowledge` bundle.
  2. Install that bundle through the existing shared-skill installer into `~/.agents/skills/knowledge`.
  3. Write or refresh `config_root/install.json` with the resolved absolute `data_root` and runtime discovery metadata.
  4. Expose the same installed bundle through Fleki-owned local surfaces:
     - Codex: compatibility links under configured compatibility skill paths
     - Hermes-like external-dir runtimes: optional links into operator-provided discovery roots
     - worktree-based runtimes: generated `.agents/skills/knowledge` overlay as non-canonical compatibility state
  5. Define truthful compatibility against fixed non-Fleki-owned surfaces:
     - current repo-owned Hermes path on this machine: handoff-only
     - Paperclip company import: handoff-only, but bundle-compatible with stable key
     - Paperclip workspace injection: runtime-owned limitation, not a Fleki install path
  6. Every runtime resolves the same layout before invoking repository operations.
- Root resolution order is explicit and singular:
  - first, an explicitly injected `ResolvedKnowledgeLayout` object for tests or tightly controlled embedded callers
  - otherwise, `config_root/install.json`
  - otherwise, the platform default roots above
  - any relative path, conflicting manifest, or runtime-supplied path mismatch fails loudly
- `KnowledgeRepository` stops being a root-discovery mechanism. It operates on a resolved data-root contract only.
- Codex v1 explicitly uses the existing shared-skill installer plus compatibility sync. Plugin packaging is deferred until there is a real need for richer marketplace/app-integration behavior.
- Hermes-like external-dir runtimes use native discovery only. Fleki may link into operator-provided roots but may not require runtime config to change.
- Paperclip-like runtimes use native managed import/materialization plus a current `codex-local` workspace-injection behavior that is read-only for this plan. Fleki may not require that adapter to change.
- Fleki does not publish into sibling repos as part of this target architecture. Fleki’s responsibility ends at the shipped bundle, the host-local install/root contract, and the downstream call-site handoff contract.
- Direct developer use from a Fleki checkout remains allowed only through explicit dev layout injection or through the installed shared package. Repo cwd is never allowed to decide the canonical data root.

## 5.3 Object model + abstractions (future)
- Add one typed install/layout boundary above the repository, for example:
  - `KnowledgeInstallManifest`
  - `ResolvedKnowledgeLayout`
  - `RuntimeInstallManifest`
- `KnowledgeRepository` should take `data_root` or a resolved layout object, not a generic repo root. Internally, `knowledge_root` becomes the resolved canonical data root rather than `root / "knowledge"`.
- Path fields persisted in records, pages, receipts, search results, and trace results become graph-relative to `data_root`. They must not depend on repo roots, install directories, or workspace overlays.
- `runtime_manifests.py` becomes a discovery/install description layer. It may describe adapter mode, native targets, and compatibility mirrors, but it may not invent storage roots.
- `knowledge status` becomes a composed status surface:
  - graph health from the repository
  - resolved `data_root`
  - `install.json` path
  - runtime discovery/publication agreement or drift
- If receipts carry layout metadata, they carry immutable install snapshots for diagnostics only. Receipts do not become a second configuration source.

## 5.4 Invariants and boundaries
- One host, one canonical `data_root`, one installer-managed manifest.
- Shared-skill install/discovery surfaces are allowed to vary by runtime; shared data semantics are not.
- Install paths and data paths are different classes of path. Writes to install locations are forbidden.
- Workspace `.agents/skills` is a generated worktree compatibility overlay only. It is never the canonical installed package or canonical graph root, even when a runtime still injects there.
- Paperclip managed runtime copies are allowed as adapter caches only. They are not a second authoring source and not a storage backend.
- If both `skills_or_tools/knowledge` and `skills/knowledge` exist during migration, only one is editable. The other must be generated deterministically from it.
- `knowledge/**` under a repo checkout is migration input or test data after cutover, not live canonical state.
- Sibling repos and live runtime homes must adopt the package through their own native change surfaces. Fleki does not push into them directly.
- Hermes and Paperclip are read-only integration constraints here. If compatibility cannot be achieved from Fleki-owned code and packaging alone, this plan must say so explicitly instead of requiring external edits.
- Runtime wrappers may pass resolved layout information, but they may not create ad hoc per-runtime root overrides. Any passed value must match `install.json` or the computed platform default.
- Missing native discovery targets, broken compatibility mirrors, relative manifest paths, or root disagreement fail loudly with repair instructions.

## 5.5 UI surfaces (ASCII mockups, if UI work)
- No UI surface is in scope for this plan.
<!-- arch_skill:block:target_architecture:end -->

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## 6.1 Change map (table)

| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Layout resolution core | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `KnowledgeRepository.__init__`, `initialize_layout`, `_relative` | Treats the supplied root as an enclosing repo/temp root and derives `root/knowledge/**` | Introduce a resolved layout boundary and make repository storage relative to the canonical `data_root` only | Repo cwd and install paths must stop deciding canonical storage | `ResolvedKnowledgeLayout`, `KnowledgeInstallManifest`, `data_root` contract | `tests/common.py`, `tests/test_save.py`, `tests/test_rebuild.py`, `tests/test_search_trace_status.py`, `tests/test_source_families.py` |
| Persistence payloads | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_persist_source_records`, `_persist_provenance_notes`, `_apply_topic_actions`, `_write_save_receipt`, `_write_receipt` | Serializes `relative_path` and receipt fields relative to the enclosing root | Serialize graph-relative paths and optional immutable install snapshots; never persist repo/install-root assumptions as writable truth | Migration and cross-runtime status need portable paths | graph-relative path contract plus optional receipt install snapshot | `tests/test_save.py`, `tests/test_rebuild.py`, `tests/test_source_families.py`, `tests/test_search_trace_status.py` |
| Read/status surface | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `search`, `trace`, `status` | `search` and `trace` emit root-relative path data; `status` reports graph health only | Emit graph-relative paths and compose install/layout agreement into status output | Operators need one command that proves same-root correctness across runtimes | composite `KnowledgeStatus` surface | `tests/test_search_trace_status.py` plus new status contract tests |
| Runtime install/discovery model | `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py` | `_skill_dir`, `_codex_workspace_skill_dir`, `codex_runtime_manifest`, `hermes_runtime_manifest`, `paperclip_runtime_manifest` | Hardcodes repo-local source and workspace/publication paths | Model installed shared-skill roots, native discovery targets, adapter modes, and compatibility mirrors instead of repo publication strings | Publication is not installation, and storage roots must come from one shared layout contract | `RuntimeInstallManifest` / native-target schema | `tests/test_runtime_manifests.py` plus install-manifest tests |
| Typed public boundary | `/Users/agents/workspace/fleki/src/knowledge_graph/models.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/__init__.py` | dataclasses and exports | No first-class install/layout/status types are exported | Add typed layout/install/status contracts and export them publicly | Implementation should not pass ad hoc dicts for a central boundary | layout/install/status dataclasses and exports | new unit tests around parsing/validation |
| Test fixture seam | `/Users/agents/workspace/fleki/tests/common.py` | `make_temp_repo()` | Builds `KnowledgeRepository(root)` with a temp enclosing root | Build a temp resolved layout and inject `data_root` or layout directly | Keep unit tests simple while moving OS-specific resolution above them | test helper for resolved temp layout | nearly every repository test |
| Storage semantics tests | `/Users/agents/workspace/fleki/tests/test_save.py`, `/Users/agents/workspace/fleki/tests/test_rebuild.py`, `/Users/agents/workspace/fleki/tests/test_source_families.py` | path assertions and receipt expectations | Assert files under `root/knowledge/**` and rejoin receipt paths through the enclosing root | Assert writes under explicit `data_root/**` and validate graph-relative payloads | Current assertions are coupled to repo-root semantics | graph-relative assertions | these tests directly |
| Status/integration tests | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` | `status()` assertions | Verifies only graph-health fields | Verify `resolved_data_root`, manifest path, and runtime agreement/drift reporting | Same-host correctness must be visible, not inferred | composed status contract | this test plus new multi-runtime smoke |
| Skill package contract | `/Users/agents/workspace/fleki/skills_or_tools/knowledge/SKILL.md`, `/Users/agents/workspace/fleki/skills_or_tools/knowledge/references/*.md` | skill instructions and references | Usage-focused package rooted in a Fleki-specific path | Make install/update/repair/root guidance self-contained and define the installer-native shipped bundle shape | Agents need one executable package contract with no repo-memory dependency | self-contained skill bundle contract | `tests/test_skill_package.py` and doc contract checks |
| Workspace publication overlay | `/Users/agents/workspace/fleki/.agents/skills/knowledge/**` | generated worktree compatibility mirror | Easy to mistake for an install surface because it is byte-for-byte real | Keep it as a generated worktree compatibility overlay only; never treat it as the canonical install or data root | Some runtimes still execute through workspace `.agents/skills`, but that state must stay non-canonical | worktree-overlay compatibility policy | `tests/test_skill_package.py` and runtime-manifest smoke |
| Legacy repo data root | `/Users/agents/workspace/fleki/knowledge/**` | current live graph tree | Repo checkout is the canonical graph home today | Treat as explicit migration input only and remove it from canonical read/write paths after cutover | No dual backends or repo-dependent storage | migration/cutover contract | migration smoke and same-host cross-runtime smoke |
| Standardized shared installer | `/Users/agents/workspace/skills/scripts/install-global.sh`, `/Users/agents/workspace/skills/scripts/sync-codex-skills.sh`, `/Users/agents/workspace/skills/README.md` | shared install and Codex sync scripts | Already install to `~/.agents/skills` and sync `${CODEX_HOME}/skills` | Reuse the same upstream seam directly from Fleki’s shipped bundle without making the sibling repo a runtime dependency or publication target | Reuse standardized installer paths instead of inventing a Fleki-only installer | installer-bundle compatibility contract | local install smoke |
| Fleki publish helpers | `/Users/agents/workspace/fleki/scripts/export_knowledge_skill_bundle.py`, `/Users/agents/workspace/fleki/skills_or_tools/knowledge/install/hermes/publish.sh`, `/Users/agents/workspace/fleki/skills_or_tools/knowledge/install/paperclip/publish.sh` | sibling-repo export targets and publish wrappers | Removed from Fleki during implementation; downstream handoff docs now replace runnable publish helpers | Keep the helper paths deleted and keep downstream handoff guidance path-free so Fleki cannot republish externally by accident | The corrected North Star forbids Fleki-owned sibling-repo publication | delete-or-replace-with-handoff contract | local doc/code audit only |
| Hermes native discovery | `/Users/agents/workspace/agents/deploy/hermes/profiles/agent_boss/config.yaml`, `/Users/agents/workspace/agents/deploy/mac/host_runner/runbook.md`, `/Users/agents/workspace/agents/README.md` | `skills.external_dirs` and operator docs | Hermes already owns its discovery config, and Fleki does not own the current repo-bound path on this machine | Keep Fleki generic: accept operator-provided external discovery roots and treat repo-owned Hermes paths as handoff-only | External-dir runtimes should work when the operator already controls the scanned path, not because Fleki hardcodes one repo layout | external-dir handoff contract | local manifest smoke plus manual external-root smoke |
| Paperclip native install | `/Users/agents/workspace/paperclip_agents/skills/README.md`, `/Users/agents/workspace/paperclip_agents/vendor/paperclip/server/src/services/company-skills.ts` | company-skill import/materialization | Requires a self-contained skill package and stable identity across import modes | Keep the shipped bundle importable and declare a stable `fleki/knowledge` key; do not claim direct install into Paperclip from Fleki | Paperclip’s company-skill system is the native import surface, and Fleki only owns the bundle handed to it | managed-import handoff contract | package audit plus manual import smoke |
| Paperclip Codex adapter | `/Users/agents/workspace/paperclip_agents/vendor/paperclip/packages/adapters/codex-local/src/server/execute.ts`, `/Users/agents/workspace/paperclip_agents/vendor/paperclip/packages/adapters/codex-local/src/server/skills.ts`, `/Users/agents/workspace/paperclip_agents/docs/bugs/2026-03-31-worktree-agents-skill-injection.md`, `/Users/agents/workspace/paperclip_agents/vendor/paperclip/docs/adapters/codex-local.md` | workspace `.agents/skills` injection and stale docs | Workspace injection is real current behavior, but Fleki does not own it | Model the generated `.agents/skills/knowledge` tree as a non-canonical worktree compatibility overlay and document the runtime-owned limitation instead of assuming adapter changes | Worktree injection remains real for current Paperclip runs, so Fleki must describe it honestly without elevating it to canonical install state | worktree-injection limitation contract | local manifest smoke plus doc parity checks |
| Legacy architecture docs | `/Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md`, `/Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02_WORKLOG.md` | v1 publication claims | Documents workspace/repo publications as the v1 truth | Add supersession guidance during implementation so older docs do not reassert repo-local install architecture | Prevent stale documentation from reintroducing the wrong defaults | supersession note / migration docs | doc audit only |

## 6.2 Migration notes
- Deprecated APIs (if any):
  - `KnowledgeRepository(root)` where `root` implies an enclosing repo that owns `knowledge/**`
  - publication-only runtime manifest dicts that do not carry install/discovery mode or shared-root agreement
- Delete list (what must be removed; include superseded shims/parallel paths if any):
  - repo-local `knowledge/**` as the canonical production graph after cutover
  - repo-local `.agents/skills/knowledge/**` as the production install story
  - hardcoded runtime publication assumptions in `runtime_manifests.py` that treat repo/workspace mirrors as installs
  - sibling-repo export targets and publish wrappers in Fleki were removed on 2026-04-03; do not reintroduce them
  - Paperclip `codex-local` workspace skill injection once runtime-owned injection exists
- Cleanup and migration notes:
  - The repo-local graph is real data. Initial cutover should be `copy -> verify -> switch`, not silent move or dual-write.
  - If the package source is migrated from `skills_or_tools/knowledge` to `skills/knowledge`, one path must be canonical and the other generated until the old path is deleted.
  - Downstream runtime adoption must consume the canonical shipped bundle, never hand-edit sibling-repo copies from Fleki.
  - `knowledge status` needs a migration-aware mode that can detect the legacy repo graph and point operators at the explicit repair/cutover step.

## Pattern Consolidation Sweep (anti-blinders; scoped by plan)
| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| --- | --- | --- | --- | --- |
| Storage root separation | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` path helpers and receipts | resolve layout above the repository and serialize graph-relative paths only | prevents repo roots, install dirs, and runtime mirrors from leaking into persisted truth | include |
| Status truthfulness | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py::status`, `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py` | compose graph health with install/runtime agreement | prevents silent split-brain across Codex, Hermes, and Paperclip | include |
| Test injection boundary | `/Users/agents/workspace/fleki/tests/common.py` and repository tests | explicit temp layout injection instead of repo-root magic | prevents OS-path logic from polluting unit tests and keeps same-host behavior testable | include |
| Shipped skill bundle | `/Users/agents/workspace/fleki/skills_or_tools/knowledge/**`, future `skills/knowledge/**`, `/Users/agents/workspace/fleki/tests/test_skill_package.py` | one self-contained installer-native skill bundle | prevents bespoke per-runtime packaging and hidden dependency drift | include |
| Workspace overlays | `/Users/agents/workspace/fleki/.agents/skills/knowledge/**`, Paperclip Codex adapter injection points | generated dev overlay only | prevents worktree state from becoming accidental production truth | include |
| Shared installer reuse | `/Users/agents/workspace/skills/scripts/install-global.sh`, `/Users/agents/workspace/skills/scripts/sync-codex-skills.sh` | reuse `~/.agents/skills` as the canonical installed source | prevents a second Fleki-only installer from diverging from existing platform practice | include |
| Hermes discovery | `/Users/agents/workspace/agents/deploy/hermes/profiles/agent_boss/config.yaml` and operator docs | `skills.external_dirs` points at the shared install parent directory | prevents Hermes-only package forks or repo-bound installs | include |
| Paperclip managed copies | `/Users/agents/workspace/paperclip_agents/vendor/paperclip/server/src/services/company-skills.ts` | managed materialization is a distribution cache, not an authoring root or data root | prevents Paperclip from becoming a second backend | include |
| Codex plugin path | Codex plugin packaging docs and future installer work | richer distribution surface beyond shared-skill install | prevents premature expansion into a second distribution mechanism before v1 is stable | defer |
<!-- arch_skill:block:call_site_audit:end -->

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan (tests optional). No fallbacks/runtime shims - the system must work correctly or fail loudly (delete superseded paths). Prefer programmatic checks per phase; defer manual/UI verification to finalization. Avoid negative-value tests (deletion checks, visual constants, doc-driven gates). Also: document new patterns/gotchas in code comments at the canonical boundary (high leverage, not comment spam).

## Phase 1 - Resolve layout, status, and migration contract in the core storage layer
Status: COMPLETE

Completed work:
- Added `KnowledgeInstallManifest`, `ResolvedKnowledgeLayout`, and `RuntimeInstallManifest` plus a new `layout.py` resolver/migration boundary.
- Refactored `KnowledgeRepository` so storage semantics resolve from explicit layout/data-root inputs rather than repo-root inference, and updated receipts plus `status` to surface `resolved_data_root`, install-manifest state, legacy-graph detection, and runtime agreement.
- Updated repository-centric tests to inject explicit temp layouts and verify graph-relative writes under `data_root/**`.

- Goal
  - Make storage semantics depend on an explicit resolved layout and canonical `data_root`, not on repo-root inference.
- Work
  - Add the typed install/layout/status boundary called for in Section 5, including `KnowledgeInstallManifest`, `ResolvedKnowledgeLayout`, and `RuntimeInstallManifest`.
  - Implement root-resolution and manifest parsing above `KnowledgeRepository`, and change the repository boundary so it accepts `data_root` or a resolved layout instead of a generic enclosing repo root.
  - Rewrite path serialization, receipts, `search`, `trace`, and `status` so persisted and reported paths are graph-relative and `knowledge status` can surface `resolved_data_root`, manifest path, and legacy repo-graph detection.
  - Update `tests/common.py` and repository-centric tests to inject explicit temp layouts instead of temp repo roots.
- Verification (smallest signal)
  - Contract tests for root-resolution precedence, relative-path rejection, and install-manifest parsing.
  - Updated repository tests proving writes land under explicit `data_root/**` and `status` exposes root/install state.
- Docs/comments (propagation; only if needed)
  - Add short comments at the layout resolver boundary and the graph-relative serialization boundary.
- Exit criteria
  - Core library behavior no longer depends on repo cwd or `root/knowledge/**` semantics, and callers can prove which root they are using.
- Rollback
  - Do not change runtime install/discovery defaults yet; repo-local graph state remains authoritative until migration cutover work is ready.

## Phase 2 - Normalize the shipped bundle and self-contained install assets
Status: COMPLETE

Completed work:
- Added deterministic export from `skills_or_tools/knowledge/**` into `skills/knowledge/**` plus the repo-local worktree overlay, including stale-file cleanup so generated bundle surfaces stay exact mirrors instead of additive copies.
- Added package-local install assets under `skills_or_tools/knowledge/install/**` and propagated them into the shipped bundle and worktree overlay.
- Strengthened `tests/test_skill_package.py` so source, shipped, and overlay bundles must match file-for-file and byte-for-byte.

- Goal
  - Produce one installer-native `skills/knowledge` bundle without dual-authoring while preserving a low-risk migration path from the current repo layout.
- Work
  - Adopt a one-way deterministic export from `skills_or_tools/knowledge/**` to `skills/knowledge/**` during migration, with `skills_or_tools/knowledge/**` remaining the only human-edited path until final cleanup.
  - Add self-contained install, update, repair, and migration assets under the shipped bundle so operators do not need sibling-repo memory.
  - Split tests and docs so they distinguish source package, shipped bundle, and worktree overlay responsibilities.
  - Make sure the shipped bundle does not depend on ambient interpreter state or undocumented setup beyond the explicit shared installer seam.
- Verification (smallest signal)
  - Bundle export/parity contract test.
  - Updated `tests/test_skill_package.py` proving source-versus-shipped package expectations.
  - One manual dry inspection that `skills/knowledge/**` is self-contained.
- Docs/comments (propagation; only if needed)
  - Put operator-critical instructions in the shipped bundle and keep the export boundary documented where drift would be costly.
- Exit criteria
  - An installer-native, self-contained bundle exists on disk and exactly one package path is human-edited.
- Rollback
  - Keep `skills_or_tools/knowledge/**` as the sole edited path if export stabilization fails; do not hand-edit `skills/knowledge/**`.

## Phase 3 - Finish the Fleki-owned host-local install and root cutover
Status: COMPLETE

Completed work:
- Reworked `runtime_manifests.py` and its tests around managed install roots, external discovery roots, compatibility targets, adapter modes, and installed-path metadata instead of repo-root-only assumptions.
- Added a self-contained Codex install asset that exports the shipped bundle, installs it into `~/.agents/skills/knowledge` through the upstream `npx skills add` seam, creates the Codex compatibility link, and writes `~/Library/Application Support/Fleki/install.json`.
- Migrated the repo-local graph into `~/Library/Application Support/Fleki/knowledge` and added migration-time normalization so managed embedded paths become graph-relative after cutover.
- Verified post-cutover local `status`, `search`, and `trace` against the canonical data root and install manifest.

- Goal
  - Complete everything Fleki itself owns locally: bundle export, shared install, compatibility link, install manifest, and canonical app-data-root cutover.
- Work
  - Keep the upstream shared installer seam but call it directly from package-local install assets so the bundle stays self-contained.
  - Write the installer-managed manifest and make local status/reporting prove the active root and agreement contract.
  - Perform explicit `copy -> verify -> switch` migration from the repo-local graph into the canonical app-data root.
  - Demote repo-local `.agents/skills/knowledge/**` to a generated worktree overlay only.
- Verification (smallest signal)
  - Runtime manifest tests.
  - One shared-installer smoke into `~/.agents/skills`.
  - One migration smoke plus local `status` / `search` / `trace` against the canonical data root.
- Docs/comments (propagation; only if needed)
  - Add high-leverage comments at install/discovery boundaries and keep the package-local install docs truthful.
- Exit criteria
  - Fleki-owned surfaces are cut over locally, and a host can prove the active shared install and canonical data root without consulting sibling repos.
- Rollback
  - Keep the legacy repo-local graph as explicit rollback material until downstream adoption and cleanup are ready.

## Phase 4 - Define Fleki-side adaptation rules for fixed Hermes and Paperclip surfaces
Status: COMPLETE

Completed work:
- Research-grounded the native Hermes and Paperclip surfaces, their ownership boundaries, and the exact fixed behaviors Fleki must live with.
- Implemented a reusable Fleki-owned install-target layer:
  - managed install root
  - operator-provided external discovery roots
  - compatibility skill paths
  - generated worktree overlay path
  - stable Paperclip key `fleki/knowledge`
- Repaired the runtime manifests, installer docs, and package contract so support claims now match what Fleki really owns.

Deferred:
- Any edits to Hermes or Paperclip configs, repos, or vendored runtime code.

- Goal
  - Produce the smallest truthful Fleki-only compatibility answer for Hermes-like and Paperclip-like runtimes while keeping their external configs and repos untouched.
- Work
  - Replace any remaining language that expects Hermes or Paperclip changes with explicit read-only constraint statements.
  - Implement only Fleki-owned adaptation.
  - State the support matrix plainly:
    - Codex: fully Fleki-owned
    - Hermes-like external-dir runtimes: supported through operator-provided discovery roots only
    - Current repo-owned Hermes path on this machine: handoff-only, not self-installable from Fleki
    - Paperclip-like managed-import runtimes: supported through shipped-bundle import plus stable key
    - Paperclip workspace injection: runtime-owned limitation; Fleki only models the non-canonical overlay honestly
- Verification (smallest signal)
  - Doc-level call-site audit and phase-plan consistency.
  - Local runtime-manifest/status agreement proving the Fleki-side compatibility story is shaped correctly.
  - Manual smoke for an operator-provided external discovery root and a managed-import runtime.
- Docs/comments (propagation; only if needed)
  - Document explicit read-only external constraints wherever older text implied those systems should change.
- Exit criteria
  - The plan names the Fleki-only compatibility answer and the truthful support matrix.
- Rollback
  - If Fleki-only compatibility is still ambiguous, stop at the host-local Fleki boundary and do not guess across repo lines.

## Phase 5 - Delete Fleki-side legacy compatibility paths after the Fleki-only compatibility answer is settled
Status: BLOCKED

Completed work:
- Added supersession notes to the earlier cross-agent architecture doc and worklog so they no longer imply that repo-local graph/install surfaces remain the intended long-term default.
- Removed sibling-repo export targets from `scripts/export_knowledge_skill_bundle.py` and deleted the Hermes/Paperclip publish wrappers from the source bundle.
- Reworked the runtime-manifest contract and tests so Fleki exposes managed install roots, operator-provided external discovery roots, compatibility paths, the worktree overlay, and the stable Paperclip key instead of repo publication paths.
- Rewrote `AGENTS.md`, the package skill docs, and the bundle export test so Fleki no longer documents or validates cross-repo publish commands.

Deferred:
- Deleting the legacy repo-local `knowledge/**` tree after the cutover.
- Collapsing authoring from `skills_or_tools/knowledge/**` to `skills/knowledge/**` as the only human-edited package path.
- Keep the repo-local worktree overlay only as long as some supported runtime still executes through workspace `.agents/skills`; do not schedule deletion around hypothetical external changes.

Blocked on:
- The remaining cleanup depends only on Fleki-owned migration choices, not on Hermes or Paperclip changes.

- Goal
  - Finish the no-parallel-path cleanup so repo-local graph/install truth cannot silently return.
- Work
  - Remove repo-local `knowledge/**` from canonical production use, leaving only intentional fixtures or generated overlays where still needed.
  - Remove test assumptions and manifest fields that model repo/workspace compatibility surfaces as production installs.
  - Delete or replace Fleki-local sibling-repo publish helpers with downstream handoff docs once the downstream adoption contract is stable.
  - Supersede stale claims in `CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md` and its worklog so older docs do not reassert repo-local defaults.
  - Collapse to one canonical human-edited package path by moving authoring to `skills/knowledge/**` and deleting the `skills_or_tools/knowledge/**` precursor once export-first migration is stable.
- Verification (smallest signal)
  - No remaining tests or docs assert repo-local install truth.
  - Final Fleki-owned smoke passes without using repo-local graph state or workspace publication as install truth.
  - Lightweight doc audit for superseded architecture claims.
- Docs/comments (propagation; only if needed)
  - Add short supersession notes only where older docs could still mislead operators or future implementers.
- Exit criteria
  - No Fleki-owned production path treats repo-local graph state or workspace publication as authoritative, and only one package path remains human-edited.
- Rollback
  - If cleanup reveals unresolved consumer dependencies, stop at generated-bundle mode and defer the final precursor deletion rather than reintroducing dual-authoring.
<!-- arch_skill:block:phase_plan:end -->

# 8) Verification Strategy (common-sense; non-blocking)

Avoid verification bureaucracy. Prefer the smallest existing signal. Default to 1-3 checks total. Do not invent new harnesses, frameworks, or scripts unless they are already the cheapest guardrail. Keep manual verification as finalization by default. Do not create proof tests for deletions, visual constants, or doc inventories. Document tricky invariants and gotchas at the SSOT or contract boundary.

## 8.1 Unit tests (contracts)
- Root-resolution precedence, relative-path rejection, and failure semantics.
- Install-manifest parsing/validation plus repository path-serialization/status contracts against explicit `data_root`.
- Bundle export/normalization and runtime manifest generation for standardized install surfaces and thin adapters.

## 8.2 Integration tests (flows)
- Shared-skill install/update flow from the shipped bundle into `~/.agents/skills` plus compatibility sync or adapter repair where it can be checked cheaply.
- Explicit `copy -> verify -> switch` migration from repo-local graph to centralized root.
- `knowledge status` reporting the resolved root, manifest path, and install/runtime agreement.

## 8.3 E2E / device tests (realistic)
- Same-host Codex smoke against one shared root after installation through the shared install surface.
- Hermes and Paperclip native-adoption smokes happen in their owning repos or control planes after the Fleki package/install contract is handed off there.

# 9) Rollout / Ops / Telemetry

## 9.1 Rollout plan
- Land the core layout/status contract first while repo-local graph state remains authoritative.
- Normalize the shipped bundle and shared-installer path before changing operator-default root or runtime guidance.
- Cut over one host with explicit `copy -> verify -> switch` migration and `install.json` activation.
- Delete repo-local install/storage truth only after Fleki-owned local smoke passes and downstream adoption lands in the owning surfaces.

## 9.2 Telemetry changes
- Keep telemetry light. The main operational signal is truthful root/install status surfaced by `knowledge status` and install receipts where helpful.
- If install drift needs additional signals, prefer inspectable manifest state over a new telemetry subsystem.

## 9.3 Operational runbook
- Operators need one clear package-local story for:
  - install
  - update
  - repair install/adoption drift
  - confirm the active root
  - migrate legacy repo-local graph state

# 10) Decision Log (append-only)

## 2026-04-03 - Plan around one host-level graph root and native per-runtime installation

Context
- The existing repo already proves the knowledge graph and shared skill contract, but the graph is still repo-local and installation is still publication-first.
- The user explicitly wants one centralized system-level location for the graph and native installation per runtime surface.

Options
- Keep the graph repo-local and rely on convention to keep different runtimes pointed at the same checkout.
- Introduce one host-level canonical graph root and require native runtime installations to bind to it.

Decision
- Plan around one host-level canonical graph root as the default architecture.
- Draft default root: `~/.fleki/knowledge`.
- Require native Codex, Hermes, and Paperclip installation flows to point at that same root without forking the `knowledge` contract.

Consequences
- The current repo-local `knowledge/**` tree now needs an explicit migration or cutover plan.
- Runtime packaging becomes first-class architecture work rather than a follow-up note.
- The package boundary must become self-contained enough to teach install/update/repair without dependency drift.

Follow-ups
- Confirm whether `~/.fleki/knowledge` is the right default root or whether research should move it to a platform-specific application-data location.
- Confirm whether Codex should continue using workspace publication as its native install surface or should move to a better native user-level discovery path if one exists.

## 2026-04-03 - External research shifts the default from fixed dotdir plus per-runtime installers to platform-standard data roots plus standardized shared install surfaces

Context
- External research showed that Linux/XDG and macOS both already define standard places for app-managed data and support files.
- Official Codex docs already define shared user/admin skill locations and a plugin distribution model.
- Internal grounding from `../skills` showed we already use an upstream shared-skill installer that targets `~/.agents/skills`, so a new bespoke per-agent installer would duplicate an existing install surface.

Options
- Keep the draft default of `~/.fleki/knowledge` and continue designing one installer/update flow per runtime surface.
- Resolve the graph root through platform-standard application-data paths and reuse standardized shared install/discovery surfaces, leaving only thin runtime adapters where truly needed.

Decision
- Supersede the fixed `~/.fleki/knowledge` draft default with platform-standard application-data roots.
- Treat standardized shared-skill install/discovery surfaces as the default package-install path.
- Demote workspace `.agents/skills` to a generated worktree overlay rather than the primary installed Codex surface.

Consequences
- The plan now needs an OS-aware install-layout contract instead of a single hard-coded dotdir.
- The package-install story becomes simpler operationally, but the architecture must clearly separate install/discovery paths from canonical graph-data paths.
- The existing repo-workspace publication and repo-local graph both become migration or development surfaces rather than the long-term production defaults.

Follow-ups
- Decide whether the first Codex shipping shape should stop at the existing shared-skill installer into `~/.agents/skills` or invest immediately in plugin packaging.
- Define the thin Hermes and Paperclip adapter rules so they consume the same installed package and root without becoming separate installers.

## 2026-04-03 - Deep dive locks v1 install topology around one shared installed package plus one shared data-root contract

Context
- Code review showed that `KnowledgeRepository` and `runtime_manifests.py` are still disconnected: storage is single-root only inside one repo-shaped root, while runtime manifests only describe publication copies.
- External and internal installer research showed that `~/.agents/skills` already acts as the standardized shared-skill install surface, with `${CODEX_HOME}/skills` acting as a compatibility mirror rather than a separate install model.
- Runtime-specific research showed Hermes already has native external-dir discovery, while Paperclip’s native install surface is company-skill import/materialization and its current workspace `.agents/skills` injection is a non-canonical adapter quirk.

Options
- Keep repo/workspace publications as the primary install story and let each runtime continue to infer or improvise where the graph lives.
- Standardize on one shared installed package plus one explicit layout manifest, then let each runtime use only its native discovery/attachment surface.
- Jump immediately to Codex plugin packaging as the v1 install shape.

Decision
- For v1, use the existing shared-skill installer seam and treat `~/.agents/skills/knowledge` as the canonical installed package.
- Treat `${CODEX_HOME}/skills/knowledge` as a compatibility mirror only. Codex plugin packaging is explicitly deferred.
- Hermes consumes the shared installed package through `skills.external_dirs`.
- Paperclip consumes the same shipped bundle through company-skill import/materialization; managed copies are allowed as distribution artifacts, but workspace `.agents/skills` is not canonical.
- Root resolution moves above `KnowledgeRepository` into one shared layout/install-manifest contract.

Consequences
- Repository constructor semantics, path serialization, and status reporting all need refactoring around `data_root` rather than repo root.
- Fleki’s shipped package must become installer-native and self-contained enough for the shared installer, Hermes native discovery, and Paperclip company-skill import.
- Workspace publication mirrors and repo-local graph state become migration or development artifacts, not production truth.
- The existing phase plan is directionally right but now underspecified around bundle normalization, migration sequencing, and external-repo adapter work.

Follow-ups
- Run `phase-plan` next so the implementation phases match the now-locked install topology.
- During phase planning, choose whether `skills_or_tools/knowledge` is directly moved to `skills/knowledge` or feeds it through one-way deterministic export during migration.

## 2026-04-03 - Phase planning chooses export-first bundle normalization and a five-phase cutover sequence

Context
- The deep dive left Section 7 directionally correct but too coarse to execute. It did not yet decide how to get from today’s `skills_or_tools/knowledge` layout to the installer-native `skills/knowledge` bundle.
- Repo evidence shows there is no `skills/` directory yet in Fleki, while tests, docs, and active runtime/publication references still point at `skills_or_tools/knowledge` and `.agents/skills/knowledge`.

Options
- Move directly from `skills_or_tools/knowledge` to `skills/knowledge` up front and absorb the full repo-wide churn immediately.
- Use a one-way deterministic export from `skills_or_tools/knowledge` to `skills/knowledge` during migration, then collapse to one final authoring path during cleanup.

Decision
- Use export-first bundle normalization during migration.
- Keep `skills_or_tools/knowledge/**` as the only human-edited source path until the shipped bundle and runtime integrations are stable.
- Make `skills/knowledge/**` the installer-native shipped bundle immediately, then collapse to `skills/knowledge/**` as the sole human-edited path in the final cleanup phase.
- Execute the work in five phases: core layout/status contract, bundle normalization, shared installer/runtime discovery, data-root cutover, and legacy cleanup.

Consequences
- Initial implementation churn stays lower, but the export boundary must be explicit and tested.
- Final cleanup is now mandatory, not optional, because export-first is a migration tactic rather than the desired steady state.
- Section 7 becomes the authoritative sequence for execution and supersedes the earlier three-phase sketch.

Follow-ups
- Use Section 7 as the only execution checklist for `implement`.
- During implementation, add supersession notes wherever older docs still teach repo-local install or storage truth.

## 2026-04-03 - Use the upstream shared installer seam directly from the shipped bundle

Context
- The plan required reuse of the standardized shared-skill installer seam without forcing operators to remember sibling-repo wrapper scripts.
- The sibling `../skills` repo already proves that the canonical installer surface is `npx skills add ...` into `~/.agents/skills`.

Options
- Shell out through `../skills/scripts/install-global.sh`, which preserves the same seam but keeps a hidden dependency on sibling-repo layout.
- Call the same upstream `npx skills add` seam directly from the shipped bundle install asset after exporting the installer-native bundle.

Decision
- Use the upstream `npx skills add` seam directly inside `skills_or_tools/knowledge/install/codex/install.sh`.
- Keep the sibling shared-skills repo as a publication/compatibility surface, but not as a required runtime dependency for the install asset.

Consequences
- The package stays self-contained while still reusing the standardized installer path.
- Codex install/update remains aligned with the existing shared-skill ecosystem instead of inventing a Fleki-only installer.

Follow-ups
- If other runtimes gain first-class shared-installer surfaces later, prefer calling those standardized seams directly from package-local install assets as well.

## 2026-04-03 - Migration must rewrite legacy embedded `knowledge/` path strings during cutover

Context
- The initial host cutover copied the repo-local graph into the canonical app-data root successfully, but migrated provenance metadata and older receipts still contained stored `knowledge/...` relative paths from the pre-layout-refactor era.
- That stale embedded metadata made search/trace outputs partially truthful and partially legacy-shaped even though the live repository root had already switched to graph-relative path reporting.

Options
- Leave old embedded metadata untouched and accept mixed path semantics after migration.
- Normalize managed metadata and managed markdown bodies during migration while preserving raw source payloads exactly.

Decision
- Extend migration to rewrite legacy `knowledge/...` managed-path strings in source manifests, provenance metadata, and managed topic/receipt bodies during the copy -> verify -> switch cutover.
- Keep raw source payloads under `sources/**` untouched.

Consequences
- Post-migration search/trace/status outputs stay graph-relative and consistent with the new repository contract.
- Migration now owns one more repair step, but it remains explicit and inspectable instead of depending on a one-off manual cleanup.

Follow-ups
- If an already-migrated host predates this normalization step, run the same managed-metadata rewrite against the canonical data root before claiming the cutover is clean.

## 2026-04-03 - Sibling repos are reference patterns and downstream adopters, not Fleki publication targets

Context
- The earlier plan and implementation path overreached by treating sibling repos and runtime-owned surfaces as places Fleki should publish the `knowledge` package directly.
- The user clarified that those repos are for pattern research and downstream-native adoption, not for Fleki-owned mutation.

Options
- Keep treating sibling repos as Fleki publication targets and continue pushing package copies into them.
- Restrict Fleki to repo-local package/install outputs plus the host-local graph cutover, and treat Hermes/Paperclip integration as external-runtime handoff.

Decision
- Fleki stops at the shipped bundle, host-local shared install, install manifest, canonical data-root cutover, and downstream adoption contract.
- Sibling repos remain evidence sources and downstream call sites, but Fleki does not publish into them as part of its ordinary install/update story.
- Any future Hermes or Paperclip follow-through must happen explicitly in those owning surfaces, not as a side effect of Fleki implementation.

Consequences
- The North Star and phase plan now separate Fleki-owned delivery from external-runtime handoff more sharply.
- Phase 4 becomes a downstream adoption contract/handoff phase instead of a Fleki publication phase.
- Phase 5 cleanup now depends on downstream adoption landing elsewhere before Fleki deletes its remaining compatibility surfaces.

Follow-ups
- Keep runtime-manifest and call-site audit language honest about downstream ownership.
- Do not treat undone sibling-repo writes as acceptance evidence for this plan.

## 2026-04-03 - Delete Fleki-side publish helpers before the support matrix is honest

Context
- The repaired plan forbids Fleki from publishing into sibling repos, but the repo still carried local helper scripts, manifest fields, and tests that preserved that old behavior.
- Those local paths were now pure drift: they no longer matched the North Star, and leaving them in place made it easy to repeat the same mistake.

Options
- Keep the helper scripts and repo-path manifest fields until Hermes and Paperclip support is clarified elsewhere.
- Delete the Fleki-side publish helpers now, keep only downstream handoff guidance, and leave the true external blockers visible.

Decision
- Delete the sibling-repo export targets and the Hermes/Paperclip publish wrappers from Fleki now.
- Remove the Paperclip repo path and workspace-overlay path from Fleki-owned runtime-manifest truth.
- Rewrite repo and package instructions so Fleki documents only local install plus downstream handoff.

Consequences
- Fleki can no longer accidentally republish into sibling repos from its own installer surface.
- The shipped and generated skill bundles now match the repaired ownership boundary.
- The overall plan remains incomplete only because Fleki still has Phase 5 cleanup left. External runtime changes are not valid blockers anymore.

Follow-ups
- Finish deleting the legacy repo-local graph and the export-first package split.

## 2026-04-03 - Hermes and Paperclip configs are off limits; Fleki adapts or de-scopes

Context
- The repaired plan still drifted into treating Hermes and Paperclip follow-up changes as expected next steps.
- The user clarified that Hermes and Paperclip configs, repos, and vendored runtime code are off limits in this effort.

Options
- Keep treating Hermes and Paperclip changes as pending external follow-up.
- Treat those systems as fixed inputs and require Fleki to adapt to them or explicitly stop claiming support in this plan.

Decision
- Hermes and Paperclip configs and repos are read-only constraints for this plan.
- Fleki may not require or implement edits there.
- Any remaining support claim for Hermes or Paperclip must come from Fleki-owned adaptation only, or be explicitly de-scoped.

Consequences
- External Hermes and Paperclip edits are no longer valid blockers or follow-up work for this plan.
- The remaining architecture work shifts back into Fleki: compatibility from Fleki alone or an explicit scope cut.
- Phase 4 and the audit block now describe fixed external constraints instead of downstream change requests.

Follow-ups
- Repair any remaining plan sections that still imply Hermes or Paperclip should change.
- Decide the final cleanup shape now that Fleki has a reusable install-target framework.

## 2026-04-03 - Reusable install-target framework plus stable Paperclip key

Context
- Fleki needed a support story that adapts to different external-dir runtime setups without hardcoding one repo-owned Hermes path.
- Paperclip needed a stable skill identity and a truthful statement that worktree injection is runtime-owned, not canonical Fleki install state.

Options
- Keep one managed install root and pretend Hermes-like runtimes read it automatically.
- Add a reusable install-target layer with optional external discovery roots, optional compatibility paths, and a stable managed-import identity.

Decision
- Fleki now owns:
  - one managed install root
  - optional operator-provided external discovery roots
  - optional compatibility skill paths
  - one generated worktree compatibility overlay
  - stable skill key `fleki/knowledge`
- Fleki does not claim that every runtime reads the managed install root directly.

Consequences
- Codex remains fully Fleki-owned.
- Hermes-like runtimes are supported when operators already control the scanned external skill roots.
- The current repo-owned Hermes path on this machine remains handoff-only because Fleki will not write into that repo in this effort.
- Paperclip-like managed imports can keep one stable identity across import modes, but workspace injection remains a runtime-owned limitation.

Follow-ups
- Finish Phase 5 cleanup without assuming Hermes or Paperclip changes will rescue stale Fleki paths.

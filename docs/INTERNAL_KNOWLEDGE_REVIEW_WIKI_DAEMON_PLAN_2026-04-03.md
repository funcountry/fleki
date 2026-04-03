---
title: "Fleki - Internal Knowledge Review Wiki Daemon - Architecture Plan"
date: 2026-04-03
status: active
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: architectural_change
related:
  - /Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md
  - /Users/agents/workspace/fleki/docs/CENTRALIZED_KNOWLEDGE_INSTALL_AND_ROOT_PLAN_2026-04-03.md
  - /Users/agents/workspace/fleki/src/knowledge_graph/frontmatter.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/layout.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/repository.py
  - https://quartz.jzhao.xyz/
---

# TL;DR

- **Outcome:** Add an optional review wiki that runs on this machine, rebuilds automatically when exported knowledge changes, and lets humans browse the accumulated knowledge graph comfortably without turning the viewer into a writer.
- **Problem:** The current graph is correct and inspectable, but it mixes semantic pages, provenance notes, raw source records, receipts, and render artifacts in one tree. That works for agents and traceability, but it is a poor and risky direct input for a human review site.
- **Approach:** Keep the live graph under the resolved Fleki data root as the only source of truth, port the existing knowledge base in place instead of supporting split formats or split content paths, cut the markdown page format over to Quartz-friendly YAML frontmatter, export only an allowlisted browse tree into `state_root`, and run a lightweight local daemon that rebuilds Quartz only when the exported content digest changes.
- **Plan:** First hard-cut the existing knowledge base to the new canonical page format and metadata rules. Then add a review-wiki exporter plus digest gate. Then add the daemon and native per-user service install for macOS and Linux. Stop there.
- **Non-negotiables:**
  - The live knowledge graph under `resolved_data_root` remains the only writer.
  - The review wiki is disposable derived state under `state_root`.
  - The existing knowledge base is ported to the new canonical format; Fleki does not keep old and new page formats alive in parallel.
  - Quartz must never read the raw graph tree directly.
  - Raw `sources/**`, `receipts/**`, `.record.json`, and secret-bearing assets are excluded from the public review tree by default.
  - Render markdown and render assets do not ship in the review wiki in v1.
  - Rebuild correctness is decided by Fleki's own export digest, not by launchd or systemd file-watch behavior.
  - The browse model stays semantic and provenance-aware, not source-family-first.
  - The canonical markdown format becomes one thing, not mixed JSON and YAML frontmatter in parallel.
  - There is no review-wiki config file in v1.
  - There is no separate service-management CLI in v1.
  - The review-site implementation does not ship inside the agent skill runtime bundle.
  - When a simpler required rule will work, prefer making it required over adding split paths, optional compatibility modes, or dual support logic.

<!-- arch_skill:block:implementation_audit:start -->
# Implementation Audit (authoritative)
Date: 2026-04-03
Verdict (code): COMPLETE
Manual QA: pending (non-blocking)

## Code blockers (why code is not done)
- None.

## Reopened phases (false-complete fixes)
- None.

## Missing items (code gaps; evidence-anchored; no tables)
- None.

## Non-blocking follow-ups (manual QA / screenshots / human verification)
- Run `./install.sh --review-wiki` on one Linux host, open `http://127.0.0.1:4151`, confirm rebuild on exported-content changes, confirm no rebuild on receipt-only changes, and then remove it with `./install.sh --remove-review-wiki`.
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
> If Fleki ports the existing knowledge base directly to one new canonical page format and one required review-wiki export path, then adds an optional local review wiki system that exports only semantic review content from the live knowledge graph into a separate Quartz build tree, rebuilds only when that exported content actually changes, and installs as a native per-user background service on macOS or Linux, internal reviewers on this machine will be able to browse topics, indexes, and linked provenance clearly without Quartz becoming the canonical storage or raw-source exposure path and without Fleki carrying split support logic.

## 0.2 In scope
- UX surfaces (what users will see change):
  - A private local review site for the knowledge graph.
  - Human-readable home and landing pages for semantic topics.
  - Browse-oriented indexes such as by-topic, recent changes, and unresolved questions.
  - Provenance drill-down from topic pages into supporting notes.
  - A simple repo-owned install story on macOS and Linux for enabling or disabling the review wiki service on this machine.
- Technical scope (what code/docs/packaging will change):
  - Canonical topic and provenance markdown frontmatter moves from JSON to Quartz-compatible YAML by porting the existing pages in place.
  - A filtered export tree under `state_root` for review-site content and build output.
  - A lightweight daemon that scans allowlisted graph inputs, computes an export digest, rebuilds when needed, and serves the static site locally.
  - Native per-user service files for `launchd` and `systemd --user`.
  - A repo-owned Quartz template plus install-time Node/npm preflight.

## 0.3 Out of scope
- UX surfaces (what users must NOT see change):
  - Editing the knowledge graph through the review site.
  - A public internet-facing knowledge site.
  - A source-family-first information architecture such as `pdf/`, `hermes/`, or `codex/` folders as the main browse experience.
  - Raw receipts, copied source archives, or secret-bearing assets as ordinary review content.
- Technical scope (explicit exclusions):
  - Letting Quartz consume `resolved_data_root` directly.
  - A second semantic storage model that lives only inside the site generator.
  - Networked multi-user serving, authentication, or fleet management.
  - A fallback JSON-frontmatter path kept alive after YAML cutover.
  - Split support for old and new graph page formats or parallel export paths.
  - Render-markdown or render-asset export in v1.
  - A review-wiki config file in v1.
  - A separate service-management CLI in v1.
  - A filesystem-trigger-only correctness model based on `launchd WatchPaths` or `systemd.path`.
  - New inference, retrieval, or summarization machinery beyond what the graph already stores.

## 0.4 Definition of done (acceptance evidence)
- The live graph remains under the resolved Fleki data root, and the review site can be deleted and rebuilt from it.
- Topic pages, linked provenance notes, and indexes render as readable Quartz pages with working internal navigation.
- The review wiki rebuilds automatically after a save or rebuild that changes exported semantic content.
- The review wiki does not rebuild when only excluded graph state changes, such as new receipts that do not affect exported pages.
- The staged site tree does not expose raw `sources/**`, raw record JSON, or receipts by default.
- The staged site tree does not expose render markdown, render assets, or raw PDFs in v1.
- macOS and Linux operators can install or remove the background service with the repo-owned installer.
- Smallest credible evidence:
  - frontmatter migration tests prove all canonical page writers and readers round-trip YAML
  - exporter tests prove allowlist inclusion and exclusion behavior
  - digest-gating tests prove irrelevant changes do not force rebuilds
  - service-file tests prove the expected launchd and systemd user units are rendered correctly
  - one local manual smoke per OS family proves the site builds and is reachable on `127.0.0.1`

## 0.5 Key invariants (fix immediately if violated)
- The canonical writer remains the live knowledge graph under `data_root`.
- The review wiki content tree and built site live under `state_root` and are disposable.
- `state_root` holds review-wiki derived state; `data_root` holds knowledge; this feature does not use a review-wiki config file in `config_root` in v1.
- Quartz never points at the raw graph tree.
- Only allowlisted semantic review content is exported.
- Provenance is first-class in the review UI, but semantic topics remain primary.
- Raw copied sources and receipts are excluded by default.
- Render markdown, render assets, and raw PDFs are excluded by default in v1.
- YAML frontmatter becomes the only canonical markdown metadata format for graph pages.
- The existing knowledge base is ported directly to the new canonical format; Fleki does not maintain split old-versus-new support paths.
- The daemon either rebuilds correctly from a deterministic export digest or fails loudly and preserves the last good built site.
- The background service runs one foreground process. It must not daemonize itself.
- The review site binds localhost only and uses one fixed default port in v1.
- There is no review-wiki config file in v1.
- OS-native path watches may be hints later, but the correctness boundary remains Fleki's own scan and digest logic.
- Prefer required inputs and one path through the code over optional split behavior when either would satisfy the product goal.

# 1) Key Design Considerations (what matters most)

## 1.1 Priorities (ranked)
1. Safe human browsing of accumulated knowledge without raw-source leakage.
2. Preserve the live graph as the only source of truth.
3. Prefer one simple required path over compatibility branches or split support.
4. Make install on this machine easy and native for macOS and Linux.
5. Rebuild only when exported information changes, not on irrelevant churn.
6. Reuse existing graph pages and metadata instead of inventing a second knowledge model.

## 1.2 Constraints
- The current repo already stores semantic topics, provenance notes, raw source records, receipts, and optional search support state under one root.
- Topic and provenance markdown currently use JSON frontmatter, while Quartz expects YAML or TOML frontmatter.
- The current install story is already centered on `data_root`, `config_root`, `state_root`, and a repo-owned installer.
- The user explicitly approved changing the canonical graph page frontmatter if that makes Quartz easier to use.
- The user explicitly wants this feature to stay optional and easy to install on macOS and Linux.
- The user explicitly wants the existing knowledge base ported to the new format rather than supported through split old/new paths.
- The user explicitly prefers simplifying required rules over optional compatibility branches when both would meet the goal.
- The user explicitly wants extra optional reviewer features removed unless they are required to meet the core browse-and-regenerate requirement.
- Quartz publishes non-markdown assets from its content folder, so safety depends on what Fleki feeds Quartz, not only on page-level publish flags.

## 1.3 Architectural principles (rules we will enforce)
- Keep one source of truth: the live graph under `data_root`.
- Port the existing knowledge base directly to the new canonical format instead of keeping split old/new support alive.
- Separate human review output from canonical storage.
- Make the export allowlist explicit and narrow.
- Prefer hard cutover over mixed-format or mixed-authority operation.
- Prefer required inputs and one implementation path over optional branches unless the user explicitly approves the extra complexity.
- Keep the first version boring: no extra viewer features, no extra operator knobs, no extra package surfaces.
- Keep service correctness in Fleki code, not in OS watch semantics.
- Use existing repo install and packaging patterns before inventing new distribution paths.

## 1.4 Known tradeoffs (explicit)
- Moving canonical frontmatter to YAML simplifies Quartz and future renderer support, but it requires a one-time port of existing markdown pages and related tests.
- Keeping a staging tree between the graph and Quartz adds one more build step, but it is the clearest way to prevent accidental source and receipt exposure.
- A polling plus digest loop is less immediate than a full filesystem watch stack, but it is simpler and more trustworthy across macOS and Linux service managers.
- Serving locally from a Fleki-owned daemon is more code than using Quartz preview mode, but it gives Fleki control over correctness, startup, and service management.
- Fixed localhost defaults and no review config file reduce flexibility, but they keep the first version smaller and easier to trust.

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- Fleki already stores knowledge under one resolved graph root with separate `topics/`, `provenance/`, `sources/`, `assets/`, `receipts/`, and `search/` directories.
- The repo already writes human-readable semantic topic pages and provenance notes in markdown.
- The current graph is aimed at agent workflows: `knowledge save`, `knowledge search`, `knowledge trace`, `knowledge rebuild`, and `knowledge status`.
- The current graph is browseable by opening markdown files directly, but there is no dedicated human review site or background regeneration process.
- The repo already has `config_root` and `state_root`, but the review-wiki feature does not exist yet.
- The current KB is small enough that a direct in-place port is cheaper and cleaner than designing long-lived split support.

## 2.2 What’s broken / missing (concrete)
- There is no low-friction human browse surface for internal review of the accumulated knowledge.
- The raw graph tree is not a safe direct content root for a static site generator because it includes raw sources, receipts, and record JSON beside semantic pages.
- The page metadata format is not directly compatible with Quartz.
- There is no digest-gated rebuild loop, no local static build path, and no native service install for a review site.
- The current CLI only exposes agent-facing graph verbs; there is no separate operator surface for review-site lifecycle.
- The cheapest clean implementation path is to make some data and config rules required instead of supporting multiple legacy or optional shapes.

## 2.3 Constraints implied by the problem
- The viewer must not become a second writer.
- The human review browse tree must exclude raw evidence by default, yet still support provenance drill-down.
- Site regeneration must not be keyed off receipt churn or raw-source timestamps alone.
- The solution must fit the repo's existing packaging and install model instead of becoming a separate app with its own data root.
- The plan should remove rather than preserve unnecessary forks in format, export path, and config interpretation.

<!-- arch_skill:block:research_grounding:start -->
# 3) Research Grounding (external + internal “ground truth”)

## 3.1 External anchors (papers, systems, prior art)
- Quartz docs — adopt as the first renderer for the review wiki because Quartz is already optimized for markdown knowledge gardens with explorer, search, aliases, and backlinks, and it documents a local build model instead of requiring a separate backend.
  - Authoring/content model: https://quartz.jzhao.xyz/authoring-content
  - Build/runtime docs: https://quartz.jzhao.xyz/build
  - Search, explorer, aliases: https://quartz.jzhao.xyz/features/full-text-search , https://quartz.jzhao.xyz/features/explorer , https://quartz.jzhao.xyz/plugins/AliasRedirects
- Quartz frontmatter and asset behavior — adopt the frontmatter requirement and reject direct raw-graph reads. Quartz expects YAML or TOML frontmatter, and its docs say non-markdown assets in the content folder are emitted publicly. That makes a filtered export tree mandatory even after frontmatter cutover.
  - Frontmatter: https://quartz.jzhao.xyz/plugins/Frontmatter
  - Assets: https://quartz.jzhao.xyz/plugins/Assets
  - Private pages: https://quartz.jzhao.xyz/features/private-pages
- Quartz date handling — adopt frontmatter-first dates for review pages so exported files do not show rebuild-time dates as content-time dates.
  - CreatedModifiedDate: https://quartz.jzhao.xyz/plugins/CreatedModifiedDate
- Apple launchd guidance — adopt per-user LaunchAgents with one foreground process and reject `WatchPaths` as the correctness boundary because Apple documents those file-watching hooks as lossy and race-prone.
  - https://support.apple.com/guide/terminal/script-management-with-launchd-apdc6c1077b-5d5d-4d35-9c19-60f2397b2369/mac
  - https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
  - https://keith.github.io/xcode-man-pages/launchd.plist.5.html
- systemd user-service guidance — adopt `systemd --user` service install with a foreground process and reject `.path` units as the only correctness boundary. `.path` can be an optimization later, not the main safety model.
  - https://man7.org/linux/man-pages/man5/systemd.service.5.html
  - https://man7.org/linux/man-pages/man5/systemd.path.5.html
  - https://man7.org/linux/man-pages/man5/systemd.unit.5.html

## 3.2 Internal ground truth (code as spec)
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/workspace/fleki/src/knowledge_graph/frontmatter.py` — the repo-wide markdown metadata codec today; it writes and reads JSON frontmatter.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — the main storage and runtime owner for `topics`, `provenance`, `sources`, `assets`, `receipts`, and `search`, including page writes and PDF render handling.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` — canonical resolution of `data_root`, `config_root`, `state_root`, install-manifest precedence, and legacy graph migration helpers.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` — current public command surface, layout wiring, and current lack of a review-site operator command.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/install_targets.py` — current repo pattern for native runtime installation and filesystem materialization.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/runtime_manifests.py` — current repo pattern for runtime-native manifest reporting.
  - `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py` — current operator install entrypoint.
  - `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py` — generated runtime propagation path that must stay aligned with source changes.
  - `/Users/agents/workspace/fleki/knowledge/topics/indexes/README.md` — indexes are explicitly browse-oriented support pages, which makes them first-class review-wiki material.
  - `/Users/agents/workspace/fleki/knowledge/provenance/README.md`, `/Users/agents/workspace/fleki/knowledge/sources/README.md`, `/Users/agents/workspace/fleki/knowledge/receipts/README.md` — explicit distinction between primary browse pages, provenance, raw source records, and receipts.
- Existing patterns to reuse:
  - `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` — derive new review-wiki paths from `ResolvedKnowledgeLayout` instead of inventing a second root-resolution system.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/install_targets.py` and `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py` — use repo-owned native install surfaces for macOS/Linux service install instead of introducing an unrelated installer.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — preserve the existing semantic-vs-source split and reuse current page/provenance structure instead of transforming the site into a source archive.
  - `/Users/agents/workspace/fleki/skills/knowledge/runtime/src/knowledge_graph/*` — generated runtime mirrors must be refreshed from one source tree rather than hand-edited separately.

## 3.3 Open questions from research
- No blocking open questions remain from research for the first implementation slice.
- This deep-dive pass resolves the previously open branches as follows:
  - Do not export render markdown, render assets, or raw PDFs in v1.
  - Use a pure polling plus digest-gating loop in v1. Do not add filesystem nudges or OS-native path watchers in the first cut.
  - Keep the Quartz template and service-file templates as repo-owned install assets outside `skills/knowledge/runtime`.
  - Do not add a review-wiki config file in v1. Use fixed localhost defaults in code and service templates.
  - Do not add a separate service-management CLI in v1. The repo installer owns install and uninstall.
<!-- arch_skill:block:research_grounding:end -->

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
- The canonical graph root resolves through `resolve_knowledge_layout()` and normally lands under `~/.fleki/knowledge`, with sibling `config_root` and `state_root` under `~/.fleki`.
- Inside `data_root`, the current knowledge tree is split into:
  - `topics/` — semantic markdown pages
  - `provenance/` — supporting notes per source or source bundle
  - `sources/` — copied raw files plus `.record.json` manifests
  - `assets/` — supporting assets
  - `receipts/` — append-only command receipts
  - `search/` — optional helper state
- The checked-in `knowledge/**` tree is reference content and migration seed, not the live mutable graph.
- Topic and provenance markdown pages both use JSON frontmatter enclosed in markdown `---` blocks.
- Topic pages currently carry graph metadata such as `knowledge_id`, `current_path`, `aliases`, `section_ids`, `section_support`, `last_supported_at`, and `last_updated_at`.
- Provenance pages currently carry `provenance_id`, `source_record_paths`, reading-mode summaries, render metadata, and `created_at`.
- Receipt and index pages are also written through the same frontmatter codec today, with keys such as `created_at` or `generated_at`.
- PDF copies can have adjacent `.render.md`, `.render.manifest.json`, and asset directories under `sources/pdf/`.
- Topic page bodies are rendered from semantic sections plus an appended `## Provenance Notes` list in `render_page()`.
- No current review-site directory exists under `state_root`.

## 4.2 Control paths (runtime)
- `knowledge` CLI entrypoints in `cli.py` resolve the layout, build `KnowledgeRepository`, and dispatch to `status`, `search`, `trace`, `save`, or `rebuild`.
- `KnowledgeRepository.initialize_layout()` creates the graph subdirectories and basic README files.
- `apply_save()` is the main mutation flow:
  - validate source bindings and save decision
  - persist source records
  - persist eligible PDF render bundles
  - persist provenance notes
  - apply topic actions
  - write a save receipt
- `search()` and `trace()` are read paths over topics, provenance, and supporting manifests. They are deterministic and exact-or-literal only.
- `status()` reports graph counts and PDF render contract gaps.
- `layout.py` owns legacy graph migration and install-manifest precedence.
- `install.sh` and `scripts/install_knowledge_skill.py` own runtime install and bundled CLI installation.
- There is no current exporter, build daemon, service installer, or local HTTP review server.

## 4.3 Object model + key abstractions
- `ResolvedKnowledgeLayout` and `KnowledgeInstallManifest` define where the graph and install state live.
- `KnowledgeRepository` is the central storage abstraction and the current owner of graph I/O.
- `SourceBinding`, `PdfRenderBundle`, `RebuildPlan`, and `RebuildPageUpdate` define the main structured inputs and support records.
- Topic pages carry semantic identity and section support mappings in frontmatter.
- Provenance pages connect source records to topic sections and capture reading mode, reading gaps, and touched sections.
- Raw source manifests in `sources/**.record.json` capture authority tier, capture time, original path, and storage mode.
- Receipts are append-only command outputs, not browse content.

## 4.4 Observability + failure behavior today
- Invalid inputs fail loudly through `ValidationError`.
- Explicit `data_root`, `config_root`, or `state_root` mismatches against the install manifest fail loudly.
- PDF rendering is an explicit fail-loud boundary before provenance or topic writes for eligible copied PDFs.
- `status()` already reports counts relevant to graph integrity, including lifecycle gaps and PDF render contract gaps.
- There is no current build-health signal, export digest, rebuild log, or service status for a review site.
- There is no current safe-publication layer between the graph and a renderer.

## 4.5 UI surfaces (ASCII mockups, if UI work)
Current human review path:

```text
human reviewer
    |
    +--> open markdown files manually
            |
            +--> topics/                (useful but raw)
            +--> provenance/            (useful but secondary)
            +--> sources/               (unsafe to expose directly)
            +--> receipts/              (noise for human browsing)
```

Current agent path:

```text
agent
  -> knowledge search
  -> knowledge trace
  -> knowledge save / rebuild
  -> KnowledgeRepository
  -> canonical graph under data_root
```
<!-- arch_skill:block:current_architecture:end -->

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
- `data_root` remains the canonical graph and keeps the same semantic-vs-source split.
- Canonical topic and provenance markdown pages move to YAML frontmatter in place by porting the existing KB directly.
- A new review-wiki area lives under `state_root`, for example:

```text
<state_root>/review-wiki/
  quartz/
    package.json
    quartz.config.ts
    content/
    public/
  export-digest.json
  build.log
```
- Repo-owned template files for Quartz config and service templates live in source-controlled Fleki paths and are copied or synced into `state_root` during install.

## 5.2 Control paths (future)
- Frontmatter cutover:
  - Fleki ports canonical graph markdown pages from JSON frontmatter to YAML frontmatter once.
  - All page writers and readers then use one YAML codec only.
- Export path:
  - The daemon resolves the live layout.
  - It scans only allowlisted graph inputs that can affect browse output:
    - `topics/**/*.md`
    - `topics/indexes/**/*.md`
    - `provenance/**/*.md`
  - It excludes `sources/**`, `receipts/**`, `.record.json`, raw copied assets, raw PDFs, render markdown, render assets, and other non-exported state by default.
  - It normalizes the exported browse set and computes a deterministic digest.
  - If the digest changed, it materializes the Quartz `content/` tree, runs a static Quartz build, and atomically replaces the built `public/` tree.
  - If the digest did not change, it skips export and build work.
- Serve path:
  - A Fleki-owned foreground daemon serves the built site from `public/` on `127.0.0.1:4151`.
  - The service keeps the last good built site if a later export or Quartz build fails.
- Install path:
  - Repo install surfaces preflight Python, Node, and npm for the optional review feature.
  - The installer writes per-user service files for macOS LaunchAgent or Linux systemd user service.
  - Those services invoke `uv run --project <repo_root> python -m knowledge_graph.review_wiki.daemon`; they do not rely on Quartz preview mode.

## 5.3 Object model + abstractions (future)
- `frontmatter.py` becomes a YAML codec while keeping the same Python dict interface for callers.
- There is no review-wiki config file in v1.
- Fixed runtime constants in code own the few settings this feature needs in v1:
  - host: `127.0.0.1`
  - port: `4151`
  - poll_seconds: `5`
- Everything else that could have become a toggle in v1 is fixed by code policy instead:
  - provenance is first-class and always exported
  - receipts are never exported
  - render markdown, raw PDFs, and render assets are never exported in v1
- New review-wiki runtime modules under `src/knowledge_graph/review_wiki/`:
  - layout helpers derived from `ResolvedKnowledgeLayout`
  - exporter that maps graph pages into Quartz content
  - digest manager for semantic build gating
  - daemon that owns export, build, and local serving
  - service-file renderer for launchd and systemd user units
- Manual foreground runs use the same Python module entrypoint the service uses.
- The exported site stays plain markdown plus explicitly allowed assets. Fleki does not create a second semantic database for the viewer.
- Receipt markdown stays in the graph as YAML-frontmatter markdown for internal consistency, but it is always excluded from the exported review tree.

## 5.4 Invariants and boundaries
- `KnowledgeRepository` remains the only writer of canonical graph content.
- Quartz and the review daemon read only derived or exported content.
- The Quartz content root is always under `state_root`, never `data_root`.
- Export is allowlist-based, not denylist-based.
- Provenance pages are review content. Raw source records are not.
- Page dates shown by Quartz come from graph metadata, not export-time filesystem mtimes.
- The canonical frontmatter format is YAML only after migration.
- The implementation keeps one required export path and fixed localhost runtime settings in v1.
- The repo installer is the only supported install and uninstall surface for the review site in v1.
- The service must fail loudly on missing Node/npm, broken Quartz build, or invalid config rather than silently disabling updates.
- No compatibility shim keeps JSON frontmatter live after the migration completes.

## 5.5 UI surfaces (ASCII mockups, if UI work)
Proposed browse IA:

```text
/                          Home
|- /topics/                Semantic topic tree
|  |- /knowledge-system/
|  |  |- /runtime-integration
|  |  `- /semantic-organization
|- /indexes/
|  |- /by-topic
|  |- /recent-changes
|  `- /unresolved-questions
```

Topic page:

```text
+------------------------------------------------------+
| Topic title                                          |
| Summary / current understanding                      |
|                                                      |
| Supported sections                                   |
| - section heading                                    |
| - section heading                                    |
|                                                      |
| Provenance links                                     |
| - provenance note                                    |
| - provenance note                                    |
+------------------------------------------------------+
```

Provenance page:

```text
+------------------------------------------------------+
| Provenance title                                     |
| Summary                                              |
| Reading mode / gaps / sensitivity                    |
| Contributed topic sections                           |
+------------------------------------------------------+
```
<!-- arch_skill:block:target_architecture:end -->

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## Change map (table)
| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| ---- | ---- | ------------------ | ---------------- | --------------- | --- | ------------------ | -------------- |
| Frontmatter codec | `/Users/agents/workspace/fleki/src/knowledge_graph/frontmatter.py` | `dump_frontmatter`, `split_frontmatter` | Writes and reads JSON frontmatter inside markdown fences | Hard-cut to YAML frontmatter with the same dict-level caller contract and port existing KB pages in place | Quartz expects YAML or TOML frontmatter; mixed formats create needless drift | Canonical markdown pages use YAML only | new codec tests; `tests/test_cli.py`; `tests/test_save.py`; `tests/test_search_trace_status.py`; `tests/test_layout.py` |
| Generated runtime mirror | `/Users/agents/workspace/fleki/skills/knowledge/runtime/src/knowledge_graph/frontmatter.py` | mirrored codec | Generated runtime mirrors JSON frontmatter behavior | Refresh from source after YAML cutover | Installed runtime must match source behavior | runtime mirror stays generated, not hand-edited | `tests/test_skill_package.py` |
| Page writers | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | topic, provenance, receipt page writes using `dump_frontmatter` | Writes JSON-frontmatter markdown for topics and provenance | Ensure topic/provenance writes emit YAML and keep exact metadata fields required for review dates, aliases, publish flags, and section support | Canonical page format changes and review site depends on stable metadata | topic and provenance page metadata stay graph-owned and Quartz-readable | `tests/test_save.py`; `tests/test_search_trace_status.py`; `tests/test_cli.py` |
| Receipt writers | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_write_save_receipt`, `_write_receipt` | Writes receipt markdown in the same general frontmatter style | Port receipts to YAML-frontmatter markdown too and keep them always excluded from export | one markdown metadata format is simpler than special-casing receipts | receipts remain non-browse support state | `tests/test_cli.py`; receipt assertions in other tests |
| Layout migration | `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` | `_rewrite_frontmatter_paths`, legacy graph migration helpers | Rewrites paths inside frontmatter and bodies during root migration | Update migration logic to parse and rewrite YAML frontmatter and add one explicit frontmatter port step instead of old/new split support | Existing migration code touches markdown metadata directly | one canonical migration path, no permanent compatibility shim | `tests/test_layout.py` |
| Page rendering | `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` | `render_page` | Renders semantic topic sections and an appended provenance-notes section | Preserve the meaning-first page body shape while ensuring provenance links remain Quartz-friendly and stable after YAML cutover | the review site should consume the existing topic-body shape rather than invent a second body format | topic pages stay semantically primary with explicit provenance links | `tests/test_save.py`; new exporter tests |
| CLI surface | `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | `main`, `_build_parser`, `_add_common_layout_args` | Exposes only `status`, `search`, `trace`, `save`, `rebuild` | Keep current five verbs untouched | Viewer install and daemon management are not graph verbs | existing graph CLI stays unchanged | existing CLI tests stay stable |
| Package metadata | `/Users/agents/workspace/fleki/pyproject.toml` | project dependencies | Installs current CLI and docling support | Add a YAML parser dependency if needed for the frontmatter cutover and daemon module imports; do not add a separate review-site console script in v1 | frontmatter cutover needs package support, but a second CLI is unnecessary | repo package stays smaller | packaging checks |
| Runtime sync | `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py` | runtime package generation | Mirrors `src/knowledge_graph/**` into generated runtime bundle and renders runtime README | Keep the review-site implementation out of the generated agent runtime bundle | the review site is an operator feature, not part of the agent skill runtime | runtime bundle stays focused on the graph CLI | `tests/test_skill_package.py` |
| Repo installer | `/Users/agents/workspace/fleki/install.sh` | installer entrypoint | Runs the Python installer only | Add one explicit optional flag for review-wiki install, then delegate to the installer script | user wants easy native install on macOS and Linux without a second setup flow | optional review-wiki install remains repo-owned and explicit | installer smoke tests |
| Installer logic | `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py` | install flow | Installs CLI and runtime bundles into detected agent surfaces | Preflight optional Node/npm requirements, materialize the repo-owned Quartz template into `state_root`, and install or remove native service files that run the daemon module directly | native install belongs in the existing repo install path | one Fleki-owned optional install story on this machine | new installer tests |
| Install docs | `/Users/agents/workspace/fleki/README.md` | install and usage docs | Documents current graph and installer | Add optional review-wiki install, Node requirement, local URL, and security boundary notes | operator needs one clear doc path | repo docs describe optional review feature honestly | doc-oriented assertions in `tests/test_skill_package.py` if added |
| Skill docs | `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` | skill contract | Documents the graph verbs and current storage contract | Update only any wording affected by the YAML cutover; do not add review-site behavior to the agent skill | avoid drifting agent-facing docs | graph skill stays focused on graph use, not site ops | `tests/test_skill_package.py` |
| Runtime README | `/Users/agents/workspace/fleki/skills/knowledge/runtime/README.md` | generated runtime docs | Documents the installed CLI and graph contract | Regenerate after frontmatter changes; do not document review-site behavior there | the review site is not part of the agent runtime bundle | generated runtime docs stay focused | `tests/test_skill_package.py` |
| Reference content | `/Users/agents/workspace/fleki/knowledge/**` | checked-in topic/provenance pages | Reference tree currently uses JSON frontmatter | Convert checked-in topic and provenance pages to YAML frontmatter during the same cutover | checked-in examples and migration seed must match canonical format | one canonical markdown format across repo content | tests that inspect reference files or migration logic |
| Review exporter | `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/exporter.py` | new module | Does not exist | Add exporter that builds Quartz-ready content from allowlisted topic, index, and provenance pages through one required export path | current repo lacks safe human browse output | exporter owns inclusion rules and normalized page shaping | new exporter tests |
| Review digest gate | `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/digest.py` | new module | Does not exist | Add deterministic export digest calculation and last-built cache management | rebuilds must track semantic output changes, not raw churn | export digest is the correctness boundary for rebuild decisions | new digest tests |
| Review daemon | `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/daemon.py` | new module | Does not exist | Add foreground loop for scan, export, build, atomic publish, and local serving on fixed localhost defaults | required for optional auto-regenerating browse site | one foreground process, fail loud, keep last good site | new daemon tests |
| Service templates | `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/service.py` | new module | Does not exist | Render launchd plist and systemd user-service files from one config model | user wants easy native install on macOS and Linux | repo-owned native service files | new service-template tests |
| Quartz template | `/Users/agents/workspace/fleki/templates/review-wiki/` | new install asset | No Quartz project exists | Add a pinned repo-owned Quartz template/config and sync it into `state_root` during optional install | avoid depending on an interactive scaffold | Quartz project is derived install state | installer smoke tests |
| Existing architecture docs | `/Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md` | optional-viewer mentions | Says viewer export is optional later | Add a relation or supersession note if implementation changes the current downstream-viewer assumptions materially | prevent doc drift across architecture docs | one current owner for review-wiki architecture | doc review only |

## Migration notes
* Deprecated APIs (if any):
  - JSON-frontmatter graph pages are deprecated immediately once the YAML migration lands.
  - Direct manual assumptions that a renderer can safely consume `knowledge/**` or `data_root` directly are deprecated immediately.
  - Any split old/new page-format support introduced during migration is temporary at most and should be removed before the feature is considered complete.
* Delete list (what must be removed; include superseded shims/parallel paths if any):
  - Any temporary JSON-frontmatter compatibility parser kept alive after migration.
  - Any direct-Quartz-on-raw-graph experimentation paths.
  - Any service mode that shells out to `quartz build --serve` as the installed long-running path.

## Pattern Consolidation Sweep (anti-blinders; scoped by plan)
| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| ---- | ------------- | ---------------- | ---------------------- | ------------------------------------- |
| Frontmatter | `/Users/agents/workspace/fleki/skills/knowledge/runtime/src/knowledge_graph/frontmatter.py` | YAML-only canonical page metadata | keeps installed runtime aligned with source | include |
| Migration | `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` | YAML-aware graph migration and path rewriting | prevents root migration from silently breaking page metadata | include |
| Reference pages | `/Users/agents/workspace/fleki/knowledge/topics/**`, `/Users/agents/workspace/fleki/knowledge/provenance/**` | YAML-only page examples | prevents checked-in examples from drifting from live format | include |
| Install docs | `/Users/agents/workspace/fleki/README.md`, `/Users/agents/workspace/fleki/skills/knowledge/install/README.md` | optional review-wiki install story and safety boundary | prevents operators from pointing Quartz at raw graph data | include |
| Runtime docs | `/Users/agents/workspace/fleki/skills/knowledge/runtime/README.md` | regenerated frontmatter wording after cutover | prevents stale bundle docs | include |
| Historical architecture docs | `/Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md` | relation note to this plan | prevents two docs from appearing to own viewer architecture | include |
| Agent-facing skill behavior | `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` | keep review-site management outside the five graph verbs | prevents scope creep into agent contract | include |
| Search and trace | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | keep semantic browse and exact trace behavior unchanged | prevents review site work from mutating graph semantics | exclude |
<!-- arch_skill:block:call_site_audit:end -->

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan. No fallbacks or runtime shims. The graph remains the only writer. The review site stays derived state under `state_root`. Prefer programmatic checks per phase and keep manual browser QA for finalization.

## Phase 1 — Hard-cut page format and port the existing KB

Status: COMPLETE

Completed work:
- Cut the canonical frontmatter codec over to YAML and added a migration-only JSON reader for one-time graph porting.
- Ported the checked-in KB topic, provenance, and receipt markdown files to YAML and rewrote legacy `knowledge/...` path prefixes in the reference tree.
- Added frontmatter regression tests and updated layout migration coverage for YAML output.
- Removed the always-on `port_graph_frontmatter(self.knowledge_root)` call from normal repository startup so ordinary reads no longer rewrite legacy JSON pages in place.
- Tightened graph markdown loads to fail loudly on invalid frontmatter instead of silently skipping bad topic, provenance, or receipt pages.

* Goal:
  Make one canonical markdown metadata format real everywhere the graph writes or reads human-browseable pages.
* Work:
  - Change `/Users/agents/workspace/fleki/src/knowledge_graph/frontmatter.py` from JSON frontmatter to YAML frontmatter while keeping the dict-level API stable for callers.
  - Update `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` and `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` to read, write, and migrate YAML-frontmatter pages correctly.
  - Preserve the current topic-body shape in `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` so the page body format does not change while the metadata format changes.
  - Port checked-in reference content to YAML in these areas:
    - `/Users/agents/workspace/fleki/knowledge/topics/**`
    - `/Users/agents/workspace/fleki/knowledge/provenance/**`
    - `/Users/agents/workspace/fleki/knowledge/topics/indexes/**`
    - receipt exemplars still carried in `/Users/agents/workspace/fleki/knowledge/receipts/**`
  - Refresh the generated runtime bundle only for the graph-runtime pieces that still belong there by running `/Users/agents/workspace/fleki/scripts/sync_knowledge_runtime.py`.
  - Update only graph-facing docs that describe the old JSON-frontmatter shape:
    - `/Users/agents/workspace/fleki/README.md`
    - `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`
    - `/Users/agents/workspace/fleki/skills/knowledge/runtime/README.md`
* Verification (smallest signal):
  - Targeted unittest coverage for frontmatter round-trip and graph read/write paths:
    - `tests/test_cli.py`
    - `tests/test_save.py`
    - `tests/test_search_trace_status.py`
    - `tests/test_layout.py`
    - `tests/test_skill_package.py`
  - Add one focused new frontmatter codec test file if the existing suites do not make YAML round-trip failures obvious enough.
* Docs/comments (propagation; only if needed):
  - Add one short boundary comment in the frontmatter codec if the YAML cutover introduces a non-obvious parsing rule.
  - Update repo and runtime docs only where they currently describe the old JSON-frontmatter shape.
* Exit criteria:
  - Canonical graph pages are YAML-frontmatter pages.
  - The checked-in KB reference content is ported to the same format.
  - No JSON-frontmatter compatibility path is left alive in normal operation.
* Rollback:
  - Revert the YAML cutover as one unit.
  - Do not introduce a mixed JSON/YAML steady state as a rollback substitute.

## Phase 2 — Build the filtered export and digest gate

Status: COMPLETE

Completed work:
- Added the `review_wiki` package with derived-state layout helpers, a filtered exporter, and a deterministic digest helper.
- Added the repo-owned Quartz overlay under `templates/review-wiki/`.
- Kept review-wiki code out of the generated agent runtime bundle and added tests that enforce that exclusion.

* Goal:
  Produce a deterministic Quartz content tree from the live graph without exposing raw evidence or adding a second knowledge model.
* Work:
  - Create the new review-wiki package under `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/`.
  - Add `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/exporter.py` to export only:
    - `topics/**/*.md`
    - `topics/indexes/**/*.md`
    - `provenance/**/*.md`
  - Enforce the export deny set in code:
    - `sources/**`
    - `receipts/**`
    - `.record.json`
    - raw PDFs
    - render markdown
    - render assets
  - Add `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/digest.py` to compute a deterministic digest over exported semantic content and skip rebuild work when the exported result would not change.
  - Add the repo-owned Quartz template under `/Users/agents/workspace/fleki/templates/review-wiki/` with the minimum files needed to build and serve the exported content tree.
  - Sync the template into `<state_root>/review-wiki/quartz/` as derived state rather than editing it in place under source control.
  - Keep the review-site implementation out of `skills/knowledge/runtime/**`.
* Verification (smallest signal):
  - Add focused tests for exporter inclusion and exclusion behavior, for example in:
    - `tests/test_review_wiki_exporter.py`
  - Add focused tests for digest stability and no-op behavior when only excluded graph state changes, for example in:
    - `tests/test_review_wiki_digest.py`
  - Confirm the generated agent runtime bundle does not absorb review-site code or template assets.
* Docs/comments (propagation; only if needed):
  - Add one short exporter comment at the allowlist boundary and one short digest comment explaining why semantic digesting, not file watching, decides rebuilds.
* Exit criteria:
  - The exporter can materialize a Quartz content tree from the live graph.
  - Excluded graph state is not present in the exported tree.
  - Receipt-only and other excluded changes do not trigger rebuild work.
* Rollback:
  - Remove the review-wiki export modules and derived `state_root/review-wiki/` output.
  - Leave the canonical graph untouched.

## Phase 3 — Add the local daemon and native install path

Status: COMPLETE

Completed work:
- Added the foreground review-wiki daemon with digest-gated export, Quartz build staging, atomic public-site replacement, and local HTTP serving.
- Added launchd and systemd user-service renderers plus installer support for `--review-wiki` and `--remove-review-wiki`.
- Added Node/npm review-wiki preflight checks, overlay materialization, and README documentation for the local review site.
- Completed the real macOS machine smoke for install, build, local serving, and auto-regeneration after a reversible topic-page edit.
- Fixed the real installer and runtime issues uncovered by that smoke:
  - switched the Quartz pin from a hanging git dependency to a direct GitHub tarball
  - ported existing graph frontmatter explicitly during install before starting the daemon
  - copied the Quartz runtime scaffold into the workspace and aligned the local config imports
  - replaced the broken Python 3.12 `http.server` path on this host with a Fleki-owned raw-socket static file server

Manual QA (non-blocking):
- Install the feature with `./install.sh --review-wiki` on one Linux host.
- Open `http://127.0.0.1:4151` and confirm the site serves.
- Change excluded graph content such as receipts and confirm no rebuild.
- Remove the feature with `./install.sh --remove-review-wiki`.

* Goal:
  Make the review site installable on a machine and keep it regenerated automatically from exported semantic changes.
* Work:
  - Add `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/daemon.py` as the foreground process that:
    - polls every 5 seconds
    - computes the export digest
    - rebuilds Quartz when needed
    - serves the built site on `127.0.0.1:4151`
  - Add `/Users/agents/workspace/fleki/src/knowledge_graph/review_wiki/service.py` to render native per-user service files for:
    - macOS LaunchAgent
    - Linux systemd user service
  - Extend `/Users/agents/workspace/fleki/install.sh` and `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py` with these explicit installer flags:
    - `--review-wiki`
    - `--remove-review-wiki`
  - Preflight Node/npm before installing the review feature and fail loudly if the host is missing required tooling.
  - Materialize the Quartz template into `state_root`, install or remove service files, and make those services run `python -m knowledge_graph.review_wiki.daemon` from the repo project.
  - Keep the agent skill runtime bundle and its docs free of review-site behavior.
  - Add the repo doc updates needed for the new installer flags and localhost URL.
* Verification (smallest signal):
  - Add focused tests for launchd plist and systemd unit rendering, for example in:
    - `tests/test_review_wiki_service.py`
  - Add focused tests for installer flag handling and Node/npm preflight behavior, for example in:
    - `tests/test_review_wiki_install.py`
  - Manual local smoke on one macOS host and one Linux host:
    - install the feature with `./install.sh --review-wiki`
    - confirm the site serves on `127.0.0.1:4151`
    - mutate exported graph content
    - confirm rebuild occurs
    - uninstall the feature cleanly with `./install.sh --remove-review-wiki`
* Docs/comments (propagation; only if needed):
  - Update `/Users/agents/workspace/fleki/README.md` with the optional install command, localhost URL, and security boundary.
  - Add one short daemon comment at the polling-plus-digest boundary if needed.
* Exit criteria:
  - The feature can be installed or removed through the repo installer.
  - The daemon rebuilds when exported semantic content changes and stays idle when it does not.
  - The site is reachable locally on `127.0.0.1:4151`.
* Rollback:
  - Remove the installed service files and derived review-wiki state under `state_root`.
  - Leave the canonical graph and graph CLI intact.
<!-- arch_skill:block:phase_plan:end -->

# 8) Verification Strategy (common-sense; non-blocking)

Verification stays small and behavior-first.

- Use targeted `unittest` coverage while iterating:
  - frontmatter and graph read/write paths for the YAML cutover
  - exporter allowlist and exclusion behavior
  - digest no-op behavior for excluded changes
  - daemon and service-template behavior where it has a stable smallest signal
- Prefer new focused test modules for the review site instead of bloating existing graph-contract suites once the new package exists.
- Run the full repo suite plus compile after implementation is complete because this feature changes `src/knowledge_graph/**`:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
  - `.venv/bin/python -m compileall src`
- Prefer behavior assertions over deletion-proof tests, screenshot tests, or visual-constant checks.
- Keep manual verification short and final:
  - install the feature
  - open `http://127.0.0.1:4151`
  - change exported graph content
  - confirm rebuild
  - change excluded graph content such as receipts
  - confirm no rebuild
  - remove the feature cleanly

# 9) Rollout / Ops / Telemetry

Rollout is intentionally small.

- The feature is off unless the repo installer is invoked with `./install.sh --review-wiki`.
- The repo installer owns install and uninstall of the review-site service.
- Removal uses `./install.sh --remove-review-wiki`.
- The service is per-user and local to this machine:
  - macOS via LaunchAgent
  - Linux via `systemd --user`
- Runtime defaults are fixed in v1:
  - bind host: `127.0.0.1`
  - port: `4151`
  - poll interval: `5` seconds
- Derived site state, digest state, and build logs live only under `state_root/review-wiki/`.
- No extra telemetry system is added in v1.
- Failures must be loud in installer output, service logs, or daemon stderr. The graph remains canonical even if the review site is broken.

# 10) Decision Log (append-only)

- 2026-04-03: Created the dedicated review-wiki plan doc instead of reusing the broader graph or install/root plans. Reason: the review wiki has its own storage-safety rules, frontmatter cutover, daemon behavior, and native service install concerns.
- 2026-04-03: Adopted Quartz as the first renderer and rejected direct reads from the raw graph root. Reason: Quartz matches the browse goal well, but its content-folder asset behavior makes a filtered export tree mandatory.
- 2026-04-03: Adopted YAML as the only canonical page frontmatter format after migration. Reason: the current graph is small enough to migrate cleanly, and keeping JSON plus YAML would create avoidable drift.
- 2026-04-03: Adopted a Fleki-owned digest-gated daemon as the correctness boundary and rejected launchd or systemd path watchers as the correctness boundary. Reason: OS watch hooks are lossy and renderer rebuilds must follow exported semantic changes, not raw file churn.
- 2026-04-03: Tightened the plan to prefer direct KB porting and required rules over split support. Reason: the existing KB is small, and carrying old/new paths or optional compatibility modes would add code and drift without enough value.
- 2026-04-03: Removed extra optional reviewer features from the v1 plan. Reason: the minimum useful version is just YAML page porting, filtered export of topic/index/provenance pages, polling plus digest gating, a fixed localhost daemon, and repo-owned native service install.
- 2026-04-03: Locked the execution order as three phases: YAML cutover first, filtered export plus digest second, daemon plus native install third. Reason: this is the smallest depth-first sequence that keeps the graph stable while the review site comes online.
- 2026-04-03: Locked the installer interface to `./install.sh --review-wiki` and `./install.sh --remove-review-wiki`. Reason: the feature needs one explicit repo-owned on/off path, and fixed flag names are simpler than a second CLI or a config-driven installer.
- 2026-04-03: Implemented the Quartz workspace as a small repo-owned overlay plus a pinned Quartz Git dependency instead of vendoring the full Quartz source tree. Reason: it keeps the Fleki repo smaller while still pinning the renderer version and letting the installer materialize a full build workspace under `state_root`.
- 2026-04-03: Removed the startup-time JSON frontmatter auto-port and made graph markdown loads fail loudly on invalid frontmatter. Reason: the plan requires one canonical YAML path in normal operation, and silently skipping bad pages would hide broken graph state instead of surfacing it.
- 2026-04-03: Changed the Quartz install pin from a git dependency to a direct GitHub tarball and copied the installed Quartz scaffold into the workspace root during install. Reason: the real macOS install hung on the git dependency path, and Quartz expects a local `quartz/` scaffold in the build workspace.
- 2026-04-03: Added an explicit graph frontmatter port step to the installer before the review daemon starts. Reason: the live installed graph still contained legacy JSON-frontmatter pages, and normal runtime remains strict by plan.
- 2026-04-03: Replaced the review daemon's `http.server` serving path with a Fleki-owned raw-socket static server. Reason: the real Python 3.12 runtime on this macOS host built Quartz correctly but failed to serve even a trivial `http.server`, while raw sockets worked correctly.

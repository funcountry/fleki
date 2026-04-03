---
title: "Fleki - Cross-Agent Markdown Knowledge Graph - Architecture Plan"
date: 2026-04-02
status: complete
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: new_system
related:
  - /Users/agents/workspace/agents/README.md
  - /Users/agents/workspace/agents/AGENTS.md
  - /Users/agents/workspace/paperclip_agents/AGENTS.md
  - /Users/agents/workspace/paperclip_agents/PRINCIPLES.md
  - /Users/agents/workspace/paperclip_agents/vendor/paperclip/skills/paperclip/SKILL.md
  - /Users/agents/workspace/paperclip_agents/vendor/paperclip/packages/adapters/codex-local/src/index.ts
---

> Supersession note (2026-04-03): This doc remains the architecture basis for the shared knowledge model, provenance rules, and semantic graph behavior. Install/root ownership and downstream runtime adoption are now governed by [CENTRALIZED_KNOWLEDGE_INSTALL_AND_ROOT_PLAN_2026-04-03.md](/Users/agents/workspace/fleki/docs/CENTRALIZED_KNOWLEDGE_INSTALL_AND_ROOT_PLAN_2026-04-03.md).

# TL;DR

- **Outcome:** Build one runtime-neutral semantic markdown knowledge graph on disk, where the primary thing we organize is company knowledge, not source artifacts. Raw Codex sessions, Hermes materials, Paperclip materials, PDFs, images, and docs are preserved as evidence behind semantic knowledge pages with explicit provenance notes.
- **Problem:** The company already produces repeated learnings about runtime behavior, workflow law, lesson design, copy/style, UX baselines, release runbooks, and architecture tradeoffs, but those learnings are trapped inside sessions, repo docs, and scattered artifacts. Agents keep relearning the same things because there is no shared semantic knowledge graph, no provenance-preserving extraction layer, and no common agent-facing skill surface for save/search/trace over what the company knows.
- **Approach:** Treat highly capable local multimodal agents as the primary engine of the system. The public interface remains `knowledge save/search/trace/rebuild/status`, but the default operating model is simple: the agent runs the shared `knowledge` skill locally, reads the source files directly from the same filesystem, uses the active local model/runtime capabilities that are documented and verified for the current host, preserves the raw source plus provenance, updates the semantic pages, and uses `rebuild` for wider graph reorganization. Scripts, harnesses, indexes, or transport layers are optional later helpers only if explicitly approved; they are not the architectural center.
- **Plan:** Lock contracts plus the shared `knowledge` skill package first; then prove a same-host direct Codex `save` slice on real local materials, expand that same path to images/PDFs/runtime-origin artifacts, add `search/trace/status`, add `rebuild`, and only then wire Hermes plus Paperclip reuse around the same on-disk graph.
- **Non-negotiables:**
  - The core contract must not depend on Hermes, Paperclip, OpenClaw, or any single runtime being the permanent executor.
  - The primary executor model is a local multimodal LLM agent running a local skill against the same filesystem.
  - Do not design local operation around transport, services, or deterministic preprocessing layers that the agents do not need.
  - No helper scripts, harnesses, indexers, converters, or other deterministic support subsystems may be introduced without explicit approval from Amir.
  - The system must organize semantic knowledge first, preserve source provenance second, and never confuse the support archive for the primary browsing model.
  - The system must preserve original source materials, authority tier, and provenance notes; the compiler may reorganize semantic pages, not silently destroy or overwrite evidence.
  - Runtime-specific packaging must stay thin and must never become a pretext for per-runtime storage semantics.
  - The markdown tree must stay human-readable on disk, semantically legible, and searchable without a hidden control plane.
  - The system must model live doctrine, runtime truth, historical support, and derived knowledge as different classes of thing instead of flattening them into equal notes.
  - Every meaningful knowledge object should carry provenance notes that link back to supporting source materials.
  - The secondary viewer is optional; save/search/trace over the semantic knowledge graph are the primary value.
  - The first shipped slice is same-host first, but the data model must not paint us into a local-only corner.

<!-- arch_skill:block:implementation_audit:start -->
# Implementation Audit (authoritative)
Date: 2026-04-03
Verdict (code): COMPLETE
Manual QA: complete (non-blocking)

## Code blockers (why code is not done)
- None.
- Audit evidence checked:
  - `python3 -m unittest discover -s tests -p 'test_*.py' -v`
  - `python3 -m compileall src`
  - repo-local `search` / `trace` / `status` over the current `knowledge/**` tree
  - `knowledge/search/README.md` remained the only default search-support-state file
  - published `knowledge` skill mirrors across Codex, Hermes, Paperclip, and trusted Hermes local paths were byte-identical real files
  - `HERMES_HOME=/Users/agents/.hermes/profiles/agent_coder hermes skills list` showed `knowledge` as an installed local skill on this host

## Reopened phases (false-complete fixes)
- None.

## Missing items (code gaps; evidence-anchored; no tables)
- None.

## Non-blocking follow-ups (manual QA / screenshots / human verification)
- None.
<!-- arch_skill:block:implementation_audit:end -->

---

<!-- arch_skill:block:planning_passes:start -->
<!--
arch_skill:planning_passes
deep_dive_pass_1: done 2026-04-02
external_research_grounding: done 2026-04-02
deep_dive_pass_2: done 2026-04-02
deep_dive_pass_3: done 2026-04-02
recommended_flow: deep dive -> external research grounding -> deep dive again -> phase plan -> implement
note: This is a warn-first checklist only. It should not hard-block execution.
-->
<!-- arch_skill:block:planning_passes:end -->

---

# 0) Holistic North Star

## 0.1 The claim (falsifiable)
> If we build a runtime-neutral markdown knowledge graph in this repo where semantic knowledge pages are primary, raw source materials are preserved behind provenance notes, and one shared local `knowledge` skill exposes `save`, `search`, `trace`, `rebuild`, and `status`, then direct Codex and Hermes caller surfaces on this host will be able to inspect local markdown, image, and session material directly on disk, handle local PDF material through the same skill where the active runtime surface exposes documented file input, file all of that into the same semantic graph with evidence-backed provenance, retrieve and trace the same knowledge without per-runtime forks, and reorganize the graph over time without needing a deterministic transport or preprocessing harness to make the system work.

## 0.2 In scope
- UX surfaces (what users will see change):
  - A public shared skill surface, `knowledge`, that teaches five top-level verbs:
    - `save`
    - `search`
    - `trace`
    - `rebuild`
    - `status`
  - A human-readable on-disk knowledge tree whose primary pages are semantic topics, playbooks, decisions, glossaries, and topic indexes, backed by separate provenance notes and raw source records.
  - Search/trace answers that cite concrete knowledge pages plus supporting provenance/source paths and show authority tier instead of returning uncited free text.
  - Save receipts that tell the caller what source was preserved, what knowledge was extracted, what semantic page sections were touched, and whether a rebuild is pending.
  - An optional later viewer surface, such as Quartz or another static/wiki presentation layer, built on the same markdown tree rather than replacing it.
- Technical scope (what code will change):
  - A canonical storage model for semantic knowledge pages, provenance notes, preserved raw source records, media assets, authority-tier metadata, and optional support state.
  - Clean caller-integration seams for local Codex, Paperclip, Hermes, and OpenClaw-class surfaces so each runtime can invoke the same local `knowledge` contract without inventing its own storage rules or semantic taxonomy.
  - A local same-host ingest path for at minimum:
    - markdown/text docs
    - PDF inputs
    - standalone images
    - representative Hermes-origin runtime artifacts
    - representative Paperclip-origin doctrine/runtime artifacts
    - representative Codex-origin session traces, docs, and skill materials
  - A skill-first ingestion workflow that tells local agents how to inspect those files directly, preserve provenance honestly, and record any reading limitations.
  - An incremental compiler/reorganizer that can create and revise semantic pages, provenance notes, indexes, backlinks, summaries, and placements in the derived markdown tree.
  - A search/retrieval surface designed for frequent agent use, with local agent reasoning over the semantic markdown graph as the default and any helper retrieval machinery explicitly approval-gated.
  - A remote-ready data model that does not require a rewrite if later we add non-local submission paths.

## 0.3 Out of scope
- UX surfaces (what users must NOT see change):
  - A manual wiki-editing workflow as the primary authoring mode.
  - A promise that every agent type is fully auto-wired into the system on day one.
  - A polished public viewer or publishing site as a release blocker for the first slice.
  - A generic “ask anything and I’ll write the whole final answer for you” skill that tries to replace ordinary agent reasoning.
- Technical scope (explicit exclusions):
  - Hard-coding the first version to a Hermes daemon, a Paperclip-only workflow, or any other single runtime-specific execution model.
  - Multi-host sync, remote auth, distributed job scheduling, or a fleet-wide ingestion mesh in v1.
  - Fine-tuning, embedding-heavy infrastructure, or a database-first design as a prerequisite for the first useful version.
  - Designing local operation around MCP, a CLI service layer, OCR pipelines, retrieval indexes, or other deterministic infrastructure before the LLM-first local skill path has proved insufficient.
  - Adding helper scripts, helper harnesses, or conversion/indexing daemons without explicit approval from Amir.
  - Perfect visual fidelity for arbitrary PDFs and images beyond what is practical in a markdown-first knowledge compiler.
  - Prompt-telemetry-driven autonomous taxonomy changes before the basic archive/compile/search loop is trustworthy.
  - A skill-owned final-answer writer that outranks the citing/search layer; the caller agent should still own the final prose answer when one is needed.
  - A source-family-first browse model where `codex/`, `paperclip/`, `hermes/`, or `pdfs/` becomes the user-facing information architecture.

## 0.4 Definition of done (acceptance evidence)
- A single canonical repo-local knowledge tree exists and is readable on disk without internal tribal knowledge.
- The system exposes one shared local skill surface with at least:
  - `save`
  - `search`
  - `trace`
  - `rebuild`
  - `status`
- The integration model explicitly covers local Codex, Paperclip, Hermes, and OpenClaw-class callers as thin packaging layers into the same public contract rather than as competing implementations, and it names the clean seam for each runtime instead of hand-waving "integration later."
- From this host, direct Codex and Hermes caller surfaces can use the same local ingest/search/trace contract against the same underlying store in v1, while Paperclip cleanly distributes the same skill path and OpenClaw remains a follow-on thin alias path.
- Ingesting a sample markdown note, a sample image, at least one representative Codex session or runtime-origin artifact, and a sample PDF through a host-validated runtime surface that exposes documented PDF file input works through direct local agent inspection, preserves the original source record, writes provenance notes, and yields linked semantic knowledge pages in the compiled graph.
- Search can retrieve those knowledge pages by concept and intent and return concrete knowledge-page citations plus supporting provenance/source paths with authority tier clearly shown.
- `trace` can explain where a claim or page came from, what source materials back it, and which sources are live truth versus mirror/history/runtime readback.
- Re-running the compiler can reorganize semantic graph placement and backlinks without losing source records, provenance, or authority metadata.
- Evidence plan (common-sense; non-blocking):
  - Primary signal: one end-to-end local `save` flow for markdown, image, one real session/runtime-origin artifact, and one PDF through a host-validated runtime surface that exposes documented PDF file input into the same store, using direct local agent inspection rather than bespoke preprocessing infrastructure, followed by one compile pass that produces semantic pages, provenance notes, and preserved assets.
  - Secondary signal: one `search` invocation and one `trace` invocation from Hermes against material filed by direct Codex, with path citations and correct authority tagging.
  - Default: do NOT add bespoke orchestration frameworks, negative-value deletion tests, screenshot bureaucracy, viewer-first QA harnesses, or approval-free helper scripts/harnesses for the first slice.
- Metrics / thresholds (if relevant):
  - Search quality threshold: answers must cite concrete local paths, retrieve the obviously relevant knowledge pages in a small curated sample corpus, and not rank mirror/history above live doctrine when both exist.
  - Preservation threshold: zero source materials silently discarded after a reported-success ingest.

## 0.5 Key invariants (fix immediately if violated)
- There is one canonical knowledge tree on disk for this system.
- Local multimodal agents running local skills on the same filesystem are the primary execution model for this system.
- Semantic knowledge pages are the first-class browsing surface.
- Source provenance is preserved: every archived source has an immutable original payload or a durable pointer plus manifest/note.
- Derived knowledge pages are allowed to move; source materials are not silently lost when the compiler reorganizes the tree.
- Raw/source truth, provenance notes, derived knowledge pages, optional search/index support state, and receipt/mirror outputs are different layers and must not be collapsed into one class of record.
- Authority tier is first-class metadata:
  - live doctrine
  - raw runtime truth
  - generated mirror/receipt
  - historical support
  - derived page
- Every material knowledge page must carry provenance notes or explicit unresolved-gaps notes.
- A single source may support many knowledge pages, and a single knowledge page may depend on many sources.
- The shared `knowledge` skill contract is the user-facing API; runtime-specific glue and packaging must remain thin and must not fork the underlying storage model.
- Local Codex, Paperclip, Hermes, and OpenClaw-class integrations are adapters into one shared contract, not permission to create per-runtime storage semantics or alternate knowledge APIs.
- AGENTS loading, custom prompts, session stores, shell snapshots, hooks, heartbeats, and other runtime internals are evidence sources or context surfaces, not the `knowledge` API.
- Do not treat transport or service architecture as a prerequisite for local operation. The default path is the local agent reading local files directly through the skill.
- Native multimodal model capability is the default way to inspect images and similar artifacts in v1, and to inspect PDFs where the active runtime surface exposes documented file input.
- Capability claims in this plan must be grounded in official model docs or local runtime code, not in guesswork.
- Use the dated host capability snapshot in Section 3.2 for current-host capability claims. Do not widen or restate modality assumptions elsewhere without new evidence.
- No helper scripts, helper harnesses, helper indexes, converters, or other deterministic support subsystems may be added without explicit approval from Amir and a Decision Log entry.
- If a helper is approved later, it assists the agent; it does not replace the agent as the primary intelligence or become hidden authority.
- The archive/search system must remain readable and inspectable without a hidden control plane being the only way to understand it.
- The viewer, if added, is read-only with respect to canonical knowledge state.
- Search answers must point back to concrete knowledge pages plus evidence files/sections instead of becoming an uncited black box.
- Search answers must not silently outrank live doctrine with historical docs, mirror receipts, or cached runtime projections.
- Local same-host operation is the first slice, but remote ingestion must be addable later without a data-model rewrite.
- No runtime-specific semantic forks in taxonomy, storage layout, or manifest shape are allowed.
- Secret-bearing runtime files may be archived as raw pointers with redacted derived summaries, but their sensitive contents must not be copied into the graph by default.
- The system either preserves a source with usable provenance or fails loudly with an actionable error.
- Fallback policy (strict):
  - Default: **NO fallbacks or runtime shims** (the core storage and skill contract must work correctly or fail loudly).
  - If an exception is truly required later, it must be explicitly approved by Amir by setting `fallback_policy: approved` and recording a Decision Log entry with a timebox plus removal plan.

## 0.6 Pre-drafted reference artifacts (part of the North Star)
- The reference `knowledge save` ingestion query drafted in section `5.6` is not throwaway scaffolding.
  - Current intent: implementation should start from that contract nearly verbatim unless later evidence forces a targeted change.
- The draft shared `knowledge` skill package drafted in section `5.7` is not a placeholder to rediscover later.
  - Current intent: implementation should start from that skill boundary, package shape, and command model unless later research exposes a concrete flaw.
- These drafts exist specifically so the project does not regress into vague “we will figure out the prompt/skill later” thinking.
- These drafts are still the intended public layer even if thin runtime packaging differs slightly across runtimes.
- If either draft changes materially during research or implementation, the delta should be explained in the plan instead of silently replacing it.

## 0.7 Anti-Deterministic Operating Law
- This plan must be read as if the following sentence were stamped on every section: the default engine is a smart local multimodal LLM agent with direct filesystem access, not a deterministic backend.
- If a reader comes away thinking v1 requires an OCR stack, a transport architecture, a retrieval service, a conversion daemon, or a helper-script bundle before the agents can do useful work, that section is wrong and must be fixed.
- The right default move is to teach the agent what to do in the `knowledge` skill, preserve provenance, and let the agent inspect the source files directly.
- Any proposal to add scripts, harnesses, indexes, converters, or similar machinery must be framed as an exception, must justify why the local agent path is insufficient, and must be explicitly approved by Amir before it becomes part of the architecture.
- Deterministic structure belongs at the persistence boundary:
  - on-disk layout
  - ids and locators
  - authority and provenance rules
  - receipt shapes
- Deterministic structure does not belong as the default replacement for model cognition during ingest, search, or semantic reorganization.
- Anti-deterministic does not mean capability hand-waving. The right move is to rely on the documented capability envelope of the actual local model/runtime in use, not to assume missing capability and not to overclaim unsupported modalities.

---

# 1) Key Design Considerations (what matters most)

This section is intentionally seeded from the idea request and the sibling runtime docs. The later deep-dive and phase-planning passes should sharpen it, not replace it with generic boilerplate.

## 1.1 Priorities (ranked)
1. Treat strong local multimodal agents as the primary executor, so the system leans on existing model capability instead of inventing deterministic infrastructure first.
2. Semantic organization of company knowledge, so the primary browse model is what the company knows, not which runtime or file family a source came from.
3. Provenance-preserving extraction plus authority-tier awareness, so live doctrine, raw runtime truth, mirror receipts, and historical docs do not get flattened together.
4. One shared `knowledge` contract that different local runtimes can package or invoke cleanly without inventing per-runtime storage semantics.
5. An incremental compiler/reorganizer that improves the semantic graph without corrupting or obscuring the supporting source archive.
6. Human-readable, on-disk truth that stays inspectable even if the active runtime mix changes over time.

## 1.2 Constraints
- Correctness: the system must preserve source materials, authority tier, and source layer; it must not fabricate provenance or flatten precedence.
- Performance: same-host ingest/search should feel interactive enough for normal agent use without requiring a dedicated retrieval subsystem.
- Latency: full reorganization passes can be batchier, but ordinary `save/search/trace` work should stay direct and low-friction.
- Migration: the first version is greenfield in this repo, but it must integrate cleanly with sibling runtime surfaces rather than assuming one agent stack wins forever.
- Operational shape: the company already has heterogeneous agent surfaces; the knowledge system should reduce fragmentation, not add another runtime-specific doctrine layer.
- Scope: first version should be same-host first and not get blocked on remote sync, distributed queues, or polished publishing.
- Security/redaction: runtime configs, auth envelopes, and logs can contain secrets or prompt-bearing material, so the graph needs restricted raw sources plus safe derived summaries.
- Taxonomy: the first taxonomy will be imperfect; the system must make semantic reorganization cheap rather than pretending the first folder layout is final truth.
- Approval discipline: helper scripts, helper harnesses, and deterministic support subsystems are not free. They require explicit approval before they enter the plan or implementation.

## 1.3 Architectural principles (rules we will enforce)
- Optimize the top-level knowledge tree for semantic usefulness, not for source-system neatness.
- Default to skill-first, local-filesystem-first, multimodal-agent-first execution.
- Separate raw/source truth from provenance notes and from derived knowledge truth, and be explicit about which layer owns which concern.
- Use stable source/provenance identifiers so knowledge pages can move without severing provenance.
- Keep ingest/search/trace/rebuild/status as public skill contracts; treat runtime-specific integrations as thin packaging, not owners.
- Do not insert transport/service abstractions into the local path unless they are truly needed and explicitly approved.
- Prefer simple on-disk truth over opaque hidden state.
- Make the search surface return semantic knowledge pages first, with explicit supporting provenance/source refs and authority tier.
- Make trace/provenance a first-class workflow, not a debugging afterthought.
- Allow the same source to teach many concepts and the same concept to draw on many sources.
- Use model judgment first for reading and filing source material; only introduce deterministic helpers when explicitly approved and clearly net-positive.
- Do not couple the core knowledge contract to AGENTS injection, custom prompts, session stores, heartbeat runners, shell snapshots, hook systems, or transport-layer details; those are runtime internals, not the portable knowledge plane.
- Approval-gated helpers remain assistants to the agent, never the hidden owner of semantics.
- Document non-obvious invariants only at the canonical boundaries: source intake, provenance writer, compiler planner, and search-result contract.

## 1.4 Known tradeoffs (explicit)
- Dedicated long-running archivist vs caller-exec ingestion/compiler jobs:
  - Initial bias: keep the storage and skill contract independent from whether a dedicated agent exists; we can add a dedicated worker later if the workload demands it.
- Native model execution vs helper scripts/harnesses:
  - Choose native model execution by default. Helper scripts, converters, indexes, or other harnesses are exceptions that require explicit approval after a clear deficiency is observed.
- Fixed taxonomy upfront vs evolving semantic clustering:
  - Choose evolving clustering. The first version should start with obvious domains and allow split/merge/rehome operations as the corpus teaches us better structure.
- Page-level provenance vs claim-level provenance:
  - Choose section-level support on knowledge pages, backed by page-level provenance notes per source or tight source bundle. Add claim-level granularity later only where ambiguity, conflict, or compliance pressure makes it necessary.
- Local-host-first vs remote-first:
  - Choose local-host-first for speed of shipping, but avoid baking local-path assumptions into the canonical data model.
- Bigger model for compilation vs smaller/faster model for search:
  - Choose the strong local model as the default executor for both ingest and retrieval over the semantic tree. Consider helper retrieval state later only if explicitly approved and justified by measured pain.
- Viewer-first vs search-first:
  - Choose search-first. A Quartz-style viewer is helpful, but it is not the primary acceptance gate for v1.

Illustrative skill-authoring framing for the future `knowledge` skill:
- Repeated asks it should own:
  - “Save this source into the company knowledge base and extract the durable learnings honestly.”
  - “Search the knowledge base for what we know about this topic and show me the best-supported current reading.”
  - “Trace where this page or claim came from and what source materials back it.”
- One strong anti-case:
  - “Write my final uncited report for me.” That belongs to the caller agent after it uses `search` and `trace`, not to the storage/retrieval skill itself.

---

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- This repo is effectively greenfield; it does not yet contain the knowledge system implementation.
- The company already operates or recently operated multiple agent/runtime surfaces:
  - `../agents` documents a Hermes fleet as the runtime of record on this host and treats OpenClaw as retired historical context.
  - `../paperclip_agents` documents Paperclip as the control plane for issue/run coordination rather than as the storage layer for long-lived knowledge artifacts.
- The actual knowledge domains we need to support are already concrete in the source materials:
  - product north star, brand framing, and learner habit loops
  - onboarding, progression, and learner-trust UX rules
  - shared agent learnings and runbooks
  - runtime behavior, recovery, and memory boundaries
  - skill-authoring and workflow law
  - lesson-authoring architecture
  - lesson style/copy/UX baselines
  - mobile/backend bring-up guidance
  - pod/self-contained deployment patterns
- Company knowledge already exists across repos, docs, artifacts, images, outputs, and especially Codex sessions, but there is no shared knowledge-compilation layer that continuously turns those materials into one semantic, searchable markdown graph.
- Retrieval today is mostly ad hoc: repo search, memory, direct file browsing, issue comments, or runtime-specific context windows.

## 2.2 What's broken / missing (concrete)
- There is no canonical contract for turning new source material into semantic knowledge.
- There is no single place where PDFs, images, notes, reports, runtime traces, doctrine files, and sessions become durable, linked company knowledge instead of isolated files.
- There is no shared, runtime-neutral skill boundary for semantic ingest, search, and trace.
- There is no provenance surface that can explain which pages are supported by which sources and which sources are live truth versus history or mirrors.
- There is no incremental compiler that can revisit old material, extract new learnings, split/merge pages, or reorganize the semantic tree as the corpus grows.
- There is no agent-facing search surface that treats the compiled markdown graph as first-class company memory.
- Because the runtime mix can change over time, any runtime-specific knowledge store would likely become another migration problem instead of a stable asset.

## 2.3 Constraints implied by the problem
- The storage model must outlive any one runtime or orchestration choice.
- The system must preserve source materials well enough that later recompilation is possible without reacquiring the originals.
- The archive must preserve enough authority/provenance metadata that live doctrine does not get confused with historical plans, mirror receipts, or runtime caches.
- Search must be fast enough that agents prefer it over rereading raw directories manually.
- The first version should not assume a perfect taxonomy upfront; the system needs room to reorganize semantic pages as usage patterns and corpus shape become clearer.
- Remote ingestion is not a day-one requirement, but the contract should not make remote transport a redesign later.
- Raw runtime/config files can be sensitive, so the system needs a restricted-raw plus safe-derived split from day one.

---

# 3) Research Grounding (external + internal "ground truth")

<!-- arch_skill:block:research_grounding:start -->
## 3.1 External anchors (papers, systems, prior art)
- Karpathy-style "raw sources -> compiled markdown knowledge base -> later questions and edits feed back into the corpus" is the right prior-art shape to adopt for this plan.
  - Adopt:
    - preserve raw sources
    - compile durable semantic markdown pages
    - let later search/questions add more knowledge back into the same corpus
  - Reject:
    - manual human filing as the primary operating model
    - treating the prior-art folder shape as a binding taxonomy for this company
- Quartz-/Obsidian-style markdown consumption patterns are the right class of optional read surface to adopt, but only as secondary consumers.
  - Adopt:
    - static/read-only browsing over a markdown tree
    - backlinks, graph views, and local search as optional UX
  - Reject:
    - viewer conventions becoming the canonical write path or storage contract

## 3.2 Internal ground truth (code as spec)
- Authoritative planning constraint from the user:
  - The target agents are local.
  - The target skills are local.
  - The agent already has direct filesystem access when it runs the skill.
  - GPT-5.4-class agents in these harnesses are already multimodal enough that images, and PDFs when the active runtime surface exposes documented file input, should be approached as directly inspectable local inputs rather than as missing-capability problems.
  - Scripts and harnesses require explicit approval from Amir before they enter the design.
  - This user-supplied ground truth is stronger than any weaker assumption I previously made about needing transport, OCR, or deterministic preprocessing for v1.
- Official capability anchors checked on 2026-04-02:
  - `https://developers.openai.com/api/docs/models`
    - States that all latest OpenAI models support text and image input plus vision.
  - `https://developers.openai.com/api/docs/models/gpt-5.4`
    - States GPT-5.4 input is `Text, image`, output is `Text`, and modalities are:
      - text: input and output
      - image: input only
      - audio: not supported
      - video: not supported
    - Also confirms GPT-5.4 supports Responses tools including skills, apply patch, computer use, hosted shell, and MCP.
  - `https://developers.openai.com/api/docs/guides/file-inputs`
    - Documents direct PDF file input via `input_file` in the Responses API.
  - `https://developers.openai.com/api/docs/guides/images-vision`
    - Documents direct image input via `input_image` by URL or Base64.
- Local runtime anchors checked on 2026-04-02:
  - `/Users/agents/workspace/codex/README.md`
    - States Codex CLI is a coding agent from OpenAI that runs locally on your computer.
  - `/Users/agents/workspace/codex/codex-cli/README.md`
    - States Codex can inspect repositories, edit files, run commands, and accept screenshots or diagrams as multimodal inputs.
    - Documents approval modes from suggest through full auto.
  - `/Users/agents/workspace/codex/sdk/typescript/README.md`
    - Shows local image attachments passed through the CLI with `--image`.
  - `/Users/agents/workspace/codex/docs/contributing.md`
    - States omitted `input_modalities` currently implies text plus image support.
  - `/Users/agents/.codex/config.toml`
    - Confirms this host currently runs Codex on `gpt-5.4` with `xhigh` reasoning.
  - `/Users/agents/workspace/agents/deploy/hermes/profiles/agent_coder/config.yaml`
    - Confirms the live Hermes profile on this host also defaults to `gpt-5.4` with `xhigh` reasoning via `openai-codex`.
  - `/Users/agents/.hermes/hermes-agent/mcp_serve.py`
    - Confirms Hermes already extracts and preserves non-text attachments such as images/files in its local runtime surfaces.
  - `/Users/agents/.hermes/hermes-agent/tests/gateway/test_discord_document_handling.py`
    - Confirms Hermes attachment/document handling exists in local runtime tests, which is stronger than hand-waving about missing document support.
  - `/Users/agents/.hermes/hermes-agent/agent/skill_utils.py`
    - Confirms Hermes resolves shared skills from configured local directories.
  - `/Users/agents/.hermes/hermes-agent/agent/prompt_builder.py`
    - Confirms Hermes injects those shared skills into the local runtime prompt path.
  - `/Users/agents/.openclaw/completions/openclaw.zsh`
    - Confirms the local OpenClaw home still exists as local skill/memory/browser/plugin/tool state, but not that OpenClaw is a currently validated runtime seam on this host.
- Host capability snapshot (dated; evidence-backed; do not widen casually):
  - Active default model lane on this host:
    - GPT-5.4 at `xhigh` reasoning in direct Codex
    - GPT-5.4 at `xhigh` reasoning in the live Hermes `openai-codex` profile
  - Model capability proven by official docs:
    - text input/output
    - image input
    - no audio/video assumption for GPT-5.4
  - File/API capability proven by official docs:
    - PDF file input is documented at the OpenAI API/runtime surface
  - Local runtime capability verified in this audit:
    - Codex local image-attachment flow is verified
    - Hermes local attachment/document preservation is verified
  - Local runtime capability not yet proven end to end in this audit:
    - identical PDF passthrough and interpretation behavior across every local runtime surface
  - Therefore:
    - PDF handling is in scope for the system
    - end-to-end PDF interpretation must still be stated as runtime-surface-specific until each adapter path is explicitly validated
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/.codex/config.toml`
    - Confirms Codex is already a trusted local runtime in this workspace. The relevant fact for this plan is local operation against the same filesystem, not the existence of optional protocol features.
  - `/Users/agents/.codex/skills/.system/skill-creator/SKILL.md`
    - Defines the local Codex skill package contract. This confirms the clean Codex path is a normal installed skill, not a custom backend.
  - `/Users/agents/.codex/skills/.system/skill-installer/SKILL.md`
    - Confirms the standard install/distribution path for Codex skills on this host.
  - `/Users/agents/.agents/skills/skill-authoring/SKILL.md`
    - Defines the leverage-first, reference-driven quality bar for shared skills that should govern `knowledge`.
  - `/Users/agents/workspace/paperclip_agents/vendor/paperclip/skills/paperclip/SKILL.md`
    - Confirms Paperclip is a coordination/distribution surface, not the knowledge store itself.
  - `/Users/agents/workspace/paperclip_agents/vendor/paperclip/skills/paperclip/references/company-skills.md`
    - Confirms the clean Paperclip seam is distribution of shared skills into agents via company skill assignment.
  - `/Users/agents/workspace/paperclip_agents/vendor/paperclip/packages/adapters/codex-local/src/index.ts`
    - Confirms Paperclip has a first-class `codex_local` runtime path and can therefore package/runtime-manage the same local Codex skill surface instead of inventing a second backend.
  - `/Users/agents/workspace/agents/README.md`
    - Confirms Hermes is the runtime of record on this host and that the relevant integration question is how it loads skills/tools locally, not how to create a separate service.
  - `/Users/agents/workspace/agents/AGENTS.md`
    - Confirms native runtime interfaces are preferred and OpenClaw is historical unless intentionally restored.
  - `/Users/agents/workspace/agents/deploy/hermes/profiles/agent_coder/config.yaml`
    - Confirms Hermes already has a shared-skill hook point through `skills.external_dirs`.
  - `/Users/agents/.hermes/hermes-agent/agent/skill_utils.py`
    - Confirms Hermes resolves shared skills from configured local directories.
  - `/Users/agents/.hermes/hermes-agent/agent/skill_commands.py`
    - Confirms Hermes turns shared skills into callable local runtime surfaces.
  - `/Users/agents/.hermes/hermes-agent/agent/prompt_builder.py`
    - Confirms Hermes skill injection is already a local prompt/runtime path, which supports a skill-first design.
  - `/Users/agents/.agents/skills/openclaw-agent-authoring/SKILL.md`
    - Confirms OpenClaw-facing behavior is also skill/doctrine-shaped rather than requiring a separate knowledge backend.
  - `/Users/agents/workspace/paperclip_agents/vendor/paperclip/packages/adapter-utils/src/types.ts`
    - Confirms the Paperclip adapter layer is packaging/control-plane territory, not storage-semantics territory.
- Existing patterns to reuse:
  - `/Users/agents/workspace/paperclip_agents/vendor/paperclip/report/2026-03-13-08-46-token-optimization-implementation.md`
    - Important caveat: Paperclip `codex_local` injects runtime skills into workspace `.agents/skills` and uses a managed `CODEX_HOME`, so the follow-on question is now narrower: what isolation guarantees do we still want across repo-local skills, injected company skills, and shared auth/config seeding?
  - `/Users/agents/.codex/prompts/_backup/arch_skill_disabled_20260330_131759/arch-flow.md`
    - Useful negative prior art: the clean forward path is skill-first, not a revived prompt-family interface.
  - `/Users/agents/.codex/sessions/2026/02/27/rollout-2026-02-27T11-09-14-019ca013-71c8-7c21-8d94-f4f5c1f3fc56.jsonl`
    - Confirms the corpus already contains durable cross-agent operational knowledge about shared learnings, breakages, resolutions, and reusable runbooks.
  - `/Users/agents/.codex/sessions/2026/02/27/rollout-2026-02-27T17-58-14-019ca189-e285-72b2-9abc-451ed1b12074.jsonl`
    - Confirms the corpus already contains durable workflow doctrine about moving lesson authoring into a Slack-first agent plus skill tree.
  - `/Users/agents/.codex/sessions/2026/02/28/rollout-2026-02-28T09-02-19-019ca4c5-9ac4-7853-acea-d31aeb29c905.jsonl`
    - Confirms the corpus already contains lesson style, copy, UX baseline, and glossary knowledge that should become semantic topic pages rather than live forever inside session chronology.
  - `/Users/agents/.codex/sessions/2026/02/24/rollout-2026-02-24T07-36-17-019c8fdd-66ab-7ba0-bb31-6fd80714ae7a.jsonl`
    - Confirms the corpus already contains stateful OpenClaw recovery and continuity knowledge that spans runtime behavior, workspace doctrine, and provenance.
  - `/Users/agents/.codex/sessions/2026/03/29/rollout-2026-03-29T06-58-50-019d3976-094f-7291-b04f-800b78307393.jsonl`
    - Confirms the corpus already contains Hermes/OpenClaw boundary decisions and cutover concerns that the future graph must preserve with authority notes.
  - `/Users/agents/.codex/sessions/2026/04/02/rollout-2026-04-02T19-02-26-019d50a5-f2ad-7392-9fcc-b610f387eb0f.jsonl`
    - Confirms the current request itself is already defining the target skill surface, knowledge semantics, anti-deterministic law, and integration requirements and should later be preserved as provenance.
  - `/Users/agents/.codex/shell_snapshots/019d50a5-f2ad-7392-9fcc-b610f387eb0f.sh`
    - Confirms Codex-origin shell state can be preserved as supporting evidence, but it does not define the knowledge API.
  - `/opt/homebrew/bin/pdftotext` and `/opt/homebrew/bin/pdfinfo`
    - These are optional local helper candidates only. Their presence does not justify making deterministic PDF tooling the architectural default, and they cannot be used in this plan without explicit approval.
- Design consequence from that ground truth:
  - The missing product is not transport, OCR, or deterministic normalization. The missing product is a shared semantic knowledge contract, provenance discipline, and on-disk graph.
  - For the current host and current model lane, the baseline capability assumption is:
    - local text inspection
    - local image inspection
    - PDF handling when the active runtime surface exposes documented file input
    - shell/tool/file operations through the active local coding-agent harness
  - For the current host and current model lane, the architecture must **not** assume:
    - missing image understanding
    - missing PDF understanding that forces an OCR pipeline
    - identical PDF behavior across all local runtime surfaces before adapter validation proves it
    - native audio or video support under GPT-5.4
  - Local agents should inspect local files directly through the `knowledge` skill by default.
  - Codex, Paperclip, Hermes, and OpenClaw-class integration should be solved as packaging/invocation policy over the same local skill contract, not as a set of per-runtime backends.
  - Scripts, harnesses, indexes, and deterministic converters are optional later helpers only if explicitly approved after a real deficiency is observed.
  - Prompt/session/runtime internals such as AGENTS injection, custom prompts, session DBs, heartbeat machinery, shell snapshots, and hook systems are useful evidence or control-plane surfaces, but they are the wrong place to anchor the `knowledge` API.

## 3.3 Open questions from research
- What minimum isolation guarantees do we want for Paperclip `codex_local`, given its managed `CODEX_HOME` plus workspace `.agents/skills` injection model?
  - This matters before we claim clean multi-agent reuse of one shared `knowledge` skill on the same host.
- If OpenClaw is revived later, should its thin alias layer preserve the familiar `memory_search` / `memory_get` idiom, or should it expose explicit `knowledge` verbs immediately?
  - OpenClaw is not the v1 proof path on this host, so this remains a follow-on naming/packaging question rather than a current implementation requirement.
- What is the smallest optional helper surface, if any, that becomes worth explicit approval after the pure local-skill path exists?
  - Examples that may later be considered, but are not approved now: a PDF converter, a retrieval index, or a remote-submission helper.
  - The question is not “what deterministic machinery can we invent?” but “what proved painful enough in real usage that adding machinery is justified?”
- V1 semantic page kinds are now locked:
  - `topic`
  - `playbook`
  - `decision`
  - `glossary`
  - Domains are folder/index structure, not a separate page kind, and unresolved questions stay in sections or `indexes/unresolved-questions.md` rather than becoming standalone question pages.
- V1 provenance and lifecycle are now locked:
  - Knowledge pages carry section-level support maps.
  - Provenance notes stay page-level per source or tight source bundle.
  - `knowledge save` performs bounded synchronous work: preserve source, write provenance, update the smallest affected page sections, and record honest reading limitations or uncertainty.
  - `knowledge rebuild` owns split/merge/rehome, backlinks, indexes, and contradiction surfacing.
<!-- arch_skill:block:research_grounding:end -->

---

<!-- arch_skill:block:external_research:start -->
# External Research (best-in-class references; plan-adjacent)

> Goal: anchor the plan in real local runtime behavior without forgetting the stronger product truth that the agents themselves are already local, multimodal, and file-native.

## Topics researched (and why)
- Official OpenAI capability docs for the actual model/runtime lane on this host — to stop guessing about multimodal and coding-agent capability.
- Codex local runtime docs and config — to separate model capability from local harness behavior.
- Hermes and OpenClaw local surfaces — to separate packaging/invocation seams from the model's actual cognition/input capabilities.

## Findings + how we apply them

### Capability grounding for the current host
- As of 2026-04-02, official OpenAI docs state:
  - latest OpenAI models support text and image input plus vision
  - GPT-5.4 specifically supports text input/output and image input, but not audio or video
  - the file-input guide documents PDF file input at the API/runtime surface
  - the images/vision guide documents direct image input
- As of 2026-04-02, local runtime docs and config on this host state:
  - Codex runs locally on the computer, can inspect repositories, edit files, and run commands
  - Codex accepts image inputs such as screenshots and design specs
  - this host is currently configured to use `gpt-5.4` with `xhigh` reasoning in Codex
  - the live Hermes profile on this host is also configured for `gpt-5.4` with `xhigh` reasoning
  - Hermes preserves and handles document attachments in local runtime code/tests
- Therefore, the default capability envelope we should design around for v1 is:
  - local text inspection
  - local image inspection
  - PDF handling when the active runtime surface exposes documented file input
  - local file edits / shell / skill execution through the active local coding-agent harness
- Therefore, the plan should not assume:
  - a missing multimodal stack for images
  - a missing PDF path that automatically forces OCR or a conversion daemon
  - identical PDF behavior across all local runtime surfaces before adapter validation
  - audio/video capability in the GPT-5.4 default lane when the official docs do not support that claim

### Local capability is the default, not the missing piece
- The important runtime fact is not transport. It is that these agents already run locally, already operate against the same filesystem, and already support skills/tools as reusable behavior packaging.
- Therefore the architecture should center on:
  - one shared on-disk knowledge tree
  - one shared `knowledge` skill contract
  - thin runtime-specific packaging or invocation policy
- It should not center on:
  - transport protocols
  - deterministic preprocessing stacks
  - approval-free helper scripts
  - service-shaped backends that compensate for capabilities the agents already have

### Codex and Paperclip
- Best practice for this plan:
  - Codex uses a normal installed `knowledge` skill and operates directly on local files.
  - Paperclip distributes or assigns that same skill through its existing company-skill path.
  - The model capability comes from the underlying GPT-5.4 lane; Paperclip does not need to invent a second cognition or ingest backend.
- Footgun to avoid:
  - building a Paperclip-only backend or assuming Paperclip changes the underlying storage semantics.

### Hermes
- Best practice for this plan:
  - Hermes should get a clean local `knowledge` surface through the runtime’s existing shared-skill path, with slash-command or tool wrapping optional and non-architectural.
  - The exact wrapper form is an implementation detail; the architectural requirement is that it stays thin and local and does not pretend Hermes needs a second deterministic ingest stack.
- Footgun to avoid:
  - turning plugin/hook/gateway mechanics into the knowledge architecture instead of just using them as packaging.

### OpenClaw
- Best practice for this plan:
  - If OpenClaw support returns, expose the same shared `knowledge` contract through the cleanest memory/skill-style local alias.
  - Treat OpenClaw's remaining local skills, memory, browser, and plugin state as legacy host evidence plus future prior art, not as a currently validated runtime seam on this host.
- Footgun to avoid:
  - treating OpenClaw’s historical memory or plugin machinery as permission to fork the backend.

## Adopt / Reject summary
- Adopt:
  - one shared local `knowledge` skill contract
  - one shared on-disk semantic knowledge tree
  - Codex, Paperclip, Hermes, and OpenClaw-class callers as thin local packaging layers around that same contract
  - approval-gated helpers only after real observed pain
- Reject:
  - making MCP, CLI services, deterministic search stacks, OCR stacks, or helper-script bundles the architectural center for local operation
  - runtime-specific backends that fork storage semantics
  - using AGENTS injection, custom prompts, session stores, shell snapshots, hooks, or heartbeats as the primary knowledge API

## Open questions (ONLY if truly not answerable)
- OpenClaw naming at the user layer — evidence needed: a thin alias sketch showing whether preserving `memory_search` / `memory_get` semantics or exposing explicit `knowledge` verbs yields less friction without hiding the shared contract.
- Future alternate-model modality lanes — if we later want audio or video ingestion, that should be added as an explicit model/runtime-specific capability claim with evidence, not smuggled in as if GPT-5.4 already guaranteed it.
<!-- arch_skill:block:external_research:end -->

---

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
```text
/Users/agents/workspace/fleki
|-- .git
`-- docs/
    `-- CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md

Relevant current source-of-knowledge and runtime-control surfaces live outside this repo:
/Users/agents/.codex/config.toml
/Users/agents/.codex/skills/**
/Users/agents/.codex/sessions/**
/Users/agents/.codex/shell_snapshots/**
/Users/agents/workspace/paperclip_agents/vendor/paperclip/skills/**
/Users/agents/workspace/paperclip_agents/vendor/paperclip/packages/adapters/codex-local/**
/Users/agents/.hermes/profiles/**
/Users/agents/.hermes/hermes-agent/**
/Users/agents/workspace/agents/deploy/hermes/profiles/**
/Users/agents/workspace/agents/agents/_shared/vendors/hermes-agent/**
/Users/agents/.openclaw/**
/Users/agents/workspace/work/openclaw-live-rollout-v2026.3.22/**
```

## 4.2 Control paths (runtime)
- There is no runtime or ingest/search control path in this repo yet.
- Existing adjacent runtimes already expose materially different control paths:
  - Codex:
    - project instructions come from AGENTS loading
    - skills are prompt-teaching surfaces
    - it already runs locally against the same filesystem as this repo
    - sessions and shell state persist under `~/.codex`, but there is no compiled semantic knowledge layer
  - Paperclip:
    - control plane distributes company skills and launches `codex_local`
    - it runtime-manages the Codex lane rather than owning a distinct company knowledge runtime today
  - Hermes:
    - runtime-native seams are local/shared skills, slash-command exposure, optional tool wrapping, and a small set of live hooks
    - external skills are shared procedural guidance, not a semantic knowledge backend
    - session/state lives in Hermes homes and runtime state, but there is no host-wide semantic knowledge core
  - OpenClaw:
    - historical prior art on this host exposes memory-lane, skills, hooks, transcript store, and heartbeat/session orchestration
    - it is not the runtime of record here and is not a currently validated runtime seam for v1, so it informs future adapter shape more than present-day operational truth
- Ownership today is fragmented:
  - Codex owns Codex prompt/session/tool state
  - Paperclip owns task/run/skill-distribution control-plane state
  - Hermes owns Hermes prompt/session/plugin state
  - OpenClaw owns its own memory/session/control surfaces where used
- Today, knowledge is created indirectly:
  - source materials get produced in Codex sessions, repo docs, runtime traces, Paperclip doctrine, images, PDFs, or output packets
  - durable learnings remain embedded in those sources
  - reuse depends on manual search, human memory, or runtime-local context windows
- There is no shared compile step that turns those sources into semantic company memory.
- What is missing is not local file access or model capability. What is missing is one shared semantic knowledge contract and one canonical on-disk graph that all of those local caller surfaces can use.

## 4.3 Object model + key abstractions
- What exists today are runtime-local objects, not shared knowledge objects:
  - Codex:
    - skills
    - MCP servers/tools/resources
    - rollout sessions
    - shell snapshots
  - Paperclip:
    - issues
    - runs
    - company-skill assignments
    - adapter configs
  - Hermes:
    - shared/local skills
    - optional slash or tool exposure
    - external skills
    - session DB/state
    - runtime homes
  - OpenClaw:
    - legacy memory/skill alias surfaces
    - transcript/session stores
    - hook/context-engine lifecycles
- No canonical source-record contract exists yet.
- No provenance-note contract exists yet.
- No semantic knowledge-page model exists yet.
- No stable `knowledge_id` / `source_id` / claim-locator contract exists yet.
- No search-result, trace-result, or rebuild-receipt contract exists yet.
- No explicit boundary exists yet between raw/source truth, provenance notes, derived knowledge truth, and runtime-specific control-plane state.

## 4.4 Observability + failure behavior today
- There is no central ingest receipt, compile log, search result contract, or trace contract because the system does not exist yet.
- The host does have evidence surfaces, but they are runtime-specific and non-unified:
  - Codex sessions and shell snapshots
  - Paperclip issues/runs/comments and skill-distribution state
  - Hermes session/state DB plus runtime logs and sidecar artifacts
  - OpenClaw session/memory artifacts and plugin state where historically used
- Failure today is mostly silent fragmentation:
  - learnings stay buried in sessions, docs, and runtime surfaces
  - authority collisions are resolved informally in people’s heads
  - live doctrine, historical support, and runtime readback have no shared precedence contract
  - retrieval depends on manual search or personal memory rather than explicit provenance-backed company memory

## 4.5 UI surfaces (ASCII mockups, if UI work)
```ascii
[today]
source material appears in one runtime-local surface
    |
    +-- codex sessions / shell snapshots
    +-- paperclip skills / issues / runs
    +-- hermes homes / plugins / external skills
    +-- openclaw memory / sessions / hooks
    +-- repo docs / plans / doctrine
    +-- pdf / image / note / output packet

[retrieval]
manual search + runtime-local affordances + context-window luck
```
<!-- arch_skill:block:current_architecture:end -->

---

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
```text
/Users/agents/workspace/fleki
|-- docs/
|-- knowledge/
|   |-- topics/          # primary semantic markdown knowledge graph
|   |   |-- doctrine/
|   |   |   |-- authority-and-precedence.md
|   |   |   |-- shared-agent-learnings.md
|   |   |   |-- runbooks-vs-crons.md
|   |   |   `-- skills/
|   |   |       |-- skill-authoring.md
|   |   |       `-- slack-first-lessons-skill-tree.md
|   |   |-- runtime/
|   |   |   |-- openclaw/
|   |   |   |   |-- session-recovery-and-resume.md
|   |   |   |   `-- mention-routing-and-thread-scope.md
|   |   |   |-- hermes/
|   |   |   |   |-- shared-fleet-memory.md
|   |   |   |   `-- hermes-vs-openclaw-boundaries.md
|   |   |   `-- pods/
|   |   |       `-- per-pod-isolation-and-file-native-control-planes.md
|   |   |-- product/
|   |   |   |-- brand/
|   |   |   |   `-- duolingo-for-poker.md
|   |   |   |-- learning-experience/
|   |   |   |   |-- habit-economy.md
|   |   |   |   |-- placement-and-onboarding.md
|   |   |   |   |-- progression-unlock-transparency.md
|   |   |   |   `-- puzzle-and-table-fidelity.md
|   |   |   `-- lessons/
|   |   |       |-- slack-first-authoring.md
|   |   |       |-- style-and-copy.md
|   |   |       |-- playable-ux-baselines.md
|   |   |       |-- lesson-length-and-learning-research.md
|   |   |       `-- lesson-step-count-provenance.md
|   |   |-- engineering/
|   |   |   `-- mobile/
|   |   |       |-- flutter-dev-and-mobile-sim.md
|   |   |       `-- backend-bring-up.md
|   |   |-- operations/
|   |   |   `-- releases/
|   |   |       `-- post-release-followup-runbooks.md
|   |   |-- glossary/
|   |   |   `-- terms.md
|   |   `-- indexes/
|   |       |-- by-topic.md
|   |       |-- recent-changes.md
|   |       `-- unresolved-questions.md
|   |-- provenance/     # source-backed notes that explain what was learned
|   |   |-- codex/
|   |   |   `-- sessions/2026/02/27/019ca013-71c8-7c21-8d94-f4f5c1f3fc56.md
|   |   |-- hermes/
|   |   `-- paperclip/
|   |-- sources/        # raw originals or durable pointers; not the primary browse surface
|   |   |-- codex/
|   |   |   `-- sessions/2026/02/27/rollout-2026-02-27T11-09-14-019ca013-71c8-7c21-8d94-f4f5c1f3fc56.jsonl
|   |   |-- hermes/
|   |   |-- paperclip/
|   |   |-- pdf/
|   |   `-- images/
|   |-- assets/         # derived-only renditions/extractions referenced by knowledge pages
|   |-- receipts/
|   |   |-- save/
|   |   |-- search/
|   |   |-- trace/
|   |   `-- rebuild/
|   |-- search/         # optional support state only if later explicitly approved
|   |   `-- README.md
|   `-- publish/
|       `-- quartz/
`-- skills_or_tools/     # shared `knowledge` skill package and references
```

Illustrative page types inside that tree:
- `topics/**/*.md`
  - the primary semantic pages: `topic`, `playbook`, `decision`, and `glossary`
  - domains are expressed through folders and index pages rather than as a separate page kind
  - unresolved questions stay in page sections or shared indexes instead of becoming standalone question pages in v1
- `provenance/**/*.md`
  - one provenance note per important source or tight source bundle, explaining what the source taught us, what page sections it influenced, and how reliable or sensitive the material is
- `sources/**`
  - raw originals or durable pointers/hashes; required for traceability, not primary browsing
- `assets/**`
  - derived-only page images, extracted figures, normalized renditions, or helper files produced during ingestion; descriptors belong in provenance/source metadata, not as primary topic content
- `receipts/**/*.md`
  - append-only save/search/trace/rebuild receipts for what the system did

## 5.2 Control paths (future)
- Canonical public verbs for the future shared skill:
  - `knowledge save`
    - preserve new source material under `sources/**`
    - inspect local source material directly from the filesystem
    - use native multimodal reasoning first for markdown, images, similar local artifacts, and PDFs where the active runtime surface exposes documented file input
    - classify source layer, authority tier, and sensitivity
    - create or update the smallest safe provenance note plus the smallest affected semantic page sections
    - record honest reading limitations, uncertainty, and any pending wider reorganization
  - `knowledge search`
    - retrieve relevant semantic pages first
    - search and read `topics/**` by default, then inspect provenance or raw sources as needed
    - return short cited results with authority tier plus supporting provenance/source refs
  - `knowledge trace`
    - show provenance and precedence for a `knowledge_id`, path alias, `knowledge_id#section_id`, or claim text used as best-effort lookup input
  - `knowledge rebuild`
    - re-run semantic compilation/reorganization for a scope
    - own split/merge/rehome, backlink refresh, index refresh, and contradiction surfacing
  - `knowledge status`
    - show backlog, recent ingests, stale pages, contradictions, rebuild-pending areas, ingests with reading limits, and health
- Default operating model:
  - One shared on-disk knowledge tree owns:
    - canonical storage semantics
    - provenance writing
    - semantic compilation/reorganization
    - search and trace expectations
  - The primary executor is a local multimodal agent running the shared `knowledge` skill against the same filesystem.
  - The skill package teaches:
    - how to inspect local files directly
    - how to preserve provenance and authority honestly
    - how to update the smallest correct topic set
    - how to report uncertainty, conflicts, and reading limitations
  - Use the dated host capability snapshot in Section 3.2 for current-host modality claims.
    - In this pass, that means GPT-5.4-backed text/image reasoning in the active local lanes.
    - PDF handling is in scope when the active runtime surface exposes documented file input.
    - Audio/video are not assumed for v1.
  - Helper scripts, helper harnesses, retrieval indexes, converters, or transport layers are not part of the default path.
    - If one is later proposed, it is an optional assistant to the agent and requires explicit approval from Amir plus a Decision Log entry before it becomes part of the architecture.
    - If that helper is a fallback/exception, it is invalid unless the plan/package also sets `fallback_policy: approved` and the Decision Log entry includes a timebox plus removal plan.
- Runtime packaging paths:
  - Codex:
    - install the shared `knowledge` skill normally under the local Codex skill path
    - operate directly on local files and the shared knowledge tree
  - Paperclip:
    - distribute the same `knowledge` skill through company-skill / `desiredSkills` paths into `codex_local`
    - reuse the same Codex-facing local skill path rather than inventing a Paperclip-only backend
    - in v1, Paperclip is a distribution and reuse surface for the Codex lane, not a separate portability proof surface
  - Hermes:
    - expose the same `knowledge` contract through shared skills via `skills.external_dirs`, with slash-command or tool wrapping optional and non-architectural
    - wrapper shape is an implementation detail; it must stay thin, local, and subordinate to the same on-disk contract
    - Hermes session/state data may be ingested only through explicit source inputs and provenance, never as ambient hidden context
  - OpenClaw:
    - if revived, expose the same `knowledge` contract through a thin memory/skill alias layer
    - on this host, OpenClaw is legacy state plus future prior art, not a currently validated v1 runtime seam and not a justification for a forked backend
- V1 first proof pair:
  - direct Codex local `knowledge` skill execution against the shared knowledge tree
  - Hermes local execution path against that same tree
  - exact wrapper details are implementation choices, not architectural commitments
  - Paperclip and OpenClaw remain important follow-on adapter/distribution surfaces, but they are not the v1 portability proof gate on this host
- Anti-case for the shared skill surface:
  - no `knowledge answer` verb in v1; final narrative answers remain the caller agent’s job after it uses `search` and `trace`

Flow A: `save`
- Caller invokes `knowledge save` with one or more local paths.
- The agent reads the source directly from disk, preserves it under `sources/**`, writes or updates one or more provenance notes under `provenance/**` using per-source notes or an explicit bundle note with bundle rationale, records source layer/authority/sensitivity plus honest reading limitations, extracts candidate knowledge units, and updates only the smallest semantic page sections needed immediately.
- If direct inspection is insufficient and a helper script or harness seems useful, stop at the architectural boundary: that helper is not part of the plan unless Amir explicitly approves it.

Flow B: `rebuild`
- A compiler pass rereads source records, provenance notes, and existing graph state, then updates semantic pages, splits/merges topics, refreshes backlinks/indexes/summaries, and records moves or supersessions.

Flow C: `search`
- Caller invokes `knowledge search`.
- The agent reads semantic pages first, follows supporting provenance as needed, returns path-cited and id-cited authority-aware results, and does not return raw `sources/**` as ordinary hits.
- Optional helper retrieval state may exist later only if explicitly approved, but search must remain truthful and useful without depending on it.

Flow D: `trace`
- Caller invokes `knowledge trace` for a stable id, section ref, current path alias, or claim text used as best-effort lookup input.
- The system returns the knowledge page(s), provenance note(s), raw source record(s), authority notes, and precedence chain behind that target, while preserving id continuity across page moves.

Flow E: optional publish
- A viewer/export step renders the same markdown tree into a read surface such as Quartz, but that surface does not become the canonical writer.

## 5.3 Object model + abstractions (future)
- `KnowledgePage`:
  - canonical semantic markdown page of kind `topic`, `playbook`, `decision`, or `glossary`
  - identified by opaque stable `knowledge_id`; current path/slug is a mutable alias, not the durable identity
- `ProvenanceNote`:
  - provenance-first markdown note for one source or tight source bundle, explaining what was extracted, what page sections it influenced, and how reliable, sensitive, or incomplete the material is
- `SourceRecord`:
  - preserved raw original or durable pointer/hash plus metadata, used by `trace` and later recompilation
- `SourceReadingReport`:
  - record of what the local agent actually inspected, which parts were readable, what limitations remained, and whether any explicitly approved helper was used
- `AssetRecord`:
  - derived rendition or extraction such as a page image, extracted figure, or helper artifact referenced from provenance or knowledge pages
- `KnowledgeIndex`:
  - human-readable semantic map such as by-topic, recent changes, or unresolved questions
- `SearchResult`:
  - ranked knowledge hit with:
    - `knowledge_id`
    - current page path
    - `page_kind`
    - matched `section_id` or heading
    - snippet
    - authority tier and authority posture
    - supporting provenance/source refs
    - conflict or precedence note
    - `trace` ref
    - reason it matched
    - suggested next read
- `KnowledgeWorkflow`:
  - the shared local workflow contract that owns storage semantics, provenance, compilation, search, and trace behavior
- `RuntimeSurface`:
  - thin runtime-local packaging that exposes the shared `knowledge` contract without owning semantics
- `Locator`:
  - stable `knowledge_id`, stable `section_id`, immutable `source_id`, and current-path alias resolution used by `trace`, rebuild moves, and path-cited search answers
  - claim text is accepted only as best-effort lookup input, not as a durable identity layer
- `AuthorityPolicy`:
  - one explicit precedence and redaction policy applied consistently across ingest, search, trace, and rebuild
- `KnowledgeReceipt`:
  - append-only command receipt for `save`, `trace`, `rebuild`, and `status` visibility, including `rebuild_pending`, reading limitations, and whether any approved helper was used

Illustrative semantic knowledge page contract:

```md
---
knowledge_id: kg_01J0R9E40N3T7Z2KBP2D7K5R6M
current_path: product/lessons/slack-first-authoring
page_kind: playbook
parent_topics:
  - product/lessons
section_ids:
  current_understanding: sec_01J0R9H2Y5PZ5F0YPY4Q4F8SQX
  skill_tree_boundary: sec_01J0R9J3B6N9R1H5T2C1X7M8VA
section_support:
  sec_01J0R9H2Y5PZ5F0YPY4Q4F8SQX:
    - provenance_id: prov_01J0R9K4J0H2C3B8M9N7P1Q6RW
      locator: "session notes on moving lesson editing into the Lesson Agent"
  sec_01J0R9J3B6N9R1H5T2C1X7M8VA:
    - provenance_id: prov_01J0R9M6S2K7V4T8N5D3R1Y9XZ
      locator: "follow-on porting work for style guides, copy exemplars, and UX baselines"
authority_posture: supported_by_internal_session
last_reorganized_at: 2026-04-02T20:10:00Z
supersedes: []
---
# Slack-First Lesson Authoring

## Current Understanding
- Lesson editing is moving away from repo-local Lesson Writer flows toward a Slack-first lesson agent plus skill tree.
- The future skill tree should absorb operational knowledge previously scattered across lesson-writer docs, rubrics, style guides, and UX references.

## Provenance Notes
- 2026-02-27 session: user asked to transition lesson editing directly into the Lesson Agent through a master skill plus specialized skills.
- 2026-02-28 follow-on work: multiple read-only mappings ported lesson-writer sections, style guides, copy exemplars, and UX baselines into target skills.
```

Illustrative provenance note contract:

```md
---
provenance_id: prov_01J0R9P7T4R8Y6N3K2B1M5C9DX
source_id: codex.session.2026-02-27.019ca013-71c8-7c21-8d94-f4f5c1f3fc56
source_kind: codex_session
source_path: ../../../sources/codex/sessions/2026/02/27/rollout-2026-02-27T11-09-14-019ca013-71c8-7c21-8d94-f4f5c1f3fc56.jsonl
authority_tier: historical_support
sensitivity: internal_prompt_bearing
source_reading_mode: direct_local_text
approved_helpers_used: []
knowledge_sections_touched:
  - knowledge_id: kg_01J0RA0A43M0VT9P4NQXQ57Y6S
    current_path: doctrine/shared-agent-learnings
    section_id: sec_01J0RA1FQ4K3SQX4N2C1G7ZP1A
  - knowledge_id: kg_01J0RA2JH0B9C7R2W6X4V1T5EN
    current_path: operations/releases/post-release-followup-runbooks
    section_id: sec_01J0RA3P6W8M5J4D9Q2B7N1VZX
  - knowledge_id: kg_01J0RA4WW1S7Q3T8M5P2R9C6KD
    current_path: doctrine/runbooks-vs-crons
    section_id: sec_01J0RA5C7N4P2B8K1T9V6Q3MXF
---
# Provenance Note

## What this source contributes
- User wanted a common place where all agents write learnings they should all know.
- Explicit examples included release learnings, breakages, resolutions, and reusable runbooks that should stop being relearned agent by agent.

## Extraction Notes
- This source supports shared-agent-learning doctrine.
- This source supports post-release followup runbooks.
- This source suggests a distinction between standing crons and reusable runbook guidance.
```

## 5.4 Invariants and boundaries
- Semantic knowledge pages are primary; raw/source storage is supporting evidence, not the top-level browsing model.
- The primary executor is a local multimodal agent running the shared `knowledge` skill against the same filesystem.
- Allowed v1 page kinds are exactly:
  - `topic`
  - `playbook`
  - `decision`
  - `glossary`
- Raw/source truth, provenance notes, and derived knowledge truth are separate and explicit.
- `knowledge_id`, `section_id`, and `source_id` are the durable identity layer; paths and slugs are mutable views.
- Page moves preserve ids. Split/merge operations mint new page ids and write supersession records instead of silently pretending the old page never existed.
- Reorganization is allowed only in the derived knowledge layer.
- Optional search/index support state is rebuildable support state, not canonical truth, and it is not assumed in the default architecture.
- `knowledge save` performs bounded synchronous work only: preserve source, write provenance, update the smallest affected page sections, and record honest reading limitations or uncertainty.
- `knowledge rebuild` owns global semantic reorganization, split/merge/rehome, backlink/index refresh, and contradiction surfacing.
- The shared skill contract owns public access; runtime wrappers do not own storage semantics.
- Runtime adapters may read runtime-local state only through explicit source-family ingestion and provenance inputs, not as ambient hidden context.
- The viewer/export layer is downstream of the graph and cannot silently become the write authority.
- Search must work from semantic pages plus provenance on disk without requiring a separate service or index.
- Every search answer must be able to point back to a concrete knowledge page and its supporting provenance/source refs.
- Every trace answer must be able to explain the precedence chain behind a claim:
  - live doctrine
  - raw runtime truth
  - mirror/receipt
  - historical support
  - derived page
- PDF-derived textual claims should carry page/block locators when the source material makes that feasible and the agent can identify them honestly.
- Image-only claims must remain honest about what was directly observed and how strong the evidence is.
- Native multimodal reading is the v1 default. Do not invent a deterministic OCR/conversion requirement into the architecture.
- Use the dated host capability snapshot in Section 3.2 for current-host capability claims. In this pass, that means GPT-5.4-backed text/image reasoning, plus PDF handling only where the active runtime surface exposes documented file input. Do not under-assume that capability, and do not overclaim audio/video support or universal PDF passthrough for v1.
- If any helper script or harness is approved later, its use must be visible in provenance and receipts.
- Sensitive raw sources may exist on disk, but derived pages must default to redacted summaries plus pointers/hashes rather than copied secret values.
- Every material knowledge page must contain provenance notes or explicit unresolved gaps.
- One source can feed many pages, and one page can depend on many sources.

## 5.5 UI surfaces (ASCII mockups, if UI work)
```ascii
[agent caller]
  knowledge save / search / trace / rebuild / status
        |
        v
[sources/** + provenance/**]
        |
        v
[compiler / reorganizer]
        |
        v
[topics/**/*.md]
        |
   +----+----+
   |         |
   v         v
[agent search/trace]   [optional Quartz/static view]
```

Illustrative request/response shapes:

```text
Request:
  knowledge save \
    /Users/agents/.codex/sessions/2026/02/27/rollout-2026-02-27T11-09-14-019ca013-71c8-7c21-8d94-f4f5c1f3fc56.jsonl \
    --hints "shared agent learnings, release learnings, reusable runbooks"

Response:
  Result: `applied`
  Saved source:
  - `knowledge/sources/codex/sessions/2026/02/27/rollout-2026-02-27T11-09-14-019ca013-71c8-7c21-8d94-f4f5c1f3fc56.jsonl`
  Wrote provenance note:
  - `knowledge/provenance/codex/sessions/2026/02/27/019ca013-71c8-7c21-8d94-f4f5c1f3fc56.md`
  Reading mode:
  - `direct_local_text`
  Approved helpers used:
  - `none`
  Touched page sections:
  - `kg_01J0RA0A43M0VT9P4NQXQ57Y6S#sec_01J0RA1FQ4K3SQX4N2C1G7ZP1A`
  - `kg_01J0RA2JH0B9C7R2W6X4V1T5EN#sec_01J0RA3P6W8M5J4D9Q2B7N1VZX`
  - `kg_01J0RA4WW1S7Q3T8M5P2R9C6KD#sec_01J0RA5C7N4P2B8K1T9V6Q3MXF`
  Authority posture: `supported_by_internal_session`
  Reading limitations:
  - `none material`
  Next best action: queued `knowledge rebuild --topic doctrine`
```

```text
Request:
  knowledge search "What do we currently believe about Slack-first lesson authoring and what should feed the skill tree?"

Response:
  Method:
  - read semantic pages first, then supporting provenance notes
  Approved helpers used:
  - `none`
  Best knowledge page:
  - `kg_01J0R9E40N3T7Z2KBP2D7K5R6M`
    path=`knowledge/topics/product/lessons/slack-first-authoring.md`
    page_kind=`playbook`
    authority=`supported_by_internal_session`
    match=`sec_01J0R9H2Y5PZ5F0YPY4Q4F8SQX`
    why=`captures the move from repo-local Lesson Writer flows into a Slack-first lesson agent + skill tree`
    trace_ref=`kg_01J0R9E40N3T7Z2KBP2D7K5R6M#sec_01J0R9H2Y5PZ5F0YPY4Q4F8SQX`

  Supporting knowledge pages:
  - `knowledge/topics/product/lessons/style-and-copy.md`
    page_kind=`topic`
    why=`collects style-guide and copy-exemplar learnings referenced during porting work`
  - `knowledge/topics/product/lessons/playable-ux-baselines.md`
    page_kind=`topic`
    why=`collects quality-evaluation and UX-baseline learnings for playable design`

  Supporting provenance:
  - `knowledge/provenance/codex/sessions/2026/02/27/019ca189-e285-72b2-9abc-451ed1b12074.md`
  - `knowledge/provenance/codex/sessions/2026/02/28/019ca4b9-15fc-7483-953f-d7d63ae9fa21.md`
  - `knowledge/provenance/codex/sessions/2026/02/28/019ca4c5-9ac4-7853-acea-d31aeb29c905.md`

  Authority notes:
  - current support is strong internal planning/work-session evidence
  - promote to `live_doctrine` only if later adopted into authoritative repo doctrine
```

```text
Request:
  knowledge trace --ref "kg_01J0RB8YF5C2N7Q4M1T9V6P3WX#sec_01J0RBA3R9M5Q2T7K4D1V8N6CY"

Response:
  Trace target:
  - `kg_01J0RB8YF5C2N7Q4M1T9V6P3WX#sec_01J0RBA3R9M5Q2T7K4D1V8N6CY`
  Claim:
  - `Crash/restart recovery relies on BOOT.md + HEARTBEAT.md + workspace markdown state, not magical hidden recovery`
  Knowledge page:
  - `knowledge/topics/runtime/openclaw/session-recovery-and-resume.md`
  Supporting provenance:
  - `knowledge/provenance/codex/sessions/2026/02/24/019c8fdd-66ab-7ba0-bb31-6fd80714ae7a.md`
  Raw source:
  - `knowledge/sources/codex/sessions/2026/02/24/rollout-2026-02-24T07-36-17-019c8fdd-66ab-7ba0-bb31-6fd80714ae7a.jsonl`
  Related knowledge pages:
  - `knowledge/topics/doctrine/shared-agent-learnings.md`
  Authority warning:
  - current support is internal session guidance; later live runtime doctrine outranks it if they conflict
```

```text
Request:
  knowledge rebuild --topic product/lessons

Response:
  Rebuilt topic:
  - `product/lessons`
  Approved helpers used:
  - `none`
  Changes:
  - refreshed backlinks from 3 provenance notes
  - split `style-and-copy.md` away from `slack-first-authoring.md`
  - re-ranked `playable-ux-baselines.md` as a sibling page instead of a subsection
  Open questions surfaced:
  - one unresolved contradiction on lesson-length guidance
```

```text
Request:
  knowledge status

Response:
  Pending source ingests: 4
  Stale knowledge pages: 3
  Ingests with reading limits: 1
  Approval-gated helpers in use:
  - `none`
  Rebuild pending:
  - `doctrine`
  Hot topics:
  - `runtime/openclaw`
  - `product/lessons`
  - `doctrine/shared-agent-learnings`
  Unresolved contradictions: 1
  Last rebuild:
  - `2026-04-02T20:26:00Z`
```

## 5.6 Reference Prompt - `knowledge save` ingestion query

This is the reference authoring target for the model-facing ingestion step inside `knowledge save`. It is intentionally explicit so the future implementation does not drift back into artifact filing or uncited synthesis.

```md
# Knowledge Save Ingestion Query

Your only job is to examine the provided local source material, identify the durable knowledge it contributes, and return a precise ingestion decision for the semantic markdown knowledge graph.

## Identity & Mission
You are the ingestion compiler for the company knowledge graph.

You are a highly capable local multimodal coding agent operating on the same filesystem as the source material.

Your default job is to inspect the files directly, extract durable knowledge, preserve provenance honestly, and propose the smallest correct semantic updates.

Your work matters because downstream agents will search and rely on the resulting knowledge pages. If you misclassify source material, flatten authority, or organize by source-family instead of meaning, the whole graph becomes less trustworthy.

## Success / Failure
- Success means:
  - you inspect the provided local sources directly
  - you identify the durable learnings in those sources
  - you map them to the right semantic topics
  - you preserve provenance and authority honestly
  - you update or propose updates to the smallest correct set of knowledge pages
  - you surface conflicts, uncertainty, and missing context instead of hiding them
- Failure means:
  - you act as if local file access or multimodal understanding is unavailable when it is available
  - you organize by source system instead of semantic meaning
  - you summarize raw chronology without extracting knowledge
  - you promote historical/session material to live doctrine without basis
  - you emit uncited claims
  - you copy secret or prompt-bearing values into the knowledge graph
  - you invent a helper script, harness, or deterministic preprocessing step without explicit approval
  - you create duplicate topic pages when one existing page should have been updated

## Non-Goals
- Do not write the caller’s final answer to the user.
- Do not preserve every interesting sentence from the source.
- Do not file material under `codex/`, `paperclip/`, `hermes/`, `pdfs/`, or other source-family buckets unless the knowledge itself is about that runtime.
- Do not invent certainty when the source package is ambiguous.
- Do not turn one session’s local preference into company doctrine unless the inputs clearly justify that promotion.
- Do not emit raw secrets, tokens, prompt text, or sensitive config values.
- Do not assume a transport layer, normalizer, OCR stack, or retrieval service is required for local operation.
- Do not understate the current local capability envelope for GPT-5.4, and do not overstate unsupported modalities such as audio/video.

## System Context
**What this becomes:** an ingestion decision that updates `knowledge/topics/**`, `knowledge/provenance/**`, and `knowledge/sources/**`.

**Execution model:** the agent is local, the skill is local, and the source files are local. Native model capability is the default tool for understanding the source material.

**Current host capability envelope (2026-04-02):** use the Section 3.2 host capability snapshot. In this prompt, assume GPT-5.4 text/image reasoning in the active local lanes; treat PDF handling as available only when the active runtime surface exposes documented file input. Audio/video are not current assumptions for this prompt.

**User experience moment:** later agents will search these topic pages under time pressure and will trust them to answer “what do we know?”, “what is current?”, and “where did this come from?” quickly.

**Why quality matters:** if you overfit to source layout, pollute the graph with weak or duplicated pages, hide provenance, or silently rely on unapproved machinery, the knowledge system becomes a junk drawer instead of a semantic memory.

## Inputs & Ground Truth
You will receive some or all of the following bindings:

- `source_records`
  - preserved source ids, local paths, source kinds, timestamps, and sensitivity hints
- `local_paths`
  - one or more local filesystem paths that you are expected to inspect directly
- `existing_topic_snapshots`
  - the current content of relevant topic pages, if any
- `existing_provenance_snapshots`
  - recent provenance notes, if any
- `ingest_hints`
  - caller hints about likely topics or intended use
- `authority_rules`
  - the current precedence rules, such as live doctrine outranking session-derived material
- `approved_helpers`
  - optional explicit approval metadata, valid only if it includes:
    - exact `helper_id`
    - approver = `Amir`
    - `decision_log_ref`
    - allowed scope
    - expiry or timebox
    - whether it is a fallback/exception

Ground-truth rules:
- Treat the local files themselves as primary evidence when paths are provided.
- Use only the material actually provided or directly readable from those local paths.
- If part of a source is unreadable or ambiguous, say so explicitly.
- If a source is sensitive, paraphrase or point to it; do not copy restricted contents into the graph.
- Existing topic snapshots are authoritative for current page state; you are proposing changes, not pretending the page is empty.
- If `approved_helpers` is absent, or if any required approval field is missing, you do not have approval to introduce or rely on helper scripts/harnesses.
- If an approved helper is marked as a fallback/exception, it is invalid unless the enclosing plan/package has `fallback_policy: approved` and the referenced Decision Log entry records the timebox plus removal plan.

## Tools & Calling Rules
- Inspect the provided local files directly before deciding anything.
- Use native multimodal capability for images and similar local artifacts when needed.
- For PDFs, use direct local inspection when the active runtime surface exposes documented file input. If the active surface does not expose that path yet, fail loudly or record a visible reading-limit/runtime-capability gap rather than assuming a hidden converter/helper exists.
- Use source ids and concrete locators when citing evidence.
- If the package contains multiple sources, compare them before deciding whether they reinforce, refine, or conflict.
- Do not browse the internet.
- Do not assume hidden repo context beyond what is explicitly provided.
- Do not perform writes; return the ingestion decision only.
- Do not create or invoke helper scripts, helper harnesses, or deterministic preprocessing layers unless `approved_helpers` explicitly authorizes that exact helper with a valid Decision Log reference and scope.
- If you believe a helper is necessary but approval is absent, say so explicitly and return `human_review_required` rather than smuggling the helper into the workflow.

## Operating Principles
- Organize by meaning first, source-family never first.
- Local-file inspection is the default. Do not pretend a normalizer or transport layer is required when it is not.
- Extract durable knowledge, not incidental chatter.
- Treat provenance as mandatory, not optional.
- One source may feed many topics, and one topic may depend on many sources.
- Respect authority:
  - live doctrine outranks raw runtime truth when doctrine is the governing policy
  - raw runtime truth outranks mirrors or projections when the question is “what actually happened?”
  - historical support and internal sessions can justify knowledge pages, but they do not automatically become live doctrine
- Prefer updating an existing topic over creating a near-duplicate.
- Create or recommend question/conflict handling when the signal is real but unresolved.
- Preserve uncertainty explicitly.
- Never let a runtime, repo, or file path dictate the top-level knowledge taxonomy.
- Use only v1 page kinds:
  - `topic`
  - `playbook`
  - `decision`
  - `glossary`
- If a PDF or image supports a claim, capture locators or visual references when you can do so honestly.
- If visual or structural understanding is incomplete, record the gap instead of pretending certainty.

## Process
1. Inspect the local source paths directly and identify the real semantic subject matter.
2. Classify each source for:
   - source kind
   - authority tier
   - sensitivity
   - reading mode
   - whether it is primary evidence, support, or likely noise
3. Identify the durable knowledge units:
   - principles
   - playbooks
   - decisions
   - patterns
   - regressions
   - glossary items
   - open questions
4. Compare those knowledge units to the provided topic snapshots:
   - update existing topic
   - create new topic
   - append evidence only
   - recommend split/merge/rehome
   - no change
5. Draft provenance metadata honestly:
   - if one source is being ingested, draft one provenance note for that source
   - if multiple tightly coupled sources are being ingested together, draft one provenance note per source or an explicit bundle note with bundle rationale
   - always state what each source contributes, how it was read, and what limitations or uncertainties remain
6. Surface conflicts, missing context, and authority collisions instead of guessing.
7. Validate the whole decision:
   - every non-trivial knowledge unit has evidence
   - no topic path is source-family-first
   - every topic action uses an allowed v1 page kind
   - no secret content is copied
   - any reading limitations are visible
   - no weak session material is silently promoted to doctrine
   - no unapproved helper is used or implied
8. Before stopping, ask whether one more obvious in-scope improvement would materially strengthen the ingestion decision. If yes, make it.

## Quality Bar
- Great output extracts the real learning, places it in the right semantic location, cites evidence cleanly, and is honest about uncertainty, authority, and reading limits.
- It sounds like a careful librarian-architect using strong local model judgment, not like a chat summarizer, a filesystem sorter, or an overbuilt ETL pipeline.
- Weak output is source-family-shaped, overconfident, generic, or technically valid but useless for future retrieval.

## Output Contract And Validation
Return exactly one fenced `json` block and nothing else.

Top-level keys are required and must appear in this order:
- `ingest_summary`
- `source_reading_reports`
- `topic_actions`
- `provenance_notes`
- `conflicts_or_questions`
- `asset_actions`
- `recommended_next_step`

Use this exact shape:

```json
{
  "ingest_summary": {
    "source_ids": ["string"],
    "primary_domains": ["string"],
    "authority_tier": "live_doctrine | raw_runtime | historical_support | generated_mirror | mixed",
    "sensitivity": "public | internal | restricted_prompt_bearing | secret_pointer_only | mixed",
    "semantic_summary": "1-3 sentence summary of the actual knowledge contribution"
  },
  "source_reading_reports": [
    {
      "source_id": "string",
      "reading_mode": "direct_local_text | direct_local_pdf | direct_local_image | direct_local_multimodal | mixed",
      "approved_helpers_used": [
        {
          "helper_id": "string",
          "decision_log_ref": "string",
          "purpose": "string",
          "allowed_scope": ["string"],
          "expires_at": "string | null",
          "fallback_exception": false
        }
      ],
      "readable_units": ["string"],
      "gaps": ["string"],
      "confidence_notes": ["string"]
    }
  ],
  "topic_actions": [
    {
      "topic_path": "string",
      "page_kind": "topic | playbook | decision | glossary",
      "action": "create | update | append_evidence | split_suggest | merge_suggest | rehome_suggest | no_change",
      "candidate_title": "string",
      "why": "why this topic should change",
      "knowledge_units": [
        {
          "kind": "principle | playbook | decision | pattern | regression | glossary | question",
          "target_section": {
            "section_id": "string | null",
            "heading": "string"
          },
          "statement": "the durable knowledge to add or revise",
          "rationale": "why this belongs on this topic",
          "authority_posture": "live_doctrine | supported_by_runtime | supported_by_internal_session | tentative | mixed",
          "confidence": "high | medium | low",
          "evidence": [
            {
              "source_id": "string",
              "locator": "page number, heading, message hint, image region note, or other honest anchor",
              "notes": "optional redaction, uncertainty, or helper-use note"
            }
          ]
        }
      ]
    }
  ],
  "provenance_notes": [
    {
      "source_ids": ["string"],
      "bundle_rationale": "string | null",
      "title": "string",
      "summary": "1-3 sentence provenance summary",
      "source_reading_summary": "how the source was read and any limitations",
      "what_this_source_contributes": ["string"],
      "knowledge_sections_touched": [
        {
          "topic_path": "string",
          "section_heading": "string"
        }
      ],
      "sensitivity_notes": "string"
    }
  ],
  "conflicts_or_questions": [
    {
      "type": "conflict | missing_context | authority_collision | taxonomy_question | weak_signal | helper_needed",
      "topic_path": "string",
      "description": "string",
      "suggested_handling": "apply_now | queue_rebuild | human_review"
    }
  ],
  "asset_actions": [
    {
      "asset_ref": "string",
      "action": "preserve_only | attach_to_topic | caption_and_attach | redact",
      "target_topic_path": "string",
      "why": "string"
    }
  ],
  "recommended_next_step": {
    "action": "apply_now | queue_rebuild_topic | human_review_required",
    "scope": ["string"],
    "why": "string"
  }
}
```

Validation rules:
- `topic_actions` may be empty only if the source package truly adds no durable knowledge; if empty, explain why in `ingest_summary.semantic_summary`.
- Every `knowledge_unit` must have at least one evidence locator.
- `topic_path` must be semantic. Bad: `codex/2026-02-27-runbook`. Good: `doctrine/shared-agent-learnings`.
- `page_kind` must be one of `topic | playbook | decision | glossary`. Do not create `domain`, `concept`, or `question` pages in v1.
- Use `mixed` when authority is genuinely mixed; do not silently collapse it.
- Every `source_reading_reports[]` entry must map to a `source_id` listed in `ingest_summary.source_ids`.
- `approved_helpers_used` must be empty unless approval was explicitly provided in the inputs with exact helper id, Decision Log ref, scope, and timebox.
- `provenance_notes` must either be one-per-source or include an explicit non-empty `bundle_rationale`.
- If reading is partial or uncertain, at least one `gap` or `confidence_note` must explain why.
- If the source is sensitive, redact in `notes` and `sensitivity_notes` rather than omitting the provenance entirely.

## Error / Reject Handling
- Reject only if the system cannot preserve the source or cannot write truthful provenance metadata.
- Ordinary ambiguity is not a reject. Return tentative classifications and explicit questions instead.
- Partial reading is not a reject. Use visible gaps and confidence notes when the source is preserved and traceable but only partly promotable into semantic knowledge.
- Sparse signal is not a reject. Use `no_change`, `weak_signal`, or `human_review` when appropriate.
- Sensitive runtime or prompt-bearing material is not a reject. Preserve pointer-level provenance and redact the content.
- If two sources conflict, do not choose silently. Record the conflict and authority posture.
- If a helper seems necessary but approval is absent or underspecified, do not proceed as if it were approved. Record `helper_needed` and return `human_review_required`.

## Examples

### Example 1: Codex session about shared agent learnings

Input shape:
- `source_id`: `codex.session.2026-02-27.019ca013-71c8-7c21-8d94-f4f5c1f3fc56`
- `local_path`: `/Users/agents/.codex/sessions/2026/02/27/rollout-2026-02-27T11-09-14-019ca013-71c8-7c21-8d94-f4f5c1f3fc56.jsonl`
- semantic hint: user wants a common place where all agents write learnings such as release learnings, breakages, resolutions, and reusable runbooks

Good decision shape:
- `source_reading_reports[0].reading_mode = direct_local_text`
- `approved_helpers_used = []`
- update `doctrine/shared-agent-learnings`
- update `operations/releases/post-release-followup-runbooks`
- update `doctrine/runbooks-vs-crons`
- authority posture stays session-derived, not live doctrine

Why this is right:
- one source contributes to several semantic topics
- none of those topics should be filed under `codex/`
- the session is meaningful evidence, but it does not automatically outrank live doctrine

### Example 2: Live doctrine markdown about workflow rules

Input shape:
- `source_id`: `paperclip.doc.workflow_guide.current`
- `local_path`: `/Users/agents/workspace/paperclip_agents/PRINCIPLES.md`
- semantic hint: workflow law and sanctioned coordination path

Good decision shape:
- `source_reading_reports[0].reading_mode = direct_local_text`
- `approved_helpers_used = []`
- update `doctrine/authority-and-precedence`
- update `doctrine/skills/skill-authoring` only if the guide materially constrains skill usage or workflow boundaries
- if an internal session-derived topic conflicts with this guide, record `authority_collision` and prefer doctrine in the recommended next step

Why this is right:
- the semantic subject is workflow law and precedence
- the file path contains `paperclip`, but the topic should still be semantic, not source-family-based
- this source may legitimately outrank weaker session-derived pages

### Example 3: Local PDF with diagrams and text

Input shape:
- `source_id`: `research.pdf.lesson-onboarding.2026-04-02`
- `local_path`: `/Users/agents/workspace/fleki/research/lesson-onboarding.pdf`
- semantic hint: onboarding, progression, and learner trust

Good decision shape:
- inspect the PDF directly if the active runtime surface exposes documented PDF input
- preserve the original file under `sources/**`
- update `product/learning-experience/placement-and-onboarding`
- capture page numbers or figure references when they materially support a claim
- if the active runtime surface cannot read the PDF directly, fail loudly or return a visible reading-limit/runtime-capability note instead of assuming a converter/helper
- if some diagrams are ambiguous, record the limitation explicitly instead of pretending certainty
- `approved_helpers_used = []` unless explicit approval was provided

Why this is right:
- the agent is expected to try direct understanding first
- the PDF is evidence for semantic topics, not a filing destination
- any ambiguity stays visible in provenance
- runtime-surface-specific PDF gaps are surfaced honestly instead of being papered over with hidden machinery

### Example 4: Anti-example

Bad decision:
- create `topics/codex/2026-02-27-common-place-for-agents.md`
- copy a long chat chronology into the topic page
- mark it `live_doctrine`
- pretend every runtime needs a converter before it can read PDFs
- implicitly depend on an unapproved or underspecified helper script

Why this is bad:
- the topic path is source-family-first
- chronology was preserved instead of durable knowledge
- authority was overstated
- the local multimodal-agent model was ignored
- unapproved machinery was smuggled into the architecture

## Anti-Patterns
- Filing by runtime, repo, date, or file extension when the knowledge is actually semantic.
- Writing “summary pages” that just retell the source.
- Creating a new topic because the wording is new even when the meaning belongs on an existing page.
- Treating every user preference utterance as company doctrine.
- Omitting evidence because the claim feels obvious.
- Pretending the agent needs a transport layer, normalizer, OCR pipeline, or retrieval service before it can inspect local sources.
- Introducing an unapproved helper as if it were already part of the system.
- Using examples as a hidden lookup table instead of applying the governing principles.

## Checklist
- Did I inspect the local files directly first?
- Is the semantic subject clearer than the source-family label?
- Did every durable knowledge unit get evidence?
- Did authority and sensitivity stay honest?
- Did I update the smallest correct topic set?
- Did I avoid duplicating an existing topic?
- Did I surface conflicts instead of guessing them away?
- Did I avoid implying or using unapproved helper machinery?
- Would a downstream agent trust this ingestion decision during search and trace?
```

## 5.7 Reference Skill Draft - `knowledge`

This is the draft shared skill package for the runtime-facing surface. It exists because the workflow is larger than a one-shot prompt: agents need one reusable contract for saving source material into the semantic graph, searching the graph, tracing claims back to evidence, rebuilding affected topics, and checking graph health.

Repeated user problem:
- agents across different local runtimes need one shared way to contribute to and retrieve from company knowledge without inventing their own filing systems

Canonical user asks:
- "Save this Codex session into the knowledge graph and update the right semantic topics."
- "Search what we already know about Slack-first lesson authoring and cite the paths."
- "Trace why we think four-step lessons are the right contract and show me the provenance."

Anti-case:
- "Summarize this one PDF for me, but do not file it or connect it to the shared graph."

Suggested lean package:
- `SKILL.md`
- `references/save-ingestion.md`
- `references/search-and-trace.md`
- `references/storage-and-authority.md`
- `references/examples-and-validation.md`

Suggested reference ownership:
- `references/save-ingestion.md`
  - owns the `knowledge save` decision contract, JSON schema, authority and sensitivity handling, and the detailed prompt currently drafted in section 5.6
- `references/search-and-trace.md`
  - owns query shaping, citation expectations, ambiguity handling, and provenance-walk behavior for `search` and `trace`
- `references/storage-and-authority.md`
  - owns taxonomy rules, semantic-path invariants, authority tiers, provenance requirements, and rebuild boundaries
- `references/examples-and-validation.md`
  - owns canonical use cases, anti-cases, and the validation matrix for trigger quality and execution quality

Draft `SKILL.md`:

```md
---
name: knowledge
description: "Use the shared semantic markdown knowledge graph to save new source material, search what the company knows, trace claims back to provenance, rebuild affected topics, or inspect graph status. Use when work depends on durable company knowledge or must add new evidence; not for generic repo search, one-off summarization, or direct manual filing."
metadata:
  short-description: "Use the shared semantic knowledge graph"
---

# Knowledge

Use this skill when the shared company knowledge graph is the right interface, either as the destination for new source material or as the retrieval surface for existing knowledge.

This skill is about semantic knowledge with provenance, not artifact filing, generic search, or ad hoc note dumping.

Assume the agent is local, the skill is local, and the source files are local. Direct filesystem inspection and native multimodal reasoning are the default operating model.

Use the dated host capability snapshot in Section 3.2 for current-host modality claims. In this pass, that means GPT-5.4-backed local text/image reasoning, with PDF handling only where the active runtime surface exposes documented file input. Do not assume missing capability there, and do not overclaim audio/video support or universal PDF passthrough where the current docs do not support it.

## When to use

- The user wants to save sessions, docs, PDFs, images, notes, or other source material into the shared semantic knowledge graph.
- The work depends on company-specific knowledge and should search existing topic pages instead of relying on memory or raw file spelunking.
- The user asks where a belief, workflow, policy, lesson, design rule, or product decision came from.
- The graph may need a scoped rebuild because a topic cluster, backlinks, or indexes are stale after meaningful new ingestion.
- The user asks about graph freshness, queue state, coverage, or ingestion health.

## When not to use

- The task is generic repo exploration, code search, or raw file inspection that does not need shared company knowledge.
- The user wants a one-off summary, rewrite, or extraction without filing the result into the shared graph.
- The work is primarily task coordination, agent management, or project planning rather than knowledge retrieval or ingestion.
- The right artifact is a repo-local doc, `AGENTS.md` rule, or temporary scratch note rather than shared semantic memory.
- The only thing needed is a raw artifact transform with no semantic filing decision.

## Non-negotiables

- Organize by meaning first, never by source-family first.
- Use local file access and native multimodal reasoning first. Do not invent missing capability where the runtime already has it.
- Keep capability claims precise: for the current default lane, text and images are in scope; PDF handling is in scope where the active runtime surface exposes documented file input; audio/video are not implicit v1 assumptions.
- Provenance is mandatory for every non-trivial claim.
- Preserve authority posture honestly. Session material, runtime traces, and generated outputs do not become live doctrine without basis.
- Prefer updating the smallest correct topic set over creating near-duplicates.
- Canonical graph state may only be mutated through the shared `knowledge` contract. If that contract is unavailable, stop and report the gap instead of editing the graph directly.
- Do not add or rely on helper scripts, helper harnesses, retrieval indexes, or deterministic preprocessors unless Amir has explicitly approved that exact helper.
- Treat helper approval as real policy, not a loose flag: the approval must identify the exact helper, point to the Decision Log entry, define scope, and define expiry/timebox.
- If the approval is a fallback/exception, it is invalid unless the plan/package also sets `fallback_policy: approved` and the Decision Log entry includes a timebox plus removal plan.
- Cite concrete paths, ids, or provenance notes in answers that depend on graph content.
- If support is weak or conflicting, say so explicitly instead of smoothing it over.
- Handle sensitive material by preserving pointer-level provenance and redacting secrets or prompt-bearing values.
- If the shared interface is unavailable, say that clearly and do not pretend an ingest, rebuild, or graph-backed search succeeded when it did not.

## First move

1. Classify the job as `save`, `search`, `trace`, `rebuild`, or `status`.
2. Restate the user need in semantic terms rather than source-system terms.
3. Identify the minimum scope needed:
   - local source paths for `save`
   - topic cluster or question for `search`
   - claim plus expected lineage for `trace`
   - smallest affected area for `rebuild`
   - exact subsystem or freshness question for `status`
4. Load only the references needed for that command.
5. Return cited results, an explicit ingestion decision, or a clear gap.

## Workflow

### `knowledge search`

- Search semantic pages and likely aliases first.
- Prefer existing knowledge pages and indexes over raw source artifacts.
- Read semantic pages directly and inspect provenance or raw sources only when needed.
- Return the most relevant findings with cited topic ids/paths or provenance paths.
- Apply authority as a ranking rule, not a decorative note. If live doctrine conflicts with weaker material, surface doctrine first and label weaker/conflicting material explicitly.
- Include authority or confidence notes whenever they affect ordering, confidence, or recommended next action.
- Do not return raw `sources/**` as ordinary search hits.
- Do not assume a retrieval index or service exists. If one is ever approved later, treat it as an assistant, not as the source of truth.
- If the answer is thin, ambiguous, or stale, say what follow-up `trace`, `save`, or narrower search would sharpen it.

### `knowledge trace`

- Use this when the real question is "why do we believe this?" or "where did this come from?"
- Prefer stable ids or section refs when available. Claim text is acceptable as lookup input, not as durable identity.
- Walk from the claim or locator to the relevant knowledge page, then to provenance notes, then to source records.
- Distinguish live doctrine, supported practice, historical support, and tentative inference.
- Surface conflicts, missing evidence, or authority collisions instead of choosing silently.

### `knowledge save`

- Treat inputs as source material, not as filing destinations.
- Inspect the local source files directly before making semantic decisions.
- Preserve the source first and record honest reading limits before filing knowledge.
- Extract durable knowledge units and map them to the smallest correct semantic topic set.
- Preserve source records and provenance notes for every material change. If multiple sources are ingested together, preserve per-source reading/provenance detail or an explicit bundle rationale.
- Apply bounded synchronous changes to the smallest affected page sections and queue wider reorganization for `rebuild` when needed.
- Prefer updating existing topics when the meaning already has a home.
- Default to `topic` when the right page kind is otherwise unclear.
- Surface taxonomy questions, weak signals, and authority collisions instead of guessing.
- If a helper script or harness seems necessary, stop and require explicit approval instead of sneaking it into the workflow.
- Follow `references/save-ingestion.md` for the full ingestion decision contract.

### `knowledge rebuild`

- Use this when topic structure, backlinks, indexes, or derived pages may need recomputation.
- Rebuild the smallest relevant scope first.
- Report what changed, what moved, and which conflicts or merge/split/rehome suggestions remain open.
- Do not use rebuild as a substitute for unresolved semantic judgment.

### `knowledge status`

- Use this when the caller needs health, freshness, queue depth, coverage state, or failed-work visibility.
- Report the specific subsystem or topic area under discussion, not a vague global reassurance.
- Highlight the most decision-relevant next action when status reveals drift or backlog.

## Output expectations

- `search`
  - concise answer with cited topic ids/paths or provenance paths and the minimum useful authority note
- `trace`
  - lineage from knowledge page or section to provenance note to source record, plus any conflict or weakness
- `save`
  - ingestion decision or result summary with touched page sections, reading limitations, provenance consequences, helper-use disclosure, and the next step
- `rebuild`
  - scoped rebuild result with affected topics, material reorganizations, and unresolved taxonomy or authority questions
- `status`
  - current graph signal with the most relevant freshness, backlog, or integrity note

## Reference map

- `references/save-ingestion.md`
  - semantic extraction, provenance discipline, JSON contract, authority handling, sensitivity handling
- `references/search-and-trace.md`
  - semantic query shaping, result citation rules, trace walk behavior, ambiguity handling
- `references/storage-and-authority.md`
  - topic-path invariants, source/provenance/knowledge boundaries, authority tiers, rebuild boundaries
- `references/examples-and-validation.md`
  - canonical use cases, anti-cases, validation matrix, and representative examples
```
<!-- arch_skill:block:target_architecture:end -->

---

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## 6.1 Change map (table)

| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| ---- | ---- | ------------------ | ---------------- | --------------- | --- | ------------------ | -------------- |
| Canonical storage model | `knowledge/**`, `src/knowledge_graph/repository.py`, `src/knowledge_graph/frontmatter.py`, `src/knowledge_graph/models.py` | `KnowledgeRepository` layout + persistence | Implemented repo-local SSOT for semantic pages, provenance notes, source records, assets, receipts, and an approval-gated `knowledge/search/README.md` reserve | No further repo code change required in v1; keep `knowledge/**` authoritative | The system now has durable, inspectable knowledge state without hidden helper infrastructure | `KnowledgeRepository`, on-disk layout v1 | `tests/test_save.py`, `tests/test_search_trace_status.py`, `tests/test_rebuild.py` |
| Stable ids + locators | `src/knowledge_graph/ids.py`, `src/knowledge_graph/repository.py` | `knowledge_id`, `section_id`, `source_id`, trace refs, current-path aliases | Implemented opaque ids, stable section keys, immutable source ids, current-path alias resolution, and trace-target resolution in the repo-local core | No further repo code change required in v1; keep path moves alias-safe | Rehome/rebuild and trace now stay stable without treating claim text as identity | locator contract v1 | `tests/test_contracts.py`, `tests/test_rebuild.py` |
| Authority / precedence / redaction policy | `src/knowledge_graph/authority.py`, `src/knowledge_graph/validation.py` | authority tier + precedence + safe-derived rules | Implemented canonical tiers, postures, reading modes, and helper/fallback gating used by save/search/trace/status/rebuild | No further repo code change required in v1; keep one policy boundary | Live doctrine, runtime readback, history, and sensitive raw sources stay differentiated | authority policy v1 | `tests/test_contracts.py`, `tests/test_search_trace_status.py`, `tests/test_source_families.py` |
| Shared knowledge skill package | `skills_or_tools/knowledge/**` | `SKILL.md` + reference package | Implemented the canonical shared skill package plus reference files and published identical copies into the runtime discovery surfaces used in this pass | No further repo code change required in v1; keep `skills_or_tools/knowledge/**` authoritative | The public surface now exists on disk instead of only in the plan | `SKILL.md`, `references/save-ingestion.md`, `references/search-and-trace.md`, `references/storage-and-authority.md`, `references/examples-and-validation.md` | `tests/test_skill_package.py` |
| Save workflow + provenance writer | `src/knowledge_graph/repository.py`, `src/knowledge_graph/validation.py` | `knowledge save` | Implemented library-backed save behavior that preserves sources, records reading mode/helper usage, writes provenance notes, updates the smallest correct topic set, and emits receipts | No further repo code change required in v1; keep graph mutation inside the shared contract only | The core product is semantic knowledge compilation, not helper-driven conversion infrastructure | `knowledge save`, save receipt contract v1 | `tests/test_save.py`, `tests/test_source_families.py` |
| Search + trace workflow | `src/knowledge_graph/repository.py`, `src/knowledge_graph/authority.py` | `knowledge search`, `knowledge trace` | Implemented authority-aware search over semantic pages plus provenance-backed trace resolution with cited paths | No further repo code change required in v1; keep retrieval page-first and citation-bearing | Search and trace are useful without a service, daemon, or approval-free index | `knowledge search`, `knowledge trace`, result contracts v1 | `tests/test_search_trace_status.py` |
| Rebuild workflow | `src/knowledge_graph/repository.py`, `src/knowledge_graph/models.py` | `knowledge rebuild` | Implemented page rehome/supersession behavior, index refresh, and rebuild receipts over the same on-disk graph | No further repo code change required in v1; keep rebuild separate from bounded save | The graph can reorganize semantically without losing trace continuity | `knowledge rebuild` contract v1 | `tests/test_rebuild.py` |
| Status + receipts | `src/knowledge_graph/repository.py` | `knowledge status` | Implemented graph-health status, rebuild-pending visibility, contradiction counts, recent-command receipts, and helper-use disclosure | No further repo code change required in v1; keep receipts on-disk and caller-visible | The system has visible operational state without hidden runtime state | `knowledge status`, receipt payloads | `tests/test_search_trace_status.py`, `tests/test_save.py` |
| Codex packaging | `skills_or_tools/knowledge/**`, `.agents/skills/knowledge/**` | direct Codex caller surface | The canonical skill package is published into the workspace-local Codex discovery surface and live direct Codex `save/search/trace` proof exists on this host | No further repo code change required in v1; keep workspace publication in sync with the canonical skill package | Direct Codex is the cleanest v1 proof anchor and is now live | Codex local skill path | `tests/test_skill_package.py` plus end-to-end smoke |
| Paperclip distribution path | `src/knowledge_graph/runtime_manifests.py`, `/Users/agents/workspace/paperclip_agents/skills/knowledge/**` | company-skill / `desiredSkills` distribution | A repo-owned Paperclip skill publication exists as a byte-matched real-file mirror of the canonical skill package, the runtime manifest exposes `desired_skills: [knowledge]` for the Codex lane, and a live Paperclip import plus reversible `desiredSkills` sync smoke succeeded on this host | No further repo code change is required in `fleki`; keep runtime publications materialized as real files rather than symlinked leaves | Paperclip stays a reuse/control-plane surface, not a second backend | Paperclip repo-owned skill publication and company-managed distribution of the Codex lane | `tests/test_runtime_manifests.py` plus live Paperclip import/sync smoke |
| Hermes packaging | `src/knowledge_graph/runtime_manifests.py`, `/Users/agents/workspace/agents/agents/_shared/skills/knowledge/**`, `/Users/agents/.hermes/skills/knowledge/**` | Hermes local caller surface | Hermes now has shared-repo and trusted-local skill publications, and live same-host `search/trace/save` smoke succeeded without a wrapper/backend fork | No further repo code change required in v1; keep Hermes packaging thin and shared-skill-first | Hermes is the second live proof lane and remains runtime-neutral | Hermes local knowledge surface | `tests/test_runtime_manifests.py` plus end-to-end smoke |
| OpenClaw packaging | follow-on only; no repo path yet | memory/skill alias layer | Intentionally absent in v1; the plan still defers OpenClaw implementation on this host | No repo code change required for v1 | OpenClaw remains legacy prior art and follow-on alias work, not a current proof surface | OpenClaw alias path | follow-on only |
| Approval-gated helpers | future helper area only if explicitly approved | any script, harness, index, converter, or service helper | No helper is approved yet | Keep helpers excluded by default; if one is later approved, record approval, scope, and usage in provenance/receipts | Prevents quiet drift into deterministic infrastructure | helper approval gate | manual review until approved |
| Optional publishing | `src/publish/**` or Quartz adapter | viewer export | No viewer exists yet | Add downstream export only if it stays secondary | Viewer is useful but not primary | read-only export contract | optional later |

## 6.2 Migration notes
- Deprecated APIs if any:
  - None yet; this is greenfield in this repo.
- Delete list:
  - Do not allow runtime-specific storage forks to appear as "temporary" shortcuts.
  - Do not let a viewer/export directory become the only place the knowledge graph lives.
  - Do not introduce a hidden DB-only state that the markdown tree cannot reconstruct.
  - Do not add a generic `answer` verb to the shared skill surface just because it feels convenient.
  - Do not let `sources/**` become the primary browse surface just because it is easier to implement first.
  - Do not let prompt injection surfaces, AGENTS/custom prompt loaders, session stores, shell snapshots, heartbeat flows, or runtime hooks masquerade as the canonical `knowledge` API.
  - Do not reintroduce transport-first or service-first architecture into the local path.
  - Do not add helper scripts, helper harnesses, retrieval indexes, converters, or other deterministic support machinery without explicit approval from Amir.
  - Do not let descriptor-only image content masquerade as authoritative semantic evidence.
- Cleanup and migration notes:
  - Implementation should still choose exact module/file names without changing the public contract: one canonical semantic tree, one `save/search/trace/rebuild/status` boundary, one local skill-first execution model, and one bounded-save-vs-rebuild lifecycle.
  - If a helper is later approved, the plan must record why local direct inspection was insufficient, where the helper is allowed, and how its use is disclosed in provenance and receipts.

## 6.3 Pattern Consolidation Sweep (anti-blinders; scoped by plan)

| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| ---- | ------------- | ---------------- | ---------------------- | ------------------------------------- |
| Codex caller path | `skills_or_tools/knowledge/**`, `.agents/skills/knowledge/**` | one five-verb public skill surface over the shared tree | prevents Codex-specific storage semantics or prompt-only drift | include |
| Paperclip distribution path | `src/knowledge_graph/runtime_manifests.py`, `/Users/agents/workspace/paperclip_agents/skills/knowledge/**` | distribute the same canonical skill package through the Paperclip repo-owned publication instead of inventing a Paperclip backend | prevents Paperclip-only backend drift | include |
| Hermes caller path | `src/knowledge_graph/runtime_manifests.py`, `/Users/agents/workspace/agents/agents/_shared/skills/knowledge/**`, `/Users/agents/.hermes/skills/knowledge/**` | expose the same `knowledge` contract through shared/trusted skill publication | prevents canonical state from drifting into runtime-specific tooling | include |
| OpenClaw caller path | follow-on only; no repo path yet | thin memory/skill alias into the shared contract | prevents OpenClaw-specific storage forks | defer |
| Approval-gated helper anti-case | any future scripts, indexes, converters, daemons, or helper harnesses | excluded until explicitly approved | prevents quiet drift into deterministic infrastructure | exclude by default |
| Runtime internals anti-case | AGENTS/custom prompt loaders, session stores, shell snapshots, heartbeat flows, hook systems | explicitly do not become canonical knowledge API or storage | prevents architecture drift into runtime-specific control planes | exclude |
| Viewer/export layer | `src/publish/**`, Quartz or equivalent | downstream read-only consumer of the markdown tree | prevents viewer becoming write authority | defer |
| Generic answer surface | any `knowledge answer` or runtime-specific final-answer wrapper | do not add in v1 | prevents the knowledge system from swallowing caller-agent reasoning responsibility | exclude |
<!-- arch_skill:block:call_site_audit:end -->

---

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan (tests optional). No fallbacks/runtime shims: the system must work correctly or fail loudly. The default executor is a local multimodal agent, not a deterministic helper stack. Do not add scripts, harnesses, indexes, or converters without explicit approval from Amir. Prefer programmatic checks per phase; defer manual/viewer verification to finalization. Avoid negative-value tests. Document new invariants only at the canonical boundaries.

## Phase 1 - Core contracts, on-disk layout, and shared skill package

- Status:
  - COMPLETE
- Completed work:
  - Added the repo-local `knowledge_graph` core package with stable id generation, frontmatter handling, authority rules, helper-approval validation, and canonical layout initialization.
  - Materialized the shared `skills_or_tools/knowledge/**` skill package and reference files from the drafted public contract.
  - Added visible top-level knowledge-tree scaffolding in-repo under `knowledge/**`.
- Manual QA (non-blocking):
  - Completed 2026-04-03: `skills_or_tools/knowledge/SKILL.md` still matches the intended runtime-facing contract.

- Goal:
  - Lock the canonical storage model, identity rules, authority policy, and shared `knowledge` skill package before any runtime-specific proof work begins.
- Work:
  - Create the repo layout for `knowledge/topics/**`, `knowledge/provenance/**`, `knowledge/sources/**`, `knowledge/assets/**`, and `knowledge/receipts/**`.
  - Reserve any `knowledge/search/**` support state as README-only and approval-gated rather than assuming it belongs in the first implementation slice.
  - Implement the foundational contracts:
    - opaque `knowledge_id`
    - stable `section_id`
    - immutable `source_id`
    - current-path alias resolution
    - authority/precedence/redaction rules
    - source-reading report rules
    - helper approval validation including `fallback_policy: approved` for true exceptions
  - Lock the allowed v1 page kinds and section-level provenance model in code and docs.
  - Materialize `skills_or_tools/knowledge/**` from the drafted prompt/skill/reference material already embedded in this plan so the public layer stops living only inside the doc.
  - Keep same-host local usage as the default path and remote ingestion as a future extension of the data model, not a first implementation concern.
- Verification (smallest signal):
  - Contract checks cover ids, page kinds, authority precedence, provenance shape, and helper approval validation.
  - One repo-local markdown note can be represented end to end through the canonical contract as one source record, one provenance note, one touched topic section, and one save receipt without requiring rebuild or runtime packaging.
- Docs/comments (propagation; only if needed):
  - Add one short invariant comment at the storage boundary and one at the helper-approval boundary.
- Exit criteria:
  - The on-disk SSOT exists and is readable.
  - The shared `knowledge` skill package exists on disk in executable draft form.
  - The plan’s public contract, authority policy, and helper gate are now represented in code/package boundaries rather than only in prose.
- Rollback:
  - Revert the new storage/package modules before any caller surface depends on them.

## Phase 2 - `knowledge save` core plus direct Codex first proof slice

- Status:
  - COMPLETE
- Completed work:
  - Implemented `knowledge save` as a library-backed contract that preserves sources, writes provenance notes, updates semantic topic pages, and records receipts plus rebuild-pending scopes.
  - Added tests covering core save behavior, helper-policy enforcement, and semantic-path validation.
- Manual QA (non-blocking):
  - No open manual QA in this phase; the live direct Codex `save` smoke already succeeded against `docs/phase6_smoke_inputs/codex_semantic_capture.md`.

- Goal:
  - Ship the first actually usable local lane by making `knowledge save` work end to end through the shared skill for direct Codex on text-first local sources.
- Work:
  - Implement the save workflow and provenance writer for:
    - markdown/text docs
    - Codex session/source artifacts
    - multi-source ingest with per-source reading reports or explicit bundle rationale
  - Persist save receipts and rebuild-pending signals from the same code path.
  - Wire the shared `knowledge` skill into the direct local Codex path and verify graph mutation only happens through that shared contract.
  - Fail loudly on unapproved helpers, missing source readability, or contract violations instead of falling back to hidden transforms.
  - Keep search/trace shallow or internal-only if needed here; do not block the first save slice on richer retrieval.
- Verification (smallest signal):
  - One direct Codex run saves one markdown note and one real Codex session source into the same tree, writes receipts, and updates the smallest correct topic sections without a rebuild.
  - One attempted helper-dependent path without valid approval fails loudly and records the right gap.
- Docs/comments (propagation; only if needed):
  - Add one short comment at the save entrypoint that canonical graph mutation must go through the shared contract only.
- Exit criteria:
  - Direct Codex is a real usable v1 proof slice for `knowledge save`.
  - Save produces source records, provenance notes, touched-page updates, receipts, and rebuild-pending visibility for core text/session sources.
  - No runtime-specific storage semantics or prompt-only shortcuts have appeared.
- Rollback:
  - Remove Codex wiring and save-path implementation while keeping Phase 1 contracts/package intact.

## Phase 3 - Source-family expansion for images, PDFs, and runtime-origin artifacts

- Status:
  - COMPLETE
- Completed work:
  - Extended the same save path to preserve PDF, image, Hermes-runtime, and secret-pointer-only source families without introducing helper machinery.
  - Added tests covering PDF/image/runtime-family preservation and pointer-only handling for sensitive sources.
  - Ran one live direct Codex multimodal `knowledge save` using the attached `docs/phase6_smoke_inputs/knowledge_image_input.png` plus `docs/phase6_smoke_inputs/knowledge_pdf_input.pdf`, which produced `knowledge/receipts/save/receipt_agovdd67cmcebqdgq2xxkjv7ye.md`, `knowledge/topics/knowledge-system/multimodal-runtime-validation.md`, `knowledge/provenance/images/prov_agovdd67cp6pqrtytwur2io2iq.md`, and `knowledge/provenance/pdf/prov_agovdd67cp33sbnyphfnc4nxmi.md`.
  - Verified the live multimodal result through repo-local `search`, `trace`, and `status`; the PDF was directly readable and the PNG was preserved with an honest IHDR CRC decode-failure reading limit instead of fabricated visual certainty.
- Manual QA (non-blocking):
  - None.

- Goal:
  - Extend the same save path to the source families that matter most to the product vision without introducing helper machinery as architecture.
- Work:
  - Add source classification and provenance behavior for:
    - standalone images
    - representative Hermes-origin artifacts
    - representative Paperclip-origin doctrine/runtime artifacts
    - PDFs where the active runtime surface exposes documented file input
  - Preserve original assets and record locators, visual references, runtime-capability gaps, or uncertainty notes honestly.
  - Ensure image/PDF/runtime-origin evidence flows into the same topic/provenance/source structure rather than branching into source-family-specific storage logic.
  - Keep all helper use out of scope unless explicitly approved after a real failure mode is observed.
- Verification (smallest signal):
  - One sample image, one representative runtime-origin artifact, and one sample PDF through a validated PDF-capable runtime surface all save through the same contract and produce usable provenance-backed page updates.
  - One partially understood source produces a truthful reading-limit/runtime-capability gap instead of fabricated certainty.
- Docs/comments (propagation; only if needed):
  - Document the exact boundary where the agent must report uncertainty instead of inferring unsupported detail.
- Exit criteria:
  - Supported source families land cleanly in the archive through one save path.
  - PDF behavior is honest and runtime-surface-specific rather than overclaimed.
  - The system still has no approval-free deterministic helper stack.
- Rollback:
  - Revert only the added source-family handlers and test corpus artifacts; keep the Phase 1-2 core intact.

## Phase 4 - `search`, `trace`, and `status` over the semantic graph

- Status:
  - COMPLETE
- Completed work:
  - Implemented page-first `search`, lineage-preserving `trace`, and receipt-driven `status` over the on-disk graph.
  - Added authority-aware retrieval tests so live doctrine outranks weaker internal-session support when both match.

- Goal:
  - Make the stored corpus operationally useful before tackling wider semantic reorganization.
- Work:
  - Implement `knowledge search` to read semantic pages first, then provenance, with cited and authority-aware results.
  - Implement `knowledge trace` to walk from page/section/path alias or best-effort claim lookup to provenance and source lineage.
  - Implement `knowledge status` so callers can see rebuild-pending areas, reading-limit gaps, recent receipts, and integrity issues without hidden state.
  - Keep helper retrieval/index state absent by default; if someone wants it later, that is a separate approval decision.
  - Make sure receipts for save/search/trace/status all disclose helper use, authority posture, and unresolved gaps.
- Verification (smallest signal):
  - Against a small mixed corpus, one search query returns the right cited pages, one trace query shows the source chain, and one status query surfaces pending rebuild/readability state.
  - Search does not outrank live doctrine with weaker internal-session evidence when both are present.
- Docs/comments (propagation; only if needed):
  - Add one note at the authority-ranking boundary so future changes do not flatten live doctrine and weaker support into the same class.
- Exit criteria:
  - The graph is useful for real retrieval, trace, and health inspection without a viewer and without a retrieval service.
  - Search/trace/status operate on the same canonical tree and receipt model as save.
- Rollback:
  - Revert the retrieval/status modules and leave saved sources/provenance/pages intact.

## Phase 5 - `rebuild` and semantic reorganization lifecycle

- Status:
  - COMPLETE
- Completed work:
  - Implemented `rebuild` page rehome support, alias preservation, supersession updates, and deterministic index refresh for topic indexes.
  - Added rebuild tests showing a page can move without losing searchability or trace continuity.

- Goal:
  - Add the global graph-maintenance step that can reorganize knowledge without breaking trace continuity or the bounded-save model.
- Work:
  - Implement `knowledge rebuild` for split/merge/rehome, backlink refresh, index refresh, contradiction surfacing, and supersession recording.
  - Keep `save` bounded: preserve source, write provenance, update the smallest correct page sections, and mark wider work pending instead of doing global reorganization inline.
  - Ensure rebuild can reread source/provenance/page state and produce deterministic on-disk results at the persistence boundary while still relying on the local agent as the primary semantic executor.
  - Record rebuild receipts that explain what moved, what changed, and what remains unresolved.
- Verification (smallest signal):
  - A page touched by `save` is searchable/traceable before rebuild, and a later rebuild can rehome or split it without changing source identity or losing trace continuity.
  - One contradiction or taxonomy question is surfaced explicitly rather than silently flattened.
- Docs/comments (propagation; only if needed):
  - Add one short comment at the rebuild planner clarifying that paths may move but ids and provenance lineage must remain stable.
- Exit criteria:
  - Rebuild owns the wider semantic reorganization lifecycle cleanly.
  - Save and rebuild no longer compete for the same responsibilities.
  - The graph can evolve over time without losing evidence or supersession history.
- Rollback:
  - Revert rebuild/reorganization logic while preserving the saved archive and retrieval surfaces.

## Phase 6 - Hermes proof, Paperclip reuse, and v1 boundary cleanup

- Status:
  - COMPLETE
- Completed work:
  - Added thin runtime-manifest helpers for Codex, Hermes, and Paperclip so the shared skill path and packaging metadata are represented inside this repo.
  - Published the canonical `knowledge` skill into the direct Codex workspace surface at `.agents/skills/knowledge` without forking the skill body.
  - Published the same single-sourced skill into the Hermes-owned shared repo surface at `../agents/agents/_shared/skills/knowledge`.
  - Published the same single-sourced skill into the Paperclip-owned repo skill surface at `../paperclip_agents/skills/knowledge`.
  - Published the same single-sourced skill into the trusted Hermes local skills home at `~/.hermes/skills/knowledge` so Hermes has a native local path that does not require runtime-specific wrapper logic.
  - Materialized the published skill leaf files as real files across the Codex, Hermes, and Paperclip runtime surfaces after live Paperclip import showed that symlinked leaf files were not discoverable by the Paperclip importer.
  - Proved a live same-host direct Codex `save` against the real repo tree using `docs/phase6_smoke_inputs/codex_semantic_capture.md`, which produced linked topic, provenance, source, and receipt records under `knowledge/**`.
  - Proved a live same-host Hermes `search` plus `trace` against the Codex-authored knowledge, with path-cited retrieval back to the generated provenance note and preserved source record.
  - Proved a live same-host Hermes `save` against `docs/phase6_smoke_inputs/hermes_runtime_publication.md`, which produced `knowledge/topics/knowledge-system/runtime-integration.md`, its provenance note, preserved source record, and save receipt under `knowledge/**`.
  - Proved the Hermes-to-Codex return leg by running direct Codex `search` / `trace` against the Hermes-authored runtime-integration topic and its provenance/source chain.
  - Proved a live Paperclip-managed `codex_local` reuse/distribution smoke on this host by importing `../paperclip_agents/skills/knowledge` as company skill `local/fef28301b2/knowledge`, syncing it onto the `CEO` agent's `desiredSkills`, verifying the managed skill appeared as desired/configured, restoring the agent to its baseline required skills, and removing the earlier duplicate import that pointed at the Fleki canonical source path.
- Manual QA (non-blocking):
  - None.

- Goal:
  - Prove the second local caller surface, confirm reuse/distribution through Paperclip, and lock the v1 boundary so follow-on surfaces do not silently expand scope.
- Work:
  - Wire Hermes into the same `knowledge` contract through the smallest thin local surface that fits the shared-skill-first model.
  - Prove same-host cross-surface use: Codex can file knowledge that Hermes can search/trace, and Hermes can file knowledge that Codex can search/trace.
  - Add the thinnest Paperclip reuse/distribution path for the same Codex lane without creating a Paperclip-specific backend.
  - Confirm the remote-ready seam is still a data-model property, not a local transport project.
  - Explicitly defer:
    - OpenClaw implementation
    - viewer/export work
    - any helper stack
  - Remove or reject any accidental runtime-specific writers, hidden state, or service-style detours that may have appeared during implementation.
- Verification (smallest signal):
  - Direct Codex can `save` into the shared tree and Hermes can `search` / `trace` that same knowledge with path citations.
  - Hermes can `save` into the same tree and direct Codex can `search` / `trace` the Hermes-authored knowledge with path citations.
  - Hermes can discover `knowledge` through its native local skill index and the shared repo publication without introducing a wrapper/backend fork.
  - The Paperclip reuse/distribution path is published as a byte-matched real-file mirror of the canonical skill package, can be imported through the local authenticated board path, and can be synced onto a `codex_local` agent's `desiredSkills` without changing storage semantics.
- Docs/comments (propagation; only if needed):
  - Add one wrapper-boundary note that runtime packaging may change invocation shape but must never fork storage or semantic rules.
- Exit criteria:
  - The v1 proof pair, direct Codex plus Hermes, works end to end on this host.
  - Paperclip reuse/distribution is proven through a live same-host import plus reversible agent assignment on the repo-owned `skills/knowledge` publication, without creating a second backend.
  - OpenClaw remains explicitly deferred follow-on work, not implied hidden scope.
  - The shipped slice is same-host useful and remote-ready in data shape without dragging transport architecture into v1.
- Rollback:
  - Remove wrapper/distribution layers while keeping the core knowledge tree, contracts, and workflows intact.
<!-- arch_skill:block:phase_plan:end -->

---

# 8) Verification Strategy (common-sense; non-blocking)

> Principle: avoid verification bureaucracy. Prefer the smallest existing signal.
> Default: 1-3 checks total. Do not invent new harnesses, frameworks, scripts, or helper infrastructure as part of verification, and do not add helper scripts/harnesses to the product without explicit approval.
> Default: keep viewer/manual verification as finalization, not as an implementation gate.
> Default: do NOT create proof tests for deletions, visual constants, or doc inventories.
> Also: document tricky invariants only at the SSOT or contract boundary.

## 8.1 Unit tests (contracts)
- Source-record and reading-report contract rules.
- Stable knowledge-id, section-id, and source-id generation.
- Allowed page-kind enforcement.
- Authority-tier and source-layer classification rules.
- PDF/image provenance, reading-limit, asset-reference, and runtime-capability-gap contracts.
- Provenance-note contract that preserves source linkage and touched-page section tracking.
- Search result contract that enforces page-first citations, authority exposure, and default exclusion of raw `sources/**`.
- Trace result contract that preserves id/section lineage, path-alias resolution, and supersession handling back to source materials.

## 8.2 Integration tests (flows)
- Save markdown, image, and one runtime-origin or Codex-session source into one corpus, plus one PDF through a host-validated runtime surface with documented PDF file input, all through direct local agent inspection, and verify the touched page is searchable/traceable before a full rebuild.
- Re-run compile/reorganization without losing source provenance, authority metadata, stable ids, or supersession history.
- Query search against the compiled corpus and verify cited knowledge-page and authority-aware results.
- Verify one mixed-authority corpus where a session-derived page does not outrank a relevant doctrine page when doctrine should win.
- Verify one partially understood source produces a truthful gap report.
- Query trace against one result and verify source lineage.
- Query `status` after mixed ingest and verify rebuild-pending areas, reading-limit gaps, and recent-command visibility are surfaced without hidden control-plane state.

## 8.3 E2E / device tests (realistic)
- One same-host end-to-end run from direct Codex that saves a small mixed corpus.
- One same-host direct Codex `search` that returns a page hit and resolves it through `trace`.
- One same-host `search` and one same-host `trace` from Hermes that retrieve and explain the same material through the shared local contract.
- One same-host Paperclip company-skill import plus temporary `desiredSkills` sync/restore against the repo-owned `skills/knowledge` publication, proving reuse of the Codex lane without changing storage semantics.
- Optional later viewer/export smoke only if a secondary read surface lands in the first implementation window.

---

# 9) Rollout / Ops / Telemetry

## 9.1 Rollout plan
- Start as a same-host local tool/skill in this repo.
- Keep adoption opt-in until the archive and search contract are proven on a curated sample corpus.
- Only after that should we consider making the skills default guidance for more agent surfaces.

## 9.2 Telemetry changes
- Record structured ingest receipts, compile receipts, and search receipts in a rebuildable form.
- Prefer plain on-disk logs/receipts tied to source ids and knowledge ids over opaque control-plane-only state.
- Track enough data to answer: what source was ingested, how it was read, whether any approved helper was used, what changed in compilation, what search returned, what failed, and which ingests left unresolved gaps or `rebuild_pending`.

## 9.3 Operational runbook
- Need clear commands or skill usage for:
  - ingesting a local source
  - re-running compilation
  - tracing a claim back to evidence
  - diagnosing missing assets, reading-limit reports, failed ingests, or path-citation misses
- Default helper status should be obvious in the runbook:
  - `approved helpers in use: none` unless explicitly changed by Amir
- Viewer/publish runbook stays optional until a real secondary read surface exists.

---

# 10) Decision Log (append-only)

> Read newest entries last. When entries conflict, the later 2026-04-02 anti-deterministic local-agent decisions supersede the earlier transport/search/PDF-fidelity experiments.
> Historical entries marked as superseded are retained only to explain plan drift. They are not live architecture guidance. Operative guidance lives in TL;DR, Section 0, Sections 5-8, and the newest non-superseded decisions.

## 2026-04-02 - Start runtime-neutral and same-host first

Context
- The request explicitly wants one knowledge system that works across different agent types and does not lock the company into Hermes, Paperclip, or any single runtime being the permanent executor.

Options
- Build the first version around one dedicated runtime-specific archivist agent.
- Build the first version around runtime-neutral skills and on-disk contracts, then decide later whether a dedicated worker is useful.
- Delay the project until remote ingestion and viewer/publishing are fully designed upfront.

Decision
- Start with a runtime-neutral, skills-first architecture and a same-host local first slice. Keep the execution model open so the eventual implementation can be caller-executed, scheduled, or handled by a dedicated worker without changing storage semantics.

Consequences
- The first planning passes must focus on data model, ingest, compile, and search boundaries rather than on choosing a permanent runtime owner prematurely.
- Remote ingestion and polished viewer surfaces are explicitly delayed so they do not block a first useful system.

Follow-ups
- Use the next research/deep-dive passes to choose the simplest first executor model that preserves the runtime-neutral contract.

## 2026-04-02 - Work backward from narrow shared verbs, not a generic wiki bot

Context
- The request explicitly asked to mock the future disk shape and the exact skill requests/responses first, and to make those part of the North Star.

Options
- Design around one generic “knowledge agent” that owns storage, answering, and publishing.
- Design around a narrow shared skill surface that owns save/search/trace/rebuild/status, while caller agents still own final prose answers and higher-level reasoning.

Decision
- Use the narrow shared skill surface as the design center. This aligns with the real repeated workflow and avoids building another vague super-agent that duplicates normal agent reasoning.

Consequences
- The storage model, receipts, and search/trace result contracts become the main product surface.
- The future `knowledge` skill must be strong at classification, provenance, and retrieval, not at pretending to be the final answerer for every downstream ask.

Follow-ups
- Validate the exact verb set and response shapes before moving deeper into implementation planning.

## 2026-04-02 - Make semantic knowledge the product and source storage the support layer

Context
- The initial framing drifted toward an artifact-organizational system. The correction from the user was explicit: this system is for organizing knowledge semantically, while preserving links back to source materials with provenance notes.

Options
- Organize the on-disk tree primarily by source family (`codex/`, `paperclip/`, `hermes/`, `pdfs/`, etc.) and treat knowledge pages as a secondary view.
- Organize the on-disk tree primarily by semantic domains/concepts/playbooks/decisions and preserve source materials plus provenance as the support layer behind them.

Decision
- Make semantic knowledge pages the primary product surface. Preserve source materials in `sources/**` and bridge them to the semantic tree through `provenance/**`, but do not let the source archive become the primary browsing model.

Consequences
- The canonical disk layout, acceptance criteria, and examples now center on semantic pages such as runtime recovery, shared agent learnings, lesson style/copy/UX baselines, and skill-authoring patterns.
- Search returns semantic pages first, with provenance/source refs as supporting evidence.
- `trace` becomes mandatory because it is what keeps a semantic system honest instead of turning it into uncited synthesis.

Follow-ups
- Keep validating that new examples and implementation plans stay knowledge-first and provenance-backed rather than drifting back toward artifact filing.

## 2026-04-02 - Separate the public `knowledge` verbs from the runtime transport

> Historical note: this entry captured an earlier transport-heavy framing. The later 2026-04-02 decisions below supersede any implication that MCP or CLI boundaries are architectural requirements for local v1 operation. The seam descriptions below are drift history, not current guidance.

Context
- The runtime-code review across local Codex, Hermes, and OpenClaw showed that each stack had different candidate extension seams in the earlier transport-heavy framing. That framing is historical only; the live document now treats local skill-first packaging as the default.
- The same review also showed that prompt loaders, custom prompts, hooks, heartbeats, session DBs, shell snapshots, and similar internals are tempting but wrong places to anchor the shared contract.

Options
- Force every runtime to use the exact same low-level mechanism and contort runtimes that do not fit it.
- Keep the public `knowledge save/search/trace/rebuild/status` surface stable while letting runtimes reach one shared core through the thinnest clean adapter they already support.
- Accept runtime-specific backends and storage semantics as the price of "native" integrations.

Superseded proposal
- Keep one shared `knowledge` core and one stable public verb surface, but separate that from transport details and use the thinnest runtime-native boundary available.

Historical consequences
- The plan now explicitly distinguishes:
  - public `knowledge` verbs
  - core storage/compiler/search/trace behavior
  - historical transport surfaces that were once under consideration
  - runtime-native packaging surfaces such as Codex local skills, Paperclip company-skill distribution, Hermes shared skills plus optional wrappers, and OpenClaw legacy alias/memory surfaces
- Future implementation work should avoid reusing runtime prompt/session internals as the primary data plane, even when those internals are useful as provenance sources or local orchestration surfaces.

Current replacement
- See `2026-04-02 - Supersede transport-first assumptions with local multimodal agent execution`.

Historical follow-ups
- Use the next deep-dive pass to choose the smallest first proof pair and to decide whether the Hermes adapter should call the core through a local CLI boundary or direct library import.

## 2026-04-02 - Lock the v1 proof pair to direct Codex plus Hermes

> Historical note: the proof pair remains valid. Any transport-specific details in this entry were superseded later the same day by the local-skill-first decisions below.

Context
- The runtime review showed that direct Codex is the cleanest first proof anchor on this host, while Hermes is the live runtime of record and proves the adapter split across a materially different integration style.
- Paperclip mostly reuses the Codex lane as a distribution/control-plane surface, and OpenClaw is valuable prior art but retired on this host.

Options
- Leave the first proof pair open and decide during implementation.
- Use direct Codex plus Hermes as the first proof pair, with Paperclip and OpenClaw remaining documented follow-on surfaces.
- Use direct Codex plus Paperclip because that is the easiest path to demo quickly.

Decision
- Lock the v1 proof pair to direct Codex plus Hermes.

Consequences
- Phase 4, Definition of Done, and verification now target:
  - direct Codex local `knowledge` skill against the shared tree
  - Hermes shared-skill/local adapter against that same tree
- Paperclip stays important, but as a v1 reuse/distribution surface for the Codex lane rather than as the portability proof itself.
- OpenClaw remains future prior art and an optional follow-on adapter path, but not a currently validated runtime seam on this host.

Follow-ups
- Keep Paperclip skill-isolation concerns visible as follow-on risk.
- Revisit OpenClaw only after the Codex plus Hermes proof pair works end to end.

## 2026-04-02 - Historical: CLI-first boundary for the Hermes adapter (superseded)

> Historical note: this entry is superseded by the later local-skill-first decisions below. Hermes still needs a thin local surface, but CLI-first is no longer locked as architecture, and the seam wording below is drift history rather than live guidance.

Context
- Hermes had multiple plausible local surfaces in the earlier draft, including shared skills, optional wrappers, and hooks, and the remaining question was whether any thin wrapper should call the `knowledge` core through a local CLI contract or direct library import.
- The plan already separates public verbs from transport, and the runtime review showed Hermes session DB, prompt state, and external skills should remain adjacent surfaces rather than the data plane.

Options
- Let a thin Hermes local wrapper call the core through a structured local `knowledge` CLI contract.
- Let that thin Hermes local wrapper import the core library directly in process.

Superseded proposal
- Use a CLI-first boundary for Hermes v1. Direct library import is deferred unless measured latency later proves the CLI boundary is the bottleneck.

Historical consequences
- Hermes stays runtime-neutral and does not bind the plan to one implementation language or in-process package ABI.
- Plugin/gateway failures have a smaller blast radius than with direct in-process import.
- `pre_llm_call` remains an ephemeral retrieval surface and does not become the shared data plane.

Current replacement
- See `2026-04-02 - Supersede transport-first assumptions with local multimodal agent execution` and the current Section 5 Hermes packaging language.

Historical follow-ups
- If a later measurement shows CLI overhead is the real bottleneck on a hot path, allow a timeboxed revisit with an explicit Decision Log update instead of quietly changing the boundary.

## 2026-04-02 - Lock the v1 semantic model and save/rebuild lifecycle

Context
- The earlier draft still left page kinds, provenance granularity, and save-vs-rebuild behavior as open architecture questions, even though later sections were already leaning toward one concrete shape.
- The v1 proof pair is local Codex plus Hermes on one host, which makes low-latency local saves and stable traceability more valuable than a maximally expressive first semantic model.

Options
- Keep broader page kinds such as `domain`, `concept`, and `question`, and defer the final semantic model to implementation time.
- Lock a narrower v1 semantic model with stable ids, section-level support, bounded synchronous save work, and heavier rebuild work.
- Push most semantic updates into `rebuild` and make `save` preserve-only.

Decision
- Lock v1 to page kinds `topic | playbook | decision | glossary`, with domains expressed through folders/indexes.
- Use section-level support on knowledge pages, backed by page-level provenance notes per source or tight source bundle.
- Use opaque stable `knowledge_id`, stable `section_id`, and immutable `source_id`; treat paths/slugs as mutable aliases.
- Make `knowledge save` perform bounded synchronous page/section updates, while `knowledge rebuild` owns split/merge/rehome, backlink/index refresh, and wider graph reorganization.

Consequences
- The plan now has one concrete v1 semantic model instead of several plausible ones.
- `save` can make new knowledge searchable and traceable immediately without waiting for a full rebuild.
- Rebuild remains the place where taxonomy evolves without breaking trace continuity.

Follow-ups
- If future high-stakes or disputed claims need finer evidence, add optional claim-level provenance later instead of bloating v1.

## 2026-04-02 - Historical: page-first lexical search proposal (superseded)

> Historical note: this entry is superseded by the later decision that search is LLM-first over semantic pages and provenance, with helper retrieval machinery only by explicit approval.

Context
- The draft still treated the search stack as an open question, but the rest of the plan already required authority-aware, provenance-backed, same-host retrieval with path-cited results.
- A model-dependent hot path would add cost, latency, and nondeterminism before the basic graph/search contract exists.

Options
- Use lexical-only search.
- Use page-first lexical plus metadata search with deterministic authority-aware reranking.
- Put lightweight model assistance in the default search path from day one.

Superseded proposal
- Lock v1 search to page-first lexical plus metadata over `knowledge/topics/**`, backed by one rebuildable embedded `SQLite FTS5` index.
- Keep `knowledge/provenance/**` as secondary evidence or explicit scope and keep raw `knowledge/sources/**` out of default search hits.
- Keep MCP `search` and `trace` as tool surfaces and use MCP resources/templates only for deterministic reads of pages, indexes, provenance, or locators.

Historical consequences
- Search behavior is now deterministic, cheap, and inspectable enough for same-host agent use.
- Authority posture becomes part of ranking instead of a post-hoc note.
- Model-assisted reranking and query expansion are explicitly follow-on work rather than an accidental v1 dependency.

Current replacement
- See `2026-04-02 - Supersede deterministic search and PDF/image assumptions`.

Historical follow-ups
- If measured retrieval failures show lexical plus metadata is insufficient, revisit model assistance with a Decision Log update instead of quietly adding it.

## 2026-04-02 - Historical: text-layer PDF ingest proposal (superseded)

> Historical note: this entry is superseded by the later decision that image ingest is LLM-first local multimodal inspection, while PDF ingest is local-agent-first only where the active runtime surface exposes documented PDF file input, both with honest provenance and reading-limit reporting.

Context
- The plan already rejected perfect visual fidelity as a prerequisite, but it had not yet drawn a hard line between what v1 could promise honestly and what should wait for later enrichers.
- Host reality shows local text-layer PDF tools are already available, while no committed repo-local OCR/vision ingestion stack exists yet.

Options
- Promise best-effort PDF and image understanding without defining fidelity boundaries.
- Lock v1 to text-layer PDF normalization plus explicit partial-fidelity handling for incomplete readability, and treat image descriptors as derived metadata only.
- Add OCR/vision fallback by default so more inputs appear to work.

Superseded proposal
- Lock v1 PDF ingest to a replaceable `text-layer PDF -> page-aware markdown with locators` contract.
- Treat images and extracted figures as evidence-first inputs: preserve originals, keep derived renditions in `assets/**`, and keep descriptors in provenance/source metadata.
- Use explicit fidelity outcomes `applied | partial_fidelity | failed`.
- Do not add silent OCR or vision fallback in v1.

Historical consequences
- The system can preserve and trace PDFs and images honestly without pretending it understood more than it did.
- Partial readability is surfaced as an explicit ingest state rather than hidden behind overconfident semantic pages.
- OCR/vision can be added later as replaceable enrichers without changing the storage model.

Current replacement
- See `2026-04-02 - Supersede deterministic search and PDF/image assumptions` and the Section 3.2 host capability snapshot.

Historical follow-ups
- When OCR/vision is added later, require explicit provenance/versioning rules so evidence quality upgrades are visible instead of silent.

## 2026-04-02 - Supersede transport-first assumptions with local multimodal agent execution

Context
- The user explicitly corrected the architectural center: these agents are local, the skills are local, the agents already have filesystem access, and GPT-5.4-class agents in these harnesses already have the local text/image capability needed for first-pass understanding, with PDF handling available where the active runtime surface exposes documented file input.
- Earlier deep-dive passes over-weighted transport and deterministic preprocessing assumptions relative to that stronger product truth.

Options
- Keep treating transport seams and deterministic preprocessors as the architectural center for local operation.
- Treat local multimodal agent execution through the shared `knowledge` skill as the default engine, and demote transport details to optional packaging decisions.

Decision
- Supersede the earlier transport-first framing.
- The primary executor model is now explicitly: local multimodal agent + local `knowledge` skill + direct filesystem access.
- Runtime integration remains important, but only as thin packaging around that model.

Consequences
- Sections 0, 1, 3, 5, 6, 7, and 8 now repeat the same rule instead of leaving it implicit.
- MCP, CLI boundaries, and similar transport choices are no longer architectural commitments for local v1 operation.
- Any section that implies the agents need transport machinery before they can inspect local sources is now considered wrong by definition.

Follow-ups
- Keep runtime seam work focused on packaging and reuse, not on inventing a service architecture.

## 2026-04-02 - Add an anti-deterministic operating law and approval gate for helpers

Context
- The user explicitly wants this project biased toward strong model judgment and away from deterministic infrastructure that would later need to be unwound.
- The specific instruction was that scripts, harnesses, and similar machinery require explicit approval.

Options
- Allow helper scripts, indexes, converters, and harnesses to appear whenever they seem convenient during implementation.
- Require explicit approval before any such helper enters the architecture or codebase.

Decision
- Add an anti-deterministic operating law to the plan.
- Helper scripts, helper harnesses, retrieval indexes, converters, daemons, and similar deterministic support subsystems are excluded by default and require explicit approval from Amir before they are added.

Consequences
- The plan now treats these helpers as exceptions, not defaults.
- If one is ever approved later, its use must be visible in provenance and receipts instead of becoming hidden infrastructure.
- Verification may not smuggle in product helpers under the guise of convenience.

Follow-ups
- If a future helper request appears justified, record the reason local direct inspection was insufficient, the scope of the helper, and the removal or reevaluation plan.

## 2026-04-02 - Supersede deterministic search and PDF/image assumptions

Context
- Earlier decisions locked v1 search to lexical plus metadata and v1 ingest fidelity to text-layer PDF assumptions.
- The user’s correction is stronger: native model cognition is the default for both ingest and retrieval over the local markdown graph, and deterministic support machinery should not be assumed upfront.

Options
- Keep the earlier deterministic search and text-layer PDF assumptions as v1 architecture law.
- Treat search and ingest as LLM-first local behaviors, with optional support machinery considered later only by explicit approval.

Decision
- Supersede the earlier deterministic defaults as architectural center.
- Search is now defined first as reading semantic pages and provenance honestly through the local skill.
- Image ingest is now defined first as direct local multimodal inspection plus honest provenance and reading-limit reporting.
- PDF ingest is now defined first as direct local inspection through the active runtime surface when that surface exposes documented PDF file input, plus honest provenance and reading-limit reporting.

Consequences
- The architecture no longer requires a retrieval index, a PDF conversion pipeline, or an OCR stack to be present for local usefulness.
- Optional helpers remain possible later, but they are approval-gated and non-canonical.
- Provenance and receipts now carry the burden of honesty about what the agent actually read.

Follow-ups
- If later real usage justifies a helper retrieval or conversion layer, evaluate it as a narrow exception instead of backfilling it into the foundational doctrine.

## 2026-04-02 - Ground modality and agent-capability claims in official docs plus local runtime evidence

Context
- The user explicitly asked for an external-research pass so the plan would stop guessing about agent/model capability.
- Earlier plan passes correctly moved away from deterministic infrastructure, but they still spoke too loosely about what the actual current lane can and cannot do.
- On 2026-04-02, official OpenAI docs and local runtime code were reviewed together to ground the plan.

Options
- Keep capability language broad and implicit, even if it mixes documented support with extrapolation.
- Lock the plan to the documented current host capability envelope and require evidence for future modality expansions.

Decision
- Ground the plan in the current documented local lane:
  - GPT-5.4 with `xhigh` reasoning on this host
  - model capability: text input/output plus image input
  - file/API capability: PDF file input is documented at the API/runtime surface
  - local runtime verification in this audit: Codex image attachment flow, Hermes attachment/document preservation, and local file/shell/skill operation
- Treat end-to-end PDF interpretation as runtime-surface-specific until each adapter path is explicitly validated. Do not smuggle that in as if it were a core GPT-5.4 modality claim.
- Explicitly do not treat audio/video as v1 assumptions under the current GPT-5.4 lane unless a later model/runtime-specific research pass proves otherwise.
- Repeat this distinction throughout the plan so "anti-deterministic" does not collapse into capability guesswork.

Consequences
- The plan now says, repeatedly and explicitly, that local text/image understanding is available now and should be used directly, and that PDF handling is in scope where the active runtime surface exposes the documented file-input path.
- The plan also now says, repeatedly and explicitly, that unsupported or unverified modalities must not be quietly assumed just because some other model might support them.
- Model capability and runtime packaging are now separated cleanly:
  - Codex/Hermes/OpenClaw/Paperclip mostly change how the skill is surfaced
  - the core cognition/input capability claim comes from the actual model/runtime docs for the active lane

Follow-ups
- If a future version of the project wants audio or video ingestion, add that as an explicit evidence-backed capability decision with the exact model/runtime lane named, instead of broadening the current GPT-5.4 assumptions by vibe.

## 2026-04-02 - Tighten the public contract around helper approvals, multi-source ingest, and runtime-specific PDF handling

Context
- A later deep-dive consistency pass found that the public-layer prompt/skill draft was still weaker than the North Star and latest doctrine in three places:
  - helper approval looked like a loose caller flag instead of a real policy exception
  - `knowledge save` allowed multi-source ingest conceptually, but the output contract collapsed reading/provenance to singular objects
  - PDF handling was still phrased too much like a universal lane capability instead of a runtime-surface-specific path

Options
- Leave the public-layer drafts looser than the rest of the plan and resolve those gaps during implementation.
- Tighten the plan now so the prompt, skill, target architecture, and decision log all express the same contract.

Decision
- Helper approval is now a real contract:
  - exact helper id
  - approver = `Amir`
  - Decision Log reference
  - allowed scope
  - expiry/timebox
  - fallback/exception status
- `knowledge save` now treats multi-source ingest explicitly:
  - preserve per-source reading reports
  - preserve per-source provenance notes unless an explicit bundle rationale is given
- PDF handling is now stated precisely:
  - text/image reasoning comes from the active GPT-5.4 model lane
  - PDF handling is in scope where the active runtime surface exposes documented file input
  - if a runtime surface cannot do that yet, it must fail loudly or record a runtime-capability/readability gap rather than imply a hidden converter/helper
- Canonical graph state may only be mutated through the shared `knowledge` contract. If the contract is unavailable, the correct behavior is to stop and report the gap.

Consequences
- The prompt, skill draft, target architecture, and decision log now say the same thing about helper approval, batching, and PDF handling.
- The public layer is less likely to drift back into silent helper use, ad hoc graph edits, or overclaimed modality guarantees during implementation.
- The plan remains runtime-neutral while still being honest about the dated host snapshot used for current proof work.

Follow-ups
- If a future implementation wants true batch-ingest ergonomics beyond per-source provenance arrays, add an explicit bundle contract rather than flattening evidence into one synthetic source record.

## 2026-04-02 - Implement the first repo-local core as a library-backed knowledge contract with JSON frontmatter

Context
- The repo was effectively greenfield at implementation time.
- The architecture explicitly forbade approval-free helper scripts, harnesses, or service-style infrastructure.
- The fastest compliant path was to ship the canonical contract, skill package, and on-disk graph logic directly in-repo without adding a CLI/service boundary first.

Options
- Start with a CLI or helper-script wrapper around the knowledge graph.
- Start with a repo-local library core plus the shared skill package and let runtime packaging stay thin and follow later.

Decision
- Implement the first slice as a repo-local Python library plus a materialized shared `knowledge` skill package.
- Store markdown documents with JSON frontmatter so the repo can keep frontmatter machine-readable without introducing extra parsing dependencies or helper tooling.

Consequences
- The core product now exists in this repo as:
  - on-disk knowledge-tree scaffolding
  - validation and storage logic
  - save/search/trace/status/rebuild workflows
  - thin runtime manifests for Codex, Hermes, and Paperclip reuse
- The implementation respects the anti-deterministic law by avoiding new helper scripts, retrieval daemons, or transport layers.
- Runtime publications now exist across direct Codex, Hermes shared/trusted skill surfaces, and the Paperclip repo-owned skill surface. The live image/PDF save validation is complete, and the Paperclip same-host import/sync/restore smoke is also complete.

Follow-ups
- If live runtime integration exposes friction that the library boundary cannot handle cleanly, record that as a new decision instead of quietly introducing a script or service layer.

## 2026-04-02 - Materialize runtime skill publications as single-sourced mirrors, not copied skill forks

Context
- The repo-local core and canonical `knowledge` skill were already implemented, but Phase 6 still needed real runtime publications instead of manifest-only placeholders.
- The architecture forbids runtime-specific knowledge backends, wrapper-heavy glue, or copied skill forks that can silently drift apart.
- Hermes, Codex, and Paperclip each have existing local skill discovery surfaces that can publish the same skill body without changing storage semantics.

Options
- Copy the `knowledge` skill separately into each runtime surface and let the copies drift over time.
- Publish one canonical skill body into each runtime surface as a verified mirror so the runtime packaging is real but the skill content stays single-sourced.

Decision
- Materialize the runtime publications as single-sourced mirrors of the canonical `fleki/skills_or_tools/knowledge` package.
- Use the runtime-native discovery surfaces:
  - direct Codex workspace `.agents/skills`
  - Hermes shared repo publication plus trusted local `~/.hermes/skills`
  - Paperclip repo-owned `skills/`

Consequences
- Direct Codex now has a real workspace skill publication path.
- Hermes now has both repo-owned and trusted local publication paths without adding a wrapper or backend fork.
- Paperclip now has a repo-owned skill package it can scan/import/distribute without inventing a Paperclip-only knowledge surface.
- Skill edits remain single-sourced in `fleki`, which keeps the public contract from drifting across runtimes.

Follow-ups
- The Paperclip publication-shape correction is recorded in the later decision entry below; do not silently change publication shape again.

## 2026-04-02 - Paperclip repo-owned skill publications must use real-file mirrors, not symlinked leaf files

Context
- The earlier runtime publication step intentionally kept the canonical `knowledge` skill single-sourced, but it did so by leaving symlinked leaf files inside the published runtime directories.
- A live Paperclip company-skill import against `/Users/agents/workspace/paperclip_agents/skills/knowledge` failed with `No SKILL.md files were found in the provided path.`
- Importing the Fleki canonical source path succeeded immediately, which isolated the failure to the repo-owned publication shape rather than to the skill body itself.

Options
- Keep symlinked leaf files in the runtime publication surfaces and accept that the Paperclip importer cannot reliably scan the repo-owned publication.
- Materialize the published leaf files as real files while keeping `skills_or_tools/knowledge/**` authoritative and verifying byte-for-byte equality after publication.

Decision
- Materialize the published `SKILL.md` and reference files as real files in the runtime discovery surfaces used on this host.
- Keep `skills_or_tools/knowledge/**` as the canonical source of truth and treat runtime publications as verified mirrors, not independent forks.

Consequences
- Paperclip can import the repo-owned publication and distribute it as a company-managed skill without inventing a Paperclip-only backend.
- Single-source truth is enforced by byte-for-byte publication checks instead of by symlink behavior.
- The Paperclip same-host import plus reversible `desiredSkills` sync/restore smoke is now complete, so there is no remaining runtime-distribution follow-up for v1.

Follow-ups
- If a future runtime surface proves reliable symlink traversal and there is a measurable reason to switch publication shape, record that as a new decision instead of silently changing the publication policy.

## 2026-04-02 - Lock the authoritative implementation sequence to contract -> Codex save -> source-family expansion -> search/trace/status -> rebuild -> multi-surface proof

Context
- After the third deep-dive consistency pass, the previous four-phase implementation plan was still too coarse.
- It delayed the first usable Codex-backed slice, blurred `status` into later work, and did not make the v1 defer list explicit enough.

Options
- Keep the earlier four broad buckets and let implementation choose the detailed order ad hoc.
- Recast Section 7 into a depth-first sequence that delivers the first usable lane earlier and postpones wrappers until the core graph is already real.

Decision
- Recast the authoritative phase plan into six depth-first phases:
  - core contracts, on-disk layout, and shared skill package
  - direct Codex `save` proof slice
  - source-family expansion
  - `search` / `trace` / `status`
  - `rebuild`
  - Hermes proof plus Paperclip reuse/distribution

Consequences
- The first usable slice now appears earlier and is anchored to the cleanest v1 proof lane: direct Codex.
- `rebuild` is intentionally delayed until after retrieval and status are already useful over the saved graph.
- Hermes and Paperclip remain important, but they now sit clearly on top of a proven core instead of pulling packaging concerns into the first implementation phase.
- OpenClaw implementation and viewer/export work are now explicitly deferred rather than quietly implied.

Follow-ups
- `implement` should execute Section 7 in order and reopen Section 10 only if the real codebase forces a meaningful sequencing change.

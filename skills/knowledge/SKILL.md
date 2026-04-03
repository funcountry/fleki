---
name: knowledge
key: fleki/knowledge
description: "Use the shared markdown knowledge graph to save new source material, search what the company knows, trace exact refs back to provenance, rebuild affected topics, or inspect graph status. Use when work depends on durable company knowledge or must add new evidence; not for generic repo search, one-off summarization, or direct manual filing."
metadata:
  short-description: "Use the shared semantic knowledge graph"
---

# Knowledge

Use this skill when the shared company knowledge graph is the right interface, either as the destination for new source material or as the navigation surface for existing knowledge.

This skill is about semantic knowledge with provenance, not artifact filing, generic search, or ad hoc note dumping.

Assume the agent is local, the skill is local, and the source files are local. Direct filesystem inspection and native multimodal reasoning are the default operating model.

Use the dated host capability snapshot in the canonical architecture plan for current-host modality claims. In this pass, that means GPT-5.4-backed local text/image reasoning, with PDF handling only where the active runtime surface exposes documented file input.

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
- Canonical graph state may only be mutated through the shared `knowledge` contract. If the repo-local core library is available, use it instead of editing `knowledge/**` by hand.
- Do not add or rely on helper scripts, helper harnesses, retrieval indexes, or deterministic preprocessors unless Amir has explicitly approved that exact helper.
- The live graph root is `resolved_data_root`, usually `~/.fleki/knowledge`. The checked-in repo `knowledge/**` tree is reference content and a migration seed, not live mutable truth.
- `knowledge search` may list exact or literal candidates. `knowledge trace` must follow exact refs only. The agent reads the candidates and does the meaning-making.
- Treat helper approval as real policy, not a loose flag: the approval must identify the exact helper, point to the Decision Log entry, define scope, and define expiry/timebox.
- If the approval is a fallback/exception, it is invalid unless the plan/package also sets `fallback_policy: approved` and the Decision Log entry includes a timebox plus removal plan.
- Cite concrete paths, ids, or provenance notes in answers that depend on graph content.
- If support is weak or conflicting, say so explicitly instead of smoothing it over.
- Handle sensitive material by preserving pointer-level provenance and redacting secrets or prompt-bearing values.
- Copied PDFs now persist a source-adjacent render bundle (`.render.md`, `.render.manifest.json`, optional `.assets/`) before semantic filing; pointer-only or `secret_pointer_only` PDFs must surface an explicit render omission instead.
- `knowledge save` may mark a page `current` or `historical`; `knowledge rebuild` owns `stale` and delete.
- Agents should retire fully superseded or clearly stale knowledge through `knowledge rebuild`, not by hand-editing the graph.
- If the shared interface is unavailable, say that clearly and do not pretend an ingest, rebuild, or graph-backed search succeeded when it did not.

## First move

1. Classify the job as `save`, `search`, `trace`, `rebuild`, or `status`.
2. Restate the user need in semantic terms rather than source-system terms.
3. Identify the minimum scope needed.
4. Load only the references needed for that command.
5. Return cited results, an explicit ingestion decision, or a clear gap.

## Workflow

### `knowledge save`

- Treat inputs as source material, not as filing destinations.
- `knowledge save` is apply-only. There is no preview, validate-only, or dry-run save path.
- Each binding must declare `source_family`. Do not infer family from `source_kind` or file suffixes.
- Inspect the local source files directly before making semantic decisions.
- Preserve the source first and record honest reading limits before filing knowledge.
- For copied PDFs, treat the structured render bundle as repository-owned evidence that must exist before provenance and topic writes succeed; do not invent or hand-author render metadata in the semantic decision payload.
- Extract durable knowledge units and map them to the smallest correct semantic topic set.
- Preserve source records and provenance notes for every material change. If multiple sources are ingested together, preserve per-source reading/provenance detail or an explicit bundle rationale.
- Apply bounded synchronous changes to the smallest affected page sections and queue wider reorganization for `rebuild` when needed.
- Use `fact` for plain observations unless another kind adds stronger semantic meaning.
- Keep `ingest_summary.authority_tier` separate from `knowledge_units[].authority_posture`. `historical_support` is a tier, not a posture.
- Follow `references/save-ingestion.md` for the full ingestion decision contract.

### `knowledge search`

- Search exact ids, current paths, page aliases, and literal page text.
- Return zero results on a miss instead of a nearest-looking false positive.
- Prefer existing knowledge pages over raw source artifacts.
- Use the returned `trace_ref` as the handoff into `knowledge trace`.
- Read candidate pages directly and inspect provenance or raw sources only when needed.
- Do not return raw `sources/**` as ordinary search hits.

### `knowledge trace`

- Accepted refs are exact only: `knowledge_id`, `knowledge_id#section_id`, `current_path`, page alias, or `current_path#section_alias`.
- Walk from the exact page or section ref to provenance notes, then to source records.
- Use `knowledge search` first when you need discovery. Then feed the returned `trace_ref` into `knowledge trace`.
- For PDF-backed claims, continue the chain to the render manifest and stored render markdown or the explicit omission reason; `trace` is the canonical inspection surface for PDF fidelity state.
- If a PDF source record predates the render-or-omission contract, surface the `render_contract_gaps` entry and repair it with the repo maintenance script instead of pretending trace is complete.
- Distinguish live doctrine, supported practice, historical support, and tentative inference.
- Surface conflicts, missing evidence, or authority collisions instead of choosing silently.

### `knowledge rebuild`

- Rebuild the smallest relevant scope first.
- Report what changed, what moved, and which conflicts or merge/split/rehome suggestions remain open.
- Do not use rebuild as a substitute for unresolved semantic judgment.

### `knowledge status`

- Report the specific subsystem or topic area under discussion, not a vague global reassurance.
- Highlight the most decision-relevant next action when status reveals drift or backlog.
- Surface missing lifecycle metadata when older pages still have not been normalized.
- Treat `recent_topics` and `recent_source_ingests` as the primary recentness view once they are available; receipts and indexes are supporting evidence.
- Treat `status` as graph truth, not as a runtime-install health check.

## Install And Repair

- The human-edited skill package lives under `skills/knowledge/**`.
- From a Fleki repo checkout, install or update with one command:
  - `./install.sh`
- That installer:
  - installs the bundled `knowledge` CLI with PDF support through `docling`
  - installs Codex through the upstream `npx skills add` flow
  - copies the skill into every detected Hermes home and OpenClaw root on the machine
  - refreshes the machine install manifest and centralized `~/.fleki` knowledge-home layout
- From an already installed or copied bundle, repair the CLI and manifest with:
  - `bash install/bootstrap.sh`
- After install or repair, `knowledge status --json --no-receipt` should report the centralized `resolved_data_root` and the live `install_manifest_path`.

## Reference map

- `references/save-ingestion.md`
- `references/search-and-trace.md`
- `references/storage-and-authority.md`
- `references/examples-and-validation.md`
- `install/README.md`

---
name: knowledge
key: fleki/knowledge
description: "Use the shared markdown knowledge graph to save new source material, search what the company knows, trace exact refs back to provenance, rebuild affected topics, or inspect graph status. Use when work depends on durable company knowledge or must add new evidence; not for generic repo search, one-off summarization, or direct manual filing."
metadata:
  short-description: "Use the shared semantic knowledge graph"
---

# Knowledge

Use this skill as the default interface for shared company memory.

When the user is asking what Poker Skill already knows, already decided, already learned, or where a belief came from, start here before reconstructing the answer from session history or raw files.

The knowledge base is a persistent, provenance-backed company memory. It is not a generic file search, an ad hoc notes folder, or a replacement for fresh telemetry when the job is to measure what is live now.

When the agent creates or receives a durable report, packet, action plan, truth doc, or similar artifact, default to filing its reusable takeaways here instead of leaving them stranded in local artifacts.

Assume the agent is local, the skill is local, and the source files are local. Direct filesystem inspection and native multimodal reasoning are the default operating model.

## When This Skill Activates

- The user asks what the company already knows about a topic, issue, experiment, policy, workflow, lesson, design rule, or product decision.
- The user asks what previous research, telemetry packets, or earlier work already concluded.
- The user asks where a belief, workflow, policy, lesson, design rule, or product decision came from.
- The user wants to save sessions, docs, PDFs, images, notes, or other source material into the shared semantic knowledge graph.
- The agent just produced a durable artifact that another agent would reasonably want to reuse.
- The graph may need a scoped rebuild because a topic cluster, backlinks, or indexes are stale after meaningful new ingestion.
- The user asks about graph freshness, queue state, coverage, or ingestion health.

## Resuming Existing Knowledge

When the question depends on prior company knowledge, orient yourself in the shared graph before doing anything else:

1. If freshness, backlog, or coverage might matter, run `knowledge status --json --no-receipt`; otherwise skip straight to retrieval.
2. The first retrieval move for remembered-understanding questions is `knowledge search`, not `session_search` and not `knowledge status` by itself.
3. Start with `knowledge search` using the smallest likely literal topic path, alias, heading, or exact term.
4. Read the returned topic page and follow `trace_ref` into `knowledge trace` before presenting any non-trivial provenance-backed claim.
5. If `knowledge search` misses, look for the local artifact or report file before you use `session_search`.
6. If a durable local artifact answers the question, use that artifact and then save it into `knowledge` before you finish.
7. Fall back to `session_search`, Slack memory, or raw artifact spelunking only after a good-faith `knowledge search` miss or when the graph clearly lacks support.
8. If the turn creates durable new evidence, finish by saving or rebuilding the smallest affected topic set.

## When not to use

- The task is generic repo exploration, code search, or raw file inspection that does not need shared company knowledge.
- The user wants a one-off summary, rewrite, or extraction without filing the result into the shared graph.
- The work is primarily task coordination, agent management, or project planning rather than knowledge retrieval or ingestion.
- The right artifact is a repo-local doc, `AGENTS.md` rule, or temporary scratch note rather than shared semantic memory.
- The only thing needed is a raw artifact transform with no semantic filing decision.

## Non-negotiables

- Organize by meaning first, never by source-family first.
- Use local file access and native multimodal reasoning first. Do not invent missing capability where the runtime already has it.
- Keep capability claims precise: text and images are in scope; PDF handling is in scope where the active runtime surface exposes documented file input; audio/video are not implicit assumptions.
- Provenance is mandatory for every non-trivial claim.
- Preserve authority posture honestly. Session material, runtime traces, and generated outputs do not become live doctrine without basis.
- Prefer updating the smallest correct topic set over creating near-duplicates.
- Canonical graph state may only be mutated through the shared `knowledge` contract. If the repo-local core library is available, use it instead of editing `knowledge/**` by hand.
- Do not add or rely on helper scripts, helper harnesses, retrieval indexes, or deterministic preprocessors unless Amir has explicitly approved that exact helper.
- The live graph root is `resolved_data_root`, usually `~/.fleki/knowledge`. The checked-in repo `knowledge/**` tree is reference content, not live mutable truth.
- `knowledge search` may list exact or literal candidates. It does not do paraphrase lookup, token splitting, or best-guess retrieval.
- `knowledge trace` must follow exact refs only. The agent reads the candidates and does the meaning-making.
- Treat helper approval as real policy, not a loose flag: the approval must identify the exact helper, point to the Decision Log entry, define scope, and define expiry/timebox.
- If the approval is a fallback exception, it must still be explicit, scoped, and timeboxed.
- Cite concrete paths, ids, or provenance notes in answers that depend on graph content.
- If support is weak or conflicting, say so explicitly instead of smoothing it over.
- Every saved source must resolve to one durable artifact target. Non-secret sources are copied; `secret_pointer_only` sources are preserved as pointer-backed artifacts.
- Handle sensitive material by preserving pointer-backed artifacts and redacting secrets or prompt-bearing values where needed.
- Copied PDFs persist a source-adjacent render bundle (`.render.md`, `.render.manifest.json`, optional `.assets/`) before semantic filing; `secret_pointer_only` PDFs must surface an explicit render omission instead.
- `knowledge save` may mark a page `current` or `historical`; `knowledge rebuild` owns `stale` and delete.
- Agents should retire fully superseded or clearly stale knowledge through `knowledge rebuild`, not by hand-editing the graph.
- If the shared interface is unavailable, say that clearly and do not pretend an ingest, rebuild, or graph-backed search succeeded when it did not.

## First move

1. Decide whether the user is asking for remembered company knowledge, provenance, ingestion, rebuild, or graph status.
2. If the job is retrieval, default to `knowledge search` rather than `session_search`, `knowledge status` by itself, or raw file exploration.
3. If the job is ingestion, inspect the local source directly and use `knowledge search` plus `knowledge trace` to find the nearest existing semantic home before deciding whether to update or create.
4. Restate the user need in semantic terms and identify the minimum topic scope.
5. Classify the command as `save`, `search`, `trace`, `rebuild`, or `status`.
6. Return cited results, an explicit ingestion decision, or a clear gap.

## Workflow

### `knowledge save`

- Treat inputs as source material, not as filing destinations.
- Treat durable reports, packets, action plans, runbooks, and agent-authored artifacts as normal `knowledge save` inputs when they carry reusable company evidence.
- If the current turn created a durable artifact that another agent would not want to rediscover, default to saving it.
- Once the current turn already produced the durable artifact it needs, file it before opening a discretionary refinement or code-change loop. Do not start rewriting the generator, report script, or surrounding tooling unless the user explicitly asked for that change.
- Start by inspecting the local source directly.
- Before drafting the save decision, run `knowledge search` and `knowledge trace` for the nearest existing topic.
- Prefer updating the smallest existing semantic home over creating a duplicate chronology page.
- A good semantic home is enough. If no clear existing page is obvious, create the clearest topic and save instead of leaving the artifact local while you keep searching.
- Distill the takeaways yourself in normal automated contexts; do not wait for a separate human discussion step unless the user explicitly wants that collaboration.
- `knowledge save` is apply-only. There is no preview, validate-only, or dry-run save path.
- The CLI invocation shape is `knowledge save --bindings <bindings.json> --decision <decision.json> --json`.
- Build those temp JSON files from the real shell so `local_path` points at the actual artifact, not a sandbox copy.
- Each binding must declare `source_family`. Do not infer family from `source_kind` or file suffixes.
- Each binding must declare `timestamp` as ISO 8601 source-observed time.
- For a local artifact, use the real file mtime from the shell when that is the best source-observed time you have.
- If all you have is the source date, use that ISO 8601 date and note the date-only precision in `confidence_notes`. Do not skip the save over missing time-of-day detail.
- Inspect the local source files directly before making semantic decisions.
- Preserve the source in Fleki-owned storage first and record honest reading limits before filing knowledge.
- Callers do not choose copy vs pointer mode. Fleki copies non-secret sources and preserves pointer-backed artifacts only for `secret_pointer_only`.
- For copied PDFs, treat the structured render bundle as repository-owned evidence that must exist before provenance and topic writes succeed; do not invent or hand-author render metadata in the semantic decision payload.
- Extract durable knowledge units and map them to the smallest correct semantic topic set.
- Preserve source records and provenance notes for every material change. If multiple sources are ingested together, preserve per-source reading/provenance detail or an explicit bundle rationale.
- Apply bounded synchronous changes to the smallest affected page sections and queue wider reorganization for `rebuild` when needed.
- Use `fact` for plain observations unless another kind adds stronger semantic meaning.
- Keep `ingest_summary.authority_tier` separate from `knowledge_units[].authority_posture`. `historical_support` is a tier, not a posture.
- Use the most honest authority label that matches the artifact you actually read. Do not keep searching for a stronger label before you save.
- After `knowledge save`, report exactly what changed: topic path, source record, provenance note, and any queued rebuild scope.
- Follow `references/save-ingestion.md` for the full ingestion decision contract.

### `knowledge search`

- Search exact ids, current paths, page aliases, and literal page text.
- When the user asks what the company already knows, this is the default entrypoint.
- Keep search expectations literal. Rewrite the query around exact page text, paths, aliases, or headings instead of expecting semantic paraphrase rescue.
- Return zero results on a miss instead of a nearest-looking false positive.
- Prefer existing knowledge pages over raw source artifacts.
- Use the returned `trace_ref` as the handoff into `knowledge trace`.
- Read candidate pages directly and inspect provenance or raw sources only when needed.
- Do not return raw `sources/**` as ordinary search hits.

### `knowledge trace`

- Accepted refs are exact only: `knowledge_id`, `knowledge_id#section_id`, `current_path`, page alias, or `current_path#section_alias`.
- Section aliases accept deterministic normalization only. `current_understanding`, `current-understanding`, and `Current Understanding` resolve to the same stored alias key.
- Walk from the exact page or section ref to provenance notes, then to source records.
- Use `knowledge search` first when you need discovery. Then feed the returned `trace_ref` into `knowledge trace`.
- Page-level trace does not guess a best section. Read the returned `supported_sections` list and follow the exact section ref you need.
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
- Distinguish unread content from operator caveats. `ingests_with_reading_limits` is for missing or unread content; `ingests_with_confidence_caveats` is for confidence notes that do not imply unread content.
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

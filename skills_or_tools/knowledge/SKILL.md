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
- Treat helper approval as real policy, not a loose flag: the approval must identify the exact helper, point to the Decision Log entry, define scope, and define expiry/timebox.
- If the approval is a fallback/exception, it is invalid unless the plan/package also sets `fallback_policy: approved` and the Decision Log entry includes a timebox plus removal plan.
- Cite concrete paths, ids, or provenance notes in answers that depend on graph content.
- If support is weak or conflicting, say so explicitly instead of smoothing it over.
- Handle sensitive material by preserving pointer-level provenance and redacting secrets or prompt-bearing values.
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
- Inspect the local source files directly before making semantic decisions.
- Preserve the source first and record honest reading limits before filing knowledge.
- Extract durable knowledge units and map them to the smallest correct semantic topic set.
- Preserve source records and provenance notes for every material change. If multiple sources are ingested together, preserve per-source reading/provenance detail or an explicit bundle rationale.
- Apply bounded synchronous changes to the smallest affected page sections and queue wider reorganization for `rebuild` when needed.
- Follow `references/save-ingestion.md` for the full ingestion decision contract.

### `knowledge search`

- Search semantic pages and likely aliases first.
- Prefer existing knowledge pages and indexes over raw source artifacts.
- Read semantic pages directly and inspect provenance or raw sources only when needed.
- Apply authority as a ranking rule, not a decorative note.
- Do not return raw `sources/**` as ordinary search hits.

### `knowledge trace`

- Walk from the claim or locator to the relevant knowledge page, then to provenance notes, then to source records.
- Distinguish live doctrine, supported practice, historical support, and tentative inference.
- Surface conflicts, missing evidence, or authority collisions instead of choosing silently.

### `knowledge rebuild`

- Rebuild the smallest relevant scope first.
- Report what changed, what moved, and which conflicts or merge/split/rehome suggestions remain open.
- Do not use rebuild as a substitute for unresolved semantic judgment.

### `knowledge status`

- Report the specific subsystem or topic area under discussion, not a vague global reassurance.
- Highlight the most decision-relevant next action when status reveals drift or backlog.

## Reference map

- `references/save-ingestion.md`
- `references/search-and-trace.md`
- `references/storage-and-authority.md`
- `references/examples-and-validation.md`

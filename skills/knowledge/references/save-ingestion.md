# Save Ingestion

Use this contract when a local agent is saving source material into the semantic knowledge graph.

## Core rule

Artifacts go in, semantic knowledge plus provenance come out.

Every save must leave behind one durable artifact target.
- non-secret sources are copied into Fleki storage
- `secret_pointer_only` sources are preserved as pointer-backed artifacts
- callers do not choose the storage mode

The persistent thing we care about is the semantic graph, not the source-family filing system.

`knowledge save` applies immediately. There is no preview, validate-only, or dry-run save path in this workflow.

## Exact CLI shape

Use the native CLI with temp JSON inputs:

```bash
knowledge save --bindings /tmp/bindings.json --decision /tmp/decision.json --json
```

- `bindings.json` holds the source bindings for the local files you inspected.
- `decision.json` holds the ingestion decision: reading reports, topic actions, provenance notes, and next step.
- Build those JSON files in a temp directory from the real shell when needed so `local_path` still points at the real artifact. Do not add repo-tracked helper fixtures or harnesses for one-off saves.
- For concrete starting shapes, open:
  - `references/examples/minimal-save-bindings.json`
  - `references/examples/minimal-save-decision.json`

## Default save posture

If a source or artifact carries durable company evidence, save it by default.

A durable artifact is one another agent would reasonably want later without re-deriving it from scratch.
Common examples:
- internal reports
- truth packets
- action plans
- experiment recommendations
- runbooks
- durable findings captured in agent-authored artifacts

Do not wait for explicit user confirmation in ordinary internal work unless the material is clearly too sensitive, too ambiguous, or too ephemeral to file safely.

## Core workflow

1. Read the local source directly.
2. Distill the reusable takeaways before you think about storage mechanics.
3. Run `knowledge search` for the nearest existing topic and use `knowledge trace` if needed to decide whether to update or create.
4. Prefer updating the smallest existing semantic home over creating a new one-off chronology page.
5. A good semantic home is enough. If no clear existing page is obvious, create the clearest topic and save instead of leaving the artifact local while you keep searching.
6. If the current turn already produced the durable artifact it needs, save it before opening a discretionary refinement or code-change loop. Do not rewrite the generator or surrounding tooling unless the user explicitly asked for that.
7. Apply the save with explicit provenance and evidence.
8. Report exactly what changed: topic path, source record, provenance note, and any rebuild follow-up.

## Required input posture

- Inspect the provided local files directly.
- Use native multimodal capability for images and similar local artifacts.
- For PDFs, use direct inspection only when the active runtime surface exposes documented file input.
- Do not browse the internet.
- Do not invent helper scripts or harnesses.
- Each binding must declare `source_family`. Do not infer it from `source_kind` or file suffixes.
- Each binding must declare `timestamp` as ISO 8601 source-observed time.
- For a local artifact, use the real file mtime from the shell when that is the best source-observed time you have.
- If all you have is the source date, use that ISO 8601 date and note the date-only precision in `confidence_notes`.

## Required output shape

Return an ingestion decision that includes:

- `ingest_summary`
- `source_reading_reports`
- `topic_actions`
- `provenance_notes`
- `conflicts_or_questions`
- `asset_actions`
- `recommended_next_step`

## Temporal inputs

- `ingest_summary.authority_tier` accepts:
  - `live_doctrine`
  - `raw_runtime`
  - `historical_support`
  - `generated_mirror`
  - `mixed`

- `knowledge_units[].authority_posture` accepts:
  - `live_doctrine`
  - `supported_by_runtime`
  - `supported_by_internal_session`
  - `tentative`
  - `mixed`

- These are different enums.
  - `historical_support` is valid for `ingest_summary.authority_tier`.
  - `historical_support` is not valid for `knowledge_units[].authority_posture`.

- `knowledge_units[].kind` accepts:
  - `fact`
  - `principle`
  - `playbook`
  - `decision`
  - `pattern`
  - `regression`
  - `glossary`
  - `question`

- Each binding object must include `timestamp` as ISO 8601 source-observed time.
- Each knowledge unit may include `temporal_scope`:
  - `evergreen`
  - `time_bound`
  - `ephemeral`
- Each topic action in `knowledge save` may include `lifecycle_state`:
  - `current`
  - `historical`
- `stale` and delete are rebuild-only actions.

## Hard validation points

- Every source must have a reading report.
- Every non-trivial knowledge unit must have evidence.
- Use `fact` for plain observations unless a stronger semantic kind fits better.
- Prefer updating the nearest existing semantic topic when it is already a good fit.
- Use the most honest authority label that matches the artifact you actually read. Do not keep searching for a stronger label before you save.
- Do not invent `current` or a fake timestamp when a real local artifact time is available from the shell. If all you have is a source date, use that date and note the precision.
- Topic paths must be semantic, never source-family-first.
- Provenance notes must be one-per-source or explicitly bundled with rationale.
- After a successful save, report the exact topic path, source record, and provenance note.
- Helper approvals must be exact, explicit, and timeboxed.
- A fallback helper is invalid unless `fallback_policy: approved` is set in the plan/package and the Decision Log carries the removal plan.

## Mutation rule

Canonical graph state may only be mutated through the shared `knowledge` contract. Do not edit `knowledge/**` ad hoc if the repo-local core boundary is available.

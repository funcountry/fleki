# Save Ingestion

Use this contract when a local agent is saving source material into the semantic knowledge graph.

## Core rule

Artifacts go in, semantic knowledge plus provenance come out.

The persistent thing we care about is the semantic graph, not the source-family filing system.

## Required input posture

- Inspect the provided local files directly.
- Use native multimodal capability for images and similar local artifacts.
- For PDFs, use direct inspection only when the active runtime surface exposes documented file input.
- Do not browse the internet.
- Do not invent helper scripts or harnesses.

## Required output shape

Return an ingestion decision that includes:

- `ingest_summary`
- `source_reading_reports`
- `topic_actions`
- `provenance_notes`
- `conflicts_or_questions`
- `asset_actions`
- `recommended_next_step`

## Hard validation points

- Every source must have a reading report.
- Every non-trivial knowledge unit must have evidence.
- Topic paths must be semantic, never source-family-first.
- Provenance notes must be one-per-source or explicitly bundled with rationale.
- Helper approvals must be exact, explicit, and timeboxed.
- A fallback helper is invalid unless `fallback_policy: approved` is set in the plan/package and the Decision Log carries the removal plan.

## Mutation rule

Canonical graph state may only be mutated through the shared `knowledge` contract. Do not edit `knowledge/**` ad hoc if the repo-local core boundary is available.

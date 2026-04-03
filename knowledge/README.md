# Knowledge Tree

This directory is the canonical on-disk knowledge graph for Fleki.

- `topics/` holds the primary semantic pages.
- `provenance/` holds source-backed notes explaining what was learned.
- `sources/` preserves raw originals or durable pointers.
- `receipts/` records what `save`, `search`, `trace`, `rebuild`, and `status` did.

The default executor is a smart local agent using the shared `knowledge` contract, not a hidden service or deterministic helper stack.

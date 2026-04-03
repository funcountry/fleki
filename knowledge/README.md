# Knowledge Tree

This checked-in directory is reference content and a migration seed for Fleki.

The live graph root is `resolved_data_root`, usually `~/.fleki/knowledge`.

- `topics/` holds the primary semantic pages.
- `provenance/` holds source-backed notes explaining what was learned.
- `sources/` preserves raw originals or durable pointers.
- `assets/` holds derived-only render artifacts or extracted files.
- `receipts/` records what `save`, `search`, `trace`, `rebuild`, and `status` did.
- `search/` is optional support state only.

The default executor is a smart local agent using the shared `knowledge` contract, not a hidden service or deterministic helper stack.

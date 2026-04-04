# Storage And Authority

## Storage layers

- `<resolved_data_root>/topics/**`
  - primary semantic pages
- `<resolved_data_root>/provenance/**`
  - source-backed explanation of what each source contributed
- `<resolved_data_root>/sources/**`
  - copied originals for non-secret sources or pointer-backed artifacts for `secret_pointer_only`
- `<resolved_data_root>/assets/**`
  - derived render artifacts or extracted files
- `<resolved_data_root>/receipts/**`
  - append-only command evidence
- `<resolved_data_root>/search/**`
  - optional support state only; not required for correctness

The checked-in repo `knowledge/**` tree is reference content and a migration seed. It is not the live graph root.

## Identity rules

- `knowledge_id` is the durable page identity.
- `section_id` is the durable section identity.
- `source_id` is the immutable source identity.
- paths are mutable aliases, not the durable identity layer.
- `knowledge_id#section_id` is the stable machine ref for trace.
- `current_path#section_alias` is convenience only.
- section-alias input accepts deterministic normalization like underscores, hyphens, or heading text, but nothing broader.

## Authority rules

- live doctrine outranks weaker conflicting support
- raw runtime truth outranks mirrors when the question is what actually happened
- historical support and sessions can justify pages, but they do not automatically become doctrine
- freshness and authority are separate axes
- newer weak support does not outrank stronger doctrine just because it is recent
- stale or superseded lifecycle state can demote a page without changing its authority posture

## Source family

- `source_family` is an explicit binding and manifest field.
- `source_family` owns source storage placement, provenance-family rollup, and read-side classification.
- Do not infer `source_family` from `source_kind` or file suffixes.
- `source_observed_at` comes from the required binding `timestamp`. The app does not infer it from document body text.
- Fleki owns source storage policy:
  - non-secret sources are copied
  - `secret_pointer_only` sources are preserved as pointer-backed artifacts
  - callers do not choose copy vs pointer mode

## Helper policy

- no helpers by default
- helpers must be explicitly approved by Amir
- fallback helpers additionally require `fallback_policy: approved` and a Decision Log removal plan

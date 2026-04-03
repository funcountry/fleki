# Storage And Authority

## Storage layers

- `knowledge/topics/**`
  - primary semantic pages
- `knowledge/provenance/**`
  - source-backed explanation of what each source contributed
- `knowledge/sources/**`
  - raw originals or durable pointers
- `knowledge/receipts/**`
  - append-only command evidence

## Identity rules

- `knowledge_id` is the durable page identity.
- `section_id` is the durable section identity.
- `source_id` is the immutable source identity.
- paths are mutable aliases, not the durable identity layer.

## Authority rules

- live doctrine outranks weaker conflicting support
- raw runtime truth outranks mirrors when the question is what actually happened
- historical support and sessions can justify pages, but they do not automatically become doctrine

## Helper policy

- no helpers by default
- helpers must be explicitly approved by Amir
- fallback helpers additionally require `fallback_policy: approved` and a Decision Log removal plan

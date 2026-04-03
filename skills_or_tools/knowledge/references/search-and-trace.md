# Search And Trace

## `knowledge search`

- Search semantic pages first.
- Prefer topic/playbook/decision/glossary pages over raw sources.
- Rank live doctrine ahead of weaker conflicting material.
- Return concrete page paths, ids, supporting provenance, and the minimum authority note needed for honest use.

## `knowledge trace`

- Accept a `knowledge_id`, `knowledge_id#section_id`, current path alias, or best-effort claim text lookup.
- Walk from page to provenance to source records.
- Keep precedence visible:
  - live doctrine
  - raw runtime truth
  - generated mirror or receipt
  - historical support
  - derived page

## `knowledge status`

- Surface rebuild-pending scopes, reading-limit gaps, recent receipts, and unresolved contradictions.
- Do not rely on hidden control-plane state to answer health questions.

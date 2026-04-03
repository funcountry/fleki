# Search And Trace

## `knowledge search`

- Search semantic pages first.
- Prefer topic/playbook/decision/glossary pages over raw sources.
- Rank live doctrine ahead of weaker conflicting material.
- Use freshness as a secondary ranking hint after topical match and authority.
- Demote explicit `stale` pages and derived `superseded` pages before ordinary tie-breaking.
- Return concrete page paths, ids, supporting provenance, and the minimum authority note needed for honest use.

## `knowledge trace`

- Accept a `knowledge_id`, `knowledge_id#section_id`, current path alias, or best-effort claim text lookup.
- Walk from page to provenance to source records.
- Surface source-observed time, capture time, and lifecycle state when they explain why a result ranked where it did.
- For legacy PDF source records, surface `render_contract_gaps` instead of pretending there is a clean render or omission chain.
- Keep precedence visible:
  - live doctrine
  - raw runtime truth
  - generated mirror or receipt
  - historical support
  - derived page

## `knowledge status`

- Surface the active `resolved_data_root`, `install_manifest_path`, rebuild-pending scopes, reading-limit gaps, recent receipts, and unresolved contradictions.
- Surface `pdf_render_contract_gap_count` when older PDF records still need repair.
- Prefer `recent_topics` and `recent_source_ingests` over hot-topic frequency when answering what changed recently.
- Do not rely on hidden control-plane state to answer health questions.

# Search And Trace

## `knowledge search`

- Search semantic pages first.
- Return zero results on a miss instead of a nearest-looking false positive.
- Prefer topic/playbook/decision/glossary pages over raw sources.
- Rank live doctrine ahead of weaker conflicting material.
- Use freshness as a secondary ranking hint after topical match and authority.
- Demote explicit `stale` pages and derived `superseded` pages before ordinary tie-breaking.
- Return concrete page paths, ids, supporting provenance, and the minimum authority note needed for honest use.

## `knowledge trace`

- Accept a `knowledge_id`, `knowledge_id#section_id`, current path alias, or best-effort claim text lookup.
- Walk from page to provenance to source records.
- Best-effort claim text should narrow to the best matching section and the most relevant supporting provenance when the graph contains enough evidence to do that honestly.
- If best-effort claim text cannot narrow to a section and evidence, return no match instead of a page-level guess.
- Surface the matched heading, matched snippet, and evidence locator when trace succeeds.
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
- Surface `missing_lifecycle_state_count` when older pages still lack lifecycle metadata.
- Prefer `recent_topics` and `recent_source_ingests` over hot-topic frequency when answering what changed recently.
- Do not rely on hidden control-plane state to answer health questions.

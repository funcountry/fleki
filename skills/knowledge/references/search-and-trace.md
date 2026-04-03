# Search And Trace

## `knowledge search`

- Search exact ids, current paths, page aliases, and literal page text.
- Return zero results on a miss instead of a nearest-looking false positive.
- Return candidate rows with concrete page paths, ids, `match_kind`, `trace_ref`, and supporting provenance.
- Use the returned `trace_ref` as the normal handoff into `knowledge trace`.
- Do not interpret `search` as proof. The agent still reads the candidate pages and evidence.

## `knowledge trace`

- Accept exact refs only:
  - `knowledge_id`
  - `knowledge_id#section_id`
  - `current_path`
  - page alias
  - `current_path#section_alias`
- Walk from exact page or section ref to provenance to source records.
- If a ref does not resolve exactly, return no match instead of guessing.
- Surface the matched heading, matched snippet, and evidence locator when trace succeeds.
- Surface source-observed time, capture time, and lifecycle state when they help the agent judge the evidence.
- For legacy PDF source records, surface `render_contract_gaps` instead of pretending there is a clean render or omission chain.
- `knowledge_id#section_id` is the stable machine ref.
- `current_path#section_alias` is convenience only and may change when headings change.

## `knowledge status`

- Surface the active `resolved_data_root`, `install_manifest_path`, rebuild-pending scopes, reading-limit gaps, recent receipts, and unresolved contradictions.
- Surface `pdf_render_contract_gap_count` when older PDF records still need repair.
- Surface `missing_lifecycle_state_count` when older pages still lack lifecycle metadata.
- Prefer `recent_topics` and `recent_source_ingests` over hot-topic frequency when answering what changed recently.
- Do not rely on hidden control-plane state to answer health questions.

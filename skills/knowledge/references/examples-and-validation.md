# Examples And Validation

## Good examples

- Save a Codex session into `doctrine/shared-agent-learnings` and `operations/releases/post-release-followup-runbooks`.
- Search for Slack-first lesson authoring, return the candidate rows, and follow the returned `trace_ref`.
- Trace a runtime recovery ref back to the exact knowledge page, provenance note, and source record.

## Anti-example

- Create `topics/codex/2026-02-27-common-place-for-agents.md` and dump raw chronology into it.

## Validation matrix

- valid `knowledge_unit.kind` only: `fact`, `principle`, `playbook`, `decision`, `pattern`, `regression`, `glossary`, `question`
- valid `ingest_summary.authority_tier` only: `live_doctrine`, `raw_runtime`, `historical_support`, `generated_mirror`, `mixed`
- valid `knowledge_units[].authority_posture` only: `live_doctrine`, `supported_by_runtime`, `supported_by_internal_session`, `tentative`, `mixed`
- do not swap `authority_tier` and `authority_posture`
- semantic path, not source-family path
- evidence on every knowledge unit
- valid `temporal_scope` only: `evergreen`, `time_bound`, `ephemeral`
- valid save-time `lifecycle_state` only: `current`, `historical`
- provenance coverage for every source
- honest reading limits
- exact helper approval or no helper use
- authority notes when they change confidence or interpretation

# Worklog

Plan doc: /Users/agents/workspace/fleki/docs/UNIVERSAL_ARTIFACT_PRESERVATION_AND_WIKI_EXPOSURE_2026-04-03.md

## Initial entry
- Run started.
- Current phase: Phase 1 — Delete caller-owned preservation mode.
- Warn-first note: the planning-pass block still says `external_research_grounding: not started`, but the plan is concrete enough to execute from repo evidence.

## Phase 1 (Delete caller-owned preservation mode) Progress Update
- Work completed:
  - Removed `preserve_mode` from `SourceBinding`, CLI parsing, and repository storage-policy logic.
  - Added a fail-loud CLI error for legacy `preserve_mode` bindings.
  - Updated the owning skill and storage docs to the one-rule preservation story.
  - Regenerated `skills/knowledge/runtime/**`.
- Tests run + results:
  - `.venv/bin/python scripts/sync_knowledge_runtime.py` — passed
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_cli tests.test_contracts tests.test_source_families tests.test_skill_package -v` — 31 tests passed
- Issues / deviations:
  - none
- Next steps:
  - Add the normalized manifest-backed `artifacts_by_source` summary to repository reads and `trace()`.

## Phase 2 (Normalize the artifact chain in repository reads) Progress Update
- Work completed:
  - Added the repository-owned manifest-to-artifact summary helper.
  - Extended `trace()` with `artifacts_by_source` while preserving the existing evidence fields.
  - Added assertions for copied files, copied PDFs, and `secret_pointer_only` artifact summaries.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_save tests.test_search_trace_status tests.test_source_families -v` — 19 tests passed
- Issues / deviations:
  - none
- Next steps:
  - Add the minimal review-wiki exporter package and repair the older review-wiki plan so it matches the artifact-visible browse rule.

## Phase 3 (Export artifact-visible wiki pages) Progress Update
- Work completed:
  - Added `src/knowledge_graph/review_wiki/exporter.py` and the package entrypoint.
  - Added `tests/test_review_wiki_exporter.py` for topic pages, provenance pages, artifact detail pages, and selective file export.
  - Repaired the older review-wiki daemon plan so it matches the shipped artifact-visible browse rule.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_save tests.test_search_trace_status tests.test_source_families tests.test_review_wiki_exporter -v` — 20 tests passed
- Issues / deviations:
  - none
- Next steps:
  - Run the full repo verification and complete the phase.

## Final verification
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — 65 tests passed
  - `.venv/bin/python -m compileall src` — passed
- Remaining gap:
  - none inside repo verification; this plan did not add daemon or install-path code

## Audit follow-through
- Work completed:
  - Updated `scripts/sync_knowledge_runtime.py` so the generated skill bundle stays focused on graph runtime files and does not absorb `review_wiki`.
  - Regenerated `skills/knowledge/runtime/**` so the runtime repository now exposes `artifacts_by_source` and `_artifact_summary_from_manifest()`.
  - Added a package assertion that the runtime bundle includes the artifact trace shape and excludes the `review_wiki` package.
  - Closed the reopened implementation-audit gap and returned Phase 2 to `COMPLETE`.
- Tests run + results:
  - `.venv/bin/python scripts/sync_knowledge_runtime.py` — passed
  - `.venv/bin/python -m py_compile scripts/sync_knowledge_runtime.py` — passed
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_skill_package -v` — 1 test passed
- Issues / deviations:
  - The first package test attempt raced the runtime sync because they were launched in parallel. Re-running the test after sync passed cleanly.
- Next steps:
  - Run the full repo suite and `compileall` one more time with the updated runtime bundle in place.

## Final verification after audit follow-through
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — 65 tests passed
  - `.venv/bin/python -m compileall src` — passed
- Remaining gap:
  - none inside repo verification; manual browser checks remain non-blocking

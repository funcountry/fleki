# Worklog

Plan doc: /Users/agents/workspace/fleki/docs/ELIMINATE_HEURISTIC_RETRIEVAL_AND_SCRIPTED_GUESSWORK_2026-04-03.md

## Initial entry
- Run started.
- Current phase: Phase 1 - Lock doctrine, live-root truth, and public contract.

## Phase 1 (Lock doctrine, live-root truth, and public contract) Progress Update
- Work completed:
  - Updated the repo doctrine and public docs so they all teach live-root truth, exact `search` -> `trace_ref` -> `trace` flow, and no heuristic retrieval.
  - Updated checked-in family READMEs so they identify themselves as reference content instead of live mutable graph state.
- Tests run + results:
  - `rg -n "best-effort|nearest-looking|rank live doctrine|freshness sharpens ranking|best-supported|claim text|retrieval surface|infer .*source_family|fuzzy|vector|best match" README.md AGENTS.md skills/knowledge knowledge` — no remaining fuzzy or ranking promises beyond intentional anti-pattern bans and neutral no-false-positive wording.
- Issues / deviations:
  - `save-ingestion.md` now mentions explicit `source_family` ahead of the code change because the final contract is already locked in the implementation plan. Phase 3 will make the code match it.
- Next steps:
  - Replace the read-path heuristics in `repository.py`, `cli.py`, and `text.py`.

## Phase 2 (Cut search and trace to exact navigation) Progress Update
- Work completed:
  - Replaced heuristic search/trace code with exact ref resolution plus deterministic literal candidate discovery, including explicit `match_kind` output and hard failure for unknown fragments.
  - Removed tokenization and score-based helper logic from the read path, updated the CLI contract, and rewrote the affected regression tests to prove the exact-only behavior.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_search_trace_status tests.test_cli -v` — passed (`Ran 24 tests in 9.580s`, `OK`).
- Issues / deviations:
  - While tightening the CLI tests, one PDF render assertion block had drifted into the new search JSON test. I moved it back under the save-command test before rerunning the suite.
- Next steps:
  - Make `source_family` explicit in the save/manifest contract and remove the remaining family-routing inference paths.

## Phase 3 (Make `source_family` explicit and repair legacy manifests) Progress Update
- Work completed:
  - Added explicit `source_family` to the authored binding contract, save-path validation, CLI binding parsing, and the checked-in minimal save example.
  - Removed runtime family inference from the repository, made manifest reads fail loudly when `source_family` is missing, added `scripts/backfill_source_family.py` as the one sanctioned repair path, and updated the PDF render backfill script to surface missing-family errors cleanly.
  - Rewrote the schema-focused tests so they prove authored family routing, clean CLI failure for missing `source_family`, and explicit repair before runtime reads resume.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_source_families tests.test_save tests.test_contracts tests.test_backfill_pdf_render_contract tests.test_cli -v` — passed (`Ran 31 tests in 14.725s`, `OK`).
- Issues / deviations:
  - None beyond the planned contract break; old manifests now require the named repair script instead of silent runtime inference.
- Next steps:
  - Regenerate the runtime mirror, refresh bundled/runtime docs, run parity plus install-surface checks, and finish the full touched-surface verification suite.

## Phase 4 (Regenerate runtime, refresh reference artifacts, and prove the install surface) Progress Update
- Work completed:
  - Updated the runtime README generator to teach exact search/trace plus explicit `source_family`, regenerated `skills/knowledge/runtime/**`, and added package-level assertions for the new repair script and bundled contract language.
  - Labeled checked-in receipt exemplars as historical reference content and corrected the one remaining rebuild test so it verifies exact alias lookup after rehome instead of fuzzy natural-language search.
- Tests run + results:
  - `.venv/bin/python scripts/sync_knowledge_runtime.py` — passed (`synchronized runtime: /Users/agents/workspace/fleki/skills/knowledge/runtime`).
  - `diff -rq src/knowledge_graph skills/knowledge/runtime/src/knowledge_graph` — passed (no diff).
  - `./install.sh --dry-run` — passed; detected and selected real Codex, Hermes, and OpenClaw knowledge skill targets.
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_skill_package tests.test_install_targets tests.test_runtime_manifests tests.test_layout -v` — passed (`Ran 12 tests in 0.046s`, `OK`).
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_rebuild -v` — passed after the exact-alias test correction (`Ran 2 tests`, `OK`).
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed (`Ran 58 tests in 15.602s`, `OK`).
  - `.venv/bin/python -m compileall src` — passed.
- Issues / deviations:
  - The first full-suite run exposed one stale rebuild assertion that still depended on fuzzy search wording. I changed it to exact old-path alias lookup, which matches the new contract and keeps the rehome behavior covered.
- Next steps:
  - Implementation complete for this plan slice. No open runtime or contract blockers remain from this pass.

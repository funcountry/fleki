# Worklog

Plan doc: /tmp/fleki-review-wiki/docs/INTERNAL_KNOWLEDGE_REVIEW_WIKI_DAEMON_PLAN_2026-04-03.md

## Initial entry
- Run started.
- Current phase: Phase 1 — Hard-cut page format and port the existing KB.
- Branch: `feature/review-wiki-daemon`.

## Phase 1 (Hard-cut page format and port the existing KB) Progress Update
- Work completed:
  - Switched the canonical frontmatter codec to YAML while preserving timestamp strings.
  - Added a one-time JSON migration reader and in-place port step for existing graphs.
  - Ported the checked-in KB markdown pages to YAML and refreshed the generated runtime bundle.
- Tests run + results:
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest tests.test_frontmatter tests.test_layout tests.test_save tests.test_rebuild tests.test_search_trace_status tests.test_cli -v` — passed
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest tests.test_skill_package -v` — passed
- Issues / deviations:
  - None.
- Next steps:
  - Build the filtered review-wiki exporter, digest gate, and Quartz overlay.

## Phase 2 (Build the filtered export and digest gate) Progress Update
- Work completed:
  - Added the `knowledge_graph.review_wiki` exporter, digest, and derived-state layout helpers.
  - Added the repo-owned Quartz overlay in `templates/review-wiki/`.
  - Updated runtime sync so the bundled agent runtime excludes review-wiki code.
- Tests run + results:
  - `/Users/agents/workspace/fleki/.venv/bin/python scripts/sync_knowledge_runtime.py` — synchronized runtime bundle
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest tests.test_review_wiki_exporter tests.test_review_wiki_digest tests.test_skill_package -v` — passed
- Issues / deviations:
  - None.
- Next steps:
  - Add the daemon loop, native service-file rendering, and installer integration.

## Phase 3 (Add the local daemon and native install path) Progress Update
- Work completed:
  - Added the foreground daemon, Quartz build staging, and atomic public-site replacement flow.
  - Added launchd and systemd user-service renderers.
  - Extended the repo installer with `--review-wiki` and `--remove-review-wiki`, plus Node/npm preflight and overlay materialization.
  - Updated the repo README with the optional local review-wiki install and removal commands.
- Tests run + results:
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest tests.test_review_wiki_service tests.test_review_wiki_install tests.test_review_wiki_daemon tests.test_skill_package -v` — passed
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed
  - `/Users/agents/workspace/fleki/.venv/bin/python -m compileall src` — passed
- Issues / deviations:
  - I did not run the manual macOS and Linux service smoke outside the test suite.
- Next steps:
  - Run `./install.sh --review-wiki` on a macOS host and a Linux host for the final manual service smoke.

## Audit remediation (Phase 1 follow-up) Progress Update
- Work completed:
  - Removed the always-on `port_graph_frontmatter(self.knowledge_root)` call from normal repository startup.
  - Tightened graph markdown loads so invalid topic, provenance, and receipt frontmatter now fails loudly instead of being silently skipped.
  - Added layout coverage that proves normal repository reads reject legacy JSON frontmatter while explicit legacy migration still ports it.
  - Refreshed the generated runtime bundle after the source fix.
- Tests run + results:
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest tests.test_frontmatter tests.test_layout tests.test_search_trace_status tests.test_review_wiki_exporter tests.test_review_wiki_daemon -v` — passed
  - `/Users/agents/workspace/fleki/.venv/bin/python scripts/sync_knowledge_runtime.py` — synchronized runtime bundle
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed
  - `/Users/agents/workspace/fleki/.venv/bin/python -m compileall src` — passed
  - `/Users/agents/workspace/fleki/.venv/bin/python -m py_compile scripts/install_knowledge_skill.py scripts/sync_knowledge_runtime.py` — passed
- Issues / deviations:
  - I still did not run the manual macOS and Linux service smoke outside the test suite.
- Next steps:
  - Run `./install.sh --review-wiki` on a macOS host and a Linux host for the final manual service smoke if machine-level verification is needed.

## Machine smoke (Phase 3 manual verification) Progress Update
- Work completed:
  - Ran the real macOS install with `./install.sh --review-wiki` and verified the launch agent, generated Quartz workspace, and built public tree under `~/.fleki/state/review-wiki/`.
  - Found and fixed a hanging Quartz git dependency install by switching the pin to a direct GitHub tarball.
  - Found and fixed missing Quartz workspace scaffold files by copying the installed `quartz/` tree into the derived workspace and aligning the local config imports.
  - Found and fixed launch-time failure against the live graph by adding an explicit installer port step for legacy JSON frontmatter before daemon startup.
  - Found and fixed a host-specific Python 3.12 serving failure by replacing the daemon's `http.server` path with a Fleki-owned raw-socket static server.
  - Verified the running daemon manually:
    - launchd service `dev.fleki.review-wiki` is running
    - `http://127.0.0.1:4151` returns `200 OK`
    - `http://127.0.0.1:4151/topics/knowledge-system/smoke-meta-optimization-pdf.html` returns `200 OK`
    - a temporary one-line edit to `~/.fleki/knowledge/topics/knowledge-system/smoke-meta-optimization-pdf.md` appeared on the served page after the poll interval
    - restoring the original file removed the line from the served page after the next poll interval
- Tests run + results:
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest tests.test_review_wiki_install tests.test_review_wiki_service tests.test_review_wiki_daemon -v` — passed
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest tests.test_review_wiki_daemon tests.test_review_wiki_install tests.test_review_wiki_service -v` — passed
  - `PYTHONPATH=src:tests /Users/agents/workspace/fleki/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed
  - `/Users/agents/workspace/fleki/.venv/bin/python -m compileall src` — passed
  - `/Users/agents/workspace/fleki/.venv/bin/python -m py_compile scripts/install_knowledge_skill.py scripts/sync_knowledge_runtime.py` — passed
- Issues / deviations:
  - Linux machine smoke is still pending.
- Next steps:
  - Run `./install.sh --review-wiki` on a Linux host and repeat the same install, serve, and auto-regeneration smoke there.

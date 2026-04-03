# Worklog

Plan doc: /Users/agents/workspace/fleki/docs/CENTRALIZED_KNOWLEDGE_INSTALL_AND_ROOT_PLAN_2026-04-03.md

## Initial entry
- Run started.
- Current phase: Phase 1 - Resolve layout, status, and migration contract in the core storage layer

## Phase 1-2 Progress Update
- Work completed:
  - Added the explicit layout/install-manifest boundary in `src/knowledge_graph/layout.py` plus typed install/runtime manifest models.
  - Refactored `KnowledgeRepository` to operate on explicit `data_root` semantics and surface install/root agreement through `status`.
  - Added deterministic export from `skills_or_tools/knowledge/**` into `skills/knowledge/**` and the repo-local worktree overlay, plus package-local install assets under `skills_or_tools/knowledge/install/**`.
  - Strengthened bundle tests so source, shipped, and overlay package trees must match exactly.
- Tests run + results:
  - `/tmp/fleki-knowledge-venv.4Cza1p/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed, 15 tests.
- Issues / deviations:
  - The host system Python did not have the declared `docling` dependency installed, so verification moved into an isolated Python 3.12 virtualenv aligned with `pyproject.toml`.
- Next steps:
  - Run the real shared-surface install/publish flow, then cut the host over to the canonical app-data root.

## Phase 3 Progress Update
- Work completed:
  - Installed `knowledge` into `~/.agents/skills/knowledge` through the upstream `npx skills add` seam and created the Codex compatibility link at `~/.codex/skills/knowledge`.
  - Wrote `~/Library/Application Support/Fleki/install.json` with the resolved data/config/state roots and install metadata.
  - Briefly tested a sibling-repo publication path, then reverted it after the ownership boundary was clarified. See `Plan Repair Update`.
- Tests run + results:
  - `bash skills_or_tools/knowledge/install/codex/install.sh` — passed; install manifest written and Codex compatibility path linked.
- Issues / deviations:
  - The first pass overreached by treating sibling repos as Fleki publication targets. That assumption was corrected and the external writes were reverted.
- Next steps:
  - Migrate the repo-local graph into the canonical app-data root and verify search/trace/status from the cutover layout.

## Phase 4-5 Progress Update
- Work completed:
  - Migrated the repo-local `knowledge/**` tree into `~/Library/Application Support/Fleki/knowledge`.
  - Added migration-time normalization so managed metadata and managed markdown bodies rewrite legacy `knowledge/...` embedded paths to graph-relative paths while leaving raw source payloads untouched.
  - Verified post-cutover `status`, `search`, and `trace` from the canonical data root with runtime-agreement metadata for Codex, Hermes, and Paperclip manifests.
  - Added supersession notes to the older cross-agent architecture doc and worklog so they no longer imply repo-local install/root truth.
- Tests run + results:
  - `PYTHONPATH=src python3.12 - <<'PY' ... migrate_legacy_repo_graph(...) ... PY` — passed; 33 files copied, verified, and switched.
  - `PYTHONPATH=src python3.12 - <<'PY' ... repo.status(...) ... PY` — passed; resolved root `/Users/agents/Library/Application Support/Fleki/knowledge`, install manifest present, runtime agreement matched for Codex/Hermes/Paperclip manifests.
  - `PYTHONPATH=src python3.12 - <<'PY' ... repo.search('semantic organization') ... repo.trace(...) ... PY` — passed; graph-relative topic/provenance/source-record paths returned from the canonical data root.
  - `rg -n 'knowledge/' "$HOME/Library/Application Support/Fleki/knowledge"` — clean after migration-path normalization.
  - `/tmp/fleki-knowledge-venv.4Cza1p/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed, 15 tests.
  - `/tmp/fleki-knowledge-venv.4Cza1p/bin/python -m compileall src` — passed.
- Issues / deviations:
  - Cleanup is intentionally incomplete: the legacy repo-local `knowledge/**` tree still exists, and the final collapse from `skills_or_tools/knowledge/**` to `skills/knowledge/**` remains deferred pending Fleki-owned cleanup choices.
- Next steps:
  - Finish the Fleki-owned support matrix and cleanup work before deleting repo-local compatibility surfaces.

## Plan Repair Update
- Work completed:
  - Reverted the sibling-repo `knowledge/` package directories that had been written during an overreaching implementation pass in `../skills`, `../agents`, and `../paperclip_agents`.
  - Reopened the architecture plan and rewrote the North Star plus phase plan so Fleki stops at repo-local package/install outputs and downstream adoption contracts.
- Tests run + results:
  - `git -C /Users/agents/workspace/skills status --short` — clean with respect to the reverted `skills/knowledge/` publication.
  - `git -C /Users/agents/workspace/agents status --short` — clean with respect to the reverted `agents/_shared/skills/knowledge/` publication.
  - `git -C /Users/agents/workspace/paperclip_agents status --short` — clean with respect to the reverted `skills/knowledge/` publication.
- Issues / deviations:
  - The earlier assumption that Fleki should publish into sibling repos was wrong. That assumption is now explicitly forbidden by the plan.
- Next steps:
  - Continue from the repaired phase plan, with downstream Hermes/Paperclip adoption treated as follow-through in their owning surfaces rather than as Fleki-owned publication work.

## Phase 5 Cleanup Progress Update
- Work completed:
  - Removed sibling-repo export targets from `scripts/export_knowledge_skill_bundle.py` and deleted the Hermes/Paperclip publish wrappers from the source skill bundle.
  - Reworked `runtime_manifests.py` so the Paperclip manifest exposes only the shared installed bundle and downstream-owned adoption notes, not a Paperclip repo path or workspace overlay path.
  - Rewrote `AGENTS.md`, `skills_or_tools/knowledge/SKILL.md`, and `skills_or_tools/knowledge/install/README.md` so Fleki no longer tells operators to publish into Hermes or Paperclip from this repo.
  - Refreshed `skills/knowledge/**` and `.agents/skills/knowledge/**` from source so the generated bundles match the cleaned install contract.
- Tests run + results:
  - `.venv/bin/python scripts/export_knowledge_skill_bundle.py --targets shipped dev_overlay` — passed; generated bundles refreshed.
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_runtime_manifests tests.test_skill_package -v` — passed.
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed, 15 tests.
  - `.venv/bin/python -m compileall src` — passed.
- Issues / deviations:
  - This update was later superseded by the reusable install-target framework. External runtime changes are not valid blockers for Fleki cleanup anymore.
- Next steps:
  - Superseded. See the reusable framework update below.

## Constraint Repair Update
- Work completed:
  - Verified that I did not edit Hermes or Paperclip config or adapter files. `git diff` was empty for the checked Hermes config/runbook files and the checked Paperclip adapter/company-skill files.
  - Repaired the active architecture plan so Hermes and Paperclip configs and repos are treated as off limits and read-only for this effort.
- Tests run + results:
  - `git -C /Users/agents/workspace/agents diff -- deploy/hermes/profiles/agent_boss/config.yaml deploy/mac/host_runner/runbook.md /Users/agents/workspace/agents/README.md` — no diff
  - `git -C /Users/agents/workspace/paperclip_agents diff -- vendor/paperclip/packages/adapters/codex-local/src/server/skills.ts vendor/paperclip/packages/adapters/codex-local/src/server/execute.ts vendor/paperclip/server/src/services/company-skills.ts skills/README.md docs/bugs/2026-03-31-worktree-agents-skill-injection.md` — no diff
- Issues / deviations:
  - The earlier audit language was wrong because it treated external Hermes and Paperclip changes as valid next steps. That assumption is now explicitly forbidden by the plan.
- Next steps:
  - Decide whether Fleki can support the current fixed Hermes and Paperclip behaviors without touching those systems, or explicitly de-scope them from this plan.

## Reusable Framework Implementation + Audit Update
- Work completed:
  - Added a Fleki-owned install-target layer in `src/knowledge_graph/install_targets.py`.
  - Reworked manifests and install metadata around:
    - one managed install root
    - optional operator-provided external discovery roots
    - optional compatibility skill paths
    - one generated worktree overlay path
    - stable Paperclip key `fleki/knowledge`
  - Updated `skills_or_tools/knowledge/SKILL.md`, `skills_or_tools/knowledge/install/README.md`, and `AGENTS.md` so they describe a reusable repo framework instead of repo-specific Hermes/Paperclip assumptions.
  - Added tests for install-target parsing/materialization and updated manifest tests to enforce the new generic contract.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_install_targets tests.test_layout tests.test_runtime_manifests tests.test_skill_package -v` — passed, 6 tests.
  - `HOME=<temp> CODEX_HOME=<temp> KNOWLEDGE_EXTERNAL_DISCOVERY_ROOTS=<temp list> KNOWLEDGE_COMPATIBILITY_SKILL_PATHS=<temp list> bash skills_or_tools/knowledge/install/codex/install.sh` — passed in a temporary home; managed install, external discovery links, compatibility links, and `install.json` all matched expectations without touching the live machine install.
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed, 17 tests.
  - `.venv/bin/python -m compileall src` — passed.
- Issues / deviations:
  - The current repo-owned Hermes path on this machine is still handoff-only because Fleki will not write into that external repo in this effort.
  - Paperclip workspace injection remains runtime-owned and non-canonical. Fleki only ships a compatible bundle plus stable key.
- Next steps:
  - Run the full repo test suite and compile checks.
  - Finish the remaining Fleki-owned cleanup around the legacy repo-local graph and export-first package split.

# Fleki Agent Guide

## Verify First
- Use `.venv/bin/python`. This repo requires Python 3.12; do not rely on the host `python3`.
- Full verification for changes under `src/knowledge_graph/**`, `tests/**`, or install/publish code:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
  - `.venv/bin/python -m compileall src`
- Targeted test loop:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_<module> -v`

## Definition Of Done
- Run the smallest relevant check while iterating.
- Run the full suite before claiming repo code changes are complete.
- Update tests and the owning docs in the same change when behavior, contracts, or install/publish steps change.
- Final replies must say what changed, what ran, and any remaining gap in plain English.

## Communication
- Write for a human reader first in replies, docs, and instruction files.
- Lead with the concrete answer in 1-3 sentences before architecture, history, or caveats.
- If the answer is a path, command, flag, or runtime fact, name that exact thing first.
- Use plain English. Avoid house jargon, compressed labels, and pseudo-technical shorthand.
- Say simple things simply. Example: `Only AGENTS.md changed, so I didn't run tests.`
- Keep instructions direct. Do not add planning notes, authoring commentary, or meta explanation about how the file was produced.
- Prefer short subject-verb-object sentences. Example: `I installed it.` `I didn't uninstall it.` `I updated the doc.` `I did not change the code.`
- When describing changes, name the concrete thing and action. Do not hide the answer behind words like `roll back`, `cutover`, `follow-through`, `prior state`, `boundary`, `surface`, or `contract` when plain words would do.
- Do not answer in workflow jargon. Avoid reply-first phrases like `arch-step`, `North Star`, `phase plan`, or `review-gate` unless the user explicitly wants that workflow language. Even then, state the plain-English answer first.
- Do not use shorthand like `host-local` without translating it immediately. Say `installed on this machine`, `saved in this repo`, or `published to the other repo` instead.

## Blocked State
- If the required interpreter, dependency, or command is missing, stop and report the exact missing piece.
- If a change appears to require compatibility support, migration shims, or a second live path, get explicit approval and name the real consumer before adding it.
- If a file looks generated or mirrored, find the owning source before editing it.

## Source Of Truth
- `src/knowledge_graph/**` owns the repo's Python implementation.
- `tests/**` owns automated coverage.
- `docs/**` holds supporting reference. If a doc conflicts with code or current instructions, follow the live owner.
- `skills/knowledge/**` is the human-edited source for the knowledge skill.
- `skills/knowledge/runtime/**` is generated. Refresh it with:
  - `.venv/bin/python scripts/sync_knowledge_runtime.py`
- Use the repository contract or the `knowledge` skill for work on `knowledge/**`; do not hand-edit graph outputs unless the task is explicitly about those generated artifacts.
- Keep one owner per rule, workflow, or implementation. Do not leave competing copies in old docs, duplicate files, or parallel paths.

## Red Lines
- Git is the history. Do not keep dead code, duplicate docs, compatibility shims, deprecated branches, legacy counters, or "for posterity" paths unless the user explicitly asks for them.
- When a path is replaced, delete or rewrite the old path in the same change.
- Do not keep both old and new implementations "just in case."
- Do not hand-edit generated mirrors when the change belongs in the source path.

## Install
- Repo installer:
  - `./install.sh`
- Dry run:
  - `./install.sh --dry-run`
- Canonical bundle repair:
  - `bash skills/knowledge/install/bootstrap.sh`
- Keep the stable skill key `fleki/knowledge`.

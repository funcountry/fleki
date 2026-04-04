---
title: "Fleki - Skill-First Shared Graph Mutation Locking - Architecture Plan"
date: 2026-04-03
status: active
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: architectural_change
related:
  - /Users/agents/workspace/fleki/README.md
  - /Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md
  - /Users/agents/workspace/fleki/docs/CENTRALIZED_KNOWLEDGE_INSTALL_AND_ROOT_PLAN_2026-04-03.md
  - /Users/agents/workspace/fleki/skills/knowledge/SKILL.md
  - /Users/agents/workspace/fleki/src/knowledge_graph/layout.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/repository.py
  - /Users/agents/workspace/fleki/tests/test_save.py
  - /Users/agents/workspace/fleki/tests/test_rebuild.py
---

# TL;DR

- **Outcome:** Add one host-local mutation lock around `knowledge save` and `knowledge rebuild` so multiple agent runtimes sharing one live Fleki graph cannot interleave writes and stomp topic pages, provenance, indexes, or receipts.
- **Problem:** Fleki explicitly supports one shared graph across multiple local agent runtimes, but the current repository write paths in `apply_save(...)` and `apply_rebuild(...)` perform multi-file mutations with no shared lock today. Concurrent writers can collide even when they are using the official shared contract correctly.
- **Approach:** Keep the existing `knowledge save/search/trace/rebuild/status` surface and the existing `knowledge` skill. Teach the mutation rule there, and add one tiny host-local lock helper at the repository boundary using `state_root`: a non-blocking OS-backed exclusive lock plus a small metadata sidecar. Scope that lock to the short final shared-graph commit. `save` must finish source capture and PDF render work before opening the lock. If the implementation needs temporary prep files to make that work, keep them in one attempt-scoped temp area under `state_root` and clean them best-effort. The helper either acquires once or fails once. It does not sleep, queue, or retry on the caller's behalf. That way `save` and `rebuild` fail loudly with a clean formatted retryable error when another mutation is active, `search` and `trace` stay lock-free, `status` stays non-blocking, and process exit releases the real lock even if cleanup is imperfect.
- **Plan:** First lock the mutation scope, state-root location, and no-new-verb stance. Then ground the exact multi-file write surfaces and failure modes. Then deep-dive the minimal lock contract and `status` visibility. Then implement the helper, wire it into `save` and `rebuild`, update the skill/docs, and add targeted tests.
- **Non-negotiables:**
  - Keep the existing five-verb public surface unless deeper evidence proves a new public verb is necessary.
  - Lock the live graph mutation boundary, not the repo worktree.
  - Host-local only in this pass. No distributed coordinator, queue, or lease service.
  - `search` and `trace` stay lock-free at the graph-mutation boundary. `status` stays non-blocking and must not wait behind the mutation lock.
  - `save` and `rebuild` must fail loudly instead of silently waiting or interleaving.
  - Do not open the mutation lock before long-running preparation. Open it only when the shared graph commit is ready.
  - Operational lock state belongs under `state_root`, not inside `data_root` and not in the repo checkout.
  - The real lock must auto-release on process exit. A plain marker file is not enough.

<!-- arch_skill:block:planning_passes:start -->
<!--
arch_skill:planning_passes
deep_dive_pass_1: done 2026-04-03
external_research_grounding: done 2026-04-03
deep_dive_pass_2: done 2026-04-03
deep_dive_pass_3_requirements_tightening: done 2026-04-03
deep_dive_pass_4_path_and_cleanup_tightening: done 2026-04-03
deep_dive_pass_5_retry_ownership_tightening: done 2026-04-03
deep_dive_pass_6_minimalization: done 2026-04-03
recommended_flow: phase plan -> implement
note: This is a warn-first checklist only. It should not hard-block execution.
-->
<!-- arch_skill:block:planning_passes:end -->

# 0) Holistic North Star

## 0.1 The claim (falsifiable)
> If Fleki adds one host-local non-blocking OS-backed mutation lock at the shared repository boundary and keeps any lock-related temp state under the resolved `state_root`, then same-host Codex, Hermes, and OpenClaw callers that point at the same live graph will no longer be able to interleave `knowledge save` and `knowledge rebuild` writes, the second writer will get a visible mutation-in-progress failure instead of corrupting graph state, `knowledge status` will be able to explain who currently owns the mutation boundary truthfully without waiting, and the system will remain lightweight because `search` and `trace` stay lock-free, `status` stays non-blocking, lock release is automatic on process exit, and the public surface stays centered on the existing five verbs.

## 0.2 In scope
- UX surfaces (what users will see change):
  - `knowledge save` and `knowledge rebuild` can fail with an explicit "another graph mutation is active" error that names the active mutation metadata, suggests a short retry delay, and exposes the timeout threshold the skill should use before stopping.
  - `knowledge status` can surface whether a mutation lock is currently active for the resolved layout.
  - If a prior writer exited without cleanup, the real lock is already gone and the next writer can proceed after refreshing the metadata sidecar.
  - The existing `knowledge` skill and repo docs explain the same-host shared-graph mutation rule plainly, including exactly how long to wait, how often to retry, and when to stop retrying.
- Technical scope (what code/docs will change):
  - One small mutation-lock helper in the shared Python core, likely under `src/knowledge_graph/**`.
  - Repository integration at `KnowledgeRepository.apply_save(...)` and `KnowledgeRepository.apply_rebuild(...)`, with `save` split into pre-lock preparation and a short locked commit.
  - A small `status()` extension so callers can inspect the active mutation state without adding a new coordination subsystem.
  - Updates to `skills/knowledge/SKILL.md`, the relevant knowledge references, and `README.md` so the contract stays truthful.
  - Targeted tests around concurrent save/rebuild attempts against the same resolved layout.

## 0.3 Out of scope
- UX surfaces (what users must NOT see change):
  - A generic task-coordination or repo-edit locking skill.
  - A sixth public `knowledge` verb unless later planning proves the current five verbs cannot carry the repair story cleanly.
  - Blocking or queueing reads behind mutation activity.
- Technical scope (explicit exclusions):
  - Repo-worktree locking.
  - Cross-machine or distributed graph locking.
  - Background daemons, job schedulers, heartbeat services, or automatic retry loops.
  - Helper-side retry harnesses, waiter commands, or internal backoff loops for lock conflicts.
  - Hand-editing `knowledge/**` or other graph files as a concurrency workaround.
  - A semantic or topic-level lock manager in v1 if one host-local global mutation lock is enough.
  - Transactional rollback, journaling, or replay for partial save/rebuild failures.

## 0.4 Definition of done (acceptance evidence)
- Two callers pointed at the same resolved layout cannot successfully run overlapping graph mutations at the same time.
- A second `save` or `rebuild` attempt fails before the shared graph commit begins and returns usable lock-holder metadata.
- `search`, `trace`, and `status` remain usable during an active mutation.
- If a writer crashes or exits abruptly, the next mutation can still acquire the real lock without requiring a manual release command.
- The `knowledge` skill and repo docs explain that graph mutation is serialized at the shared contract boundary while reads remain direct.
- Smallest credible evidence for this plan:
  - targeted unit tests for lock acquire, busy failure, and release
  - one integration test that proves `save` or `rebuild` is rejected while another mutation holds the same layout lock
  - one subprocess or integration test that proves an abrupt process exit does not require manual cleanup before the next writer proceeds
  - one `status` test that surfaces the active mutation metadata

## 0.5 Key invariants (fix immediately if violated)
- Canonical graph mutation continues to happen only through the shared `knowledge` contract. Hand-editing live graph files remains out of bounds.
- There is one host-local active mutation lock per resolved `state_root`.
- Lock state is operational state. It lives under `state_root`, not under `data_root`.
- The OS-backed lock is authoritative. The metadata sidecar is descriptive only.
- `save` and `rebuild` must acquire the mutation lock before their first shared-graph commit write and must release it in a `finally` path.
- `save` must complete long-running preparation before it acquires the mutation lock.
- If `save` needs temporary preparation files, keep them under `state_root` and clean them best-effort. Do not treat them as canonical graph state.
- Process exit must release the real lock even if the sidecar cleanup does not happen.
- `search` and `trace` remain lock-free with respect to the mutation boundary.
- `status` must not wait on the mutation lock. It may only do a non-blocking liveness probe to distinguish a live writer from stale metadata.
- Timeout metadata and retry guidance are advisory to callers. They do not authorize stealing a still-live OS lock from another writer.
- The lock helper never sleeps or retries internally. It returns one success or one busy failure, and the skill instructions tell the agent whether to wait and retry.
- The lock must fail loud instead of silently waiting, silently retrying, or silently widening into a hidden queue.
- If the metadata sidecar exists without a live lock holder, the system must treat it as stale descriptive state and repair or replace it explicitly. It must not pretend a live writer exists.
- Fallback policy is strict:
  - Default: **NO fallbacks or runtime shims**.
  - If a later pass proves the simple host-local lock insufficient, record the exception in the Decision Log with a timebox and removal plan.

# 1) Key Design Considerations (what matters most)

## 1.1 Priorities (ranked)
1. Protect the live shared graph from concurrent write stomps across runtimes on the same host.
2. Keep the existing five-verb skill and CLI surface intact.
3. Keep the implementation small and host-local.
4. Make the active-writer state inspectable through `status` and error output.
5. Preserve the fast read path for `search`, `trace`, and `status`.

## 1.2 Constraints
- Fleki explicitly aims to let multiple runtimes share one graph. Concurrency is part of the product shape, not an edge case.
- The current `save` and `rebuild` paths are bounded synchronous multi-file mutations, not one-file appends.
- `save` can include `shutil.copy2(...)` source capture and `render_pdf_bundle(...)` PDF rendering, so a 10-second default timeout only makes sense if long-running save preparation happens before lock acquisition.
- `layout.py` already gives Fleki a host-local `state_root`, which is the right place for operational coordination state.
- `skills/knowledge/SKILL.md` already says canonical graph state may only be mutated through the shared contract.
- The current public contract and tests are built around `save/search/trace/rebuild/status`, so adding a new public surface should be treated as expensive.
- A plain lockfile marker would create stale-lock cleanup problems on crash, which is exactly the failure shape we want to avoid.

## 1.3 Architectural principles (rules we will enforce)
- Lock at the shared graph mutation boundary, not at the repo-worktree boundary.
- Reuse the existing resolved-layout model. The lock follows `state_root`.
- Start with one host-local global mutation lock per resolved layout.
- Keep `search` and `trace` lock-free, and keep `status` non-blocking.
- Keep active lock state human-inspectable.
- Prefer one small internal helper and truthful docs over a new coordination subsystem.

## 1.4 Known tradeoffs (explicit)
- A single mutation lock is simpler and safer than scoped locks, but it serializes all writes to the shared graph.
- Fail-loud behavior is simpler than wait-and-retry, but the caller must decide when to retry.
- An OS-backed advisory lock plus metadata sidecar is slightly more complex than a plain file marker, but it avoids the stale-lock-on-crash problem.
- The lock prevents overlapping writers, but it does not make `save` or `rebuild` transactional. Partial files can still remain if a mutation fails mid-flight.
- A 10-second default retry budget is only credible if the lock protects a short final commit, not long-running render or source-copy work.
- A caller-visible timeout and retry budget is useful, but automatically breaking a still-live lock after that timeout would be unsafe unless the design grows into a heavier lease system.
- Surfacing lock status in `status` is more honest than burying it in exceptions only, but truthful status requires a non-blocking liveness probe instead of a pure sidecar read.

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- `/Users/agents/workspace/fleki/README.md` explicitly says Fleki is designed so the same graph can be used across multiple local agent runtimes.
- `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` says canonical graph state may only be mutated through the shared `knowledge` contract and that the live graph root is `resolved_data_root`.
- `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` implements `apply_save(...)` and `apply_rebuild(...)` as direct multi-file write paths.
- `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` already exposes `state_root` as the host-local operational state location.
- `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` also lets `search`, `trace`, and `status` write receipts by default and lets `initialize_layout()` create missing files, so the current read path is lock-free but not literally side-effect-free.
- `/Users/agents/workspace/fleki/tests/test_save.py` and `/Users/agents/workspace/fleki/tests/test_rebuild.py` prove the sequential write contract, but they do not prove concurrent-writer safety.

## 2.2 What’s broken / missing (concrete)
- Two same-host runtimes pointed at the same layout can both enter graph mutation code at once.
- `save` and `rebuild` both touch shared graph files, but there is no shared lock that prevents interleaving.
- The current system has no first-class way to explain "someone else is mutating the graph right now."
- `status` surfaces graph health and pending rebuilds, but not active mutation ownership.

## 2.3 Constraints implied by the problem
- The right fix belongs in the shared library boundary, not in one runtime-specific adapter.
- The lock must be host-local because the product is same-host first and the layout is host-local.
- The fix should reuse `state_root` instead of inventing a new state location.
- The fix must preserve the existing read path and the existing public skill shape.

<!-- arch_skill:block:research_grounding:start -->
# 3) Research Grounding (external + internal “ground truth”)

## 3.1 External anchors (papers, systems, prior art)
- Python standard-library `fcntl` docs — adopt a Unix-host non-blocking exclusive file-lock primitive for v1 because Fleki is same-host first, Python 3.12-only, and already runs at a local filesystem boundary; reject byte-range-lock complexity for the first pass because the plan is one global mutation boundary, not scoped sub-file locking.
- Python `os` docs on file-descriptor inheritance — adopt Python’s default non-inheritable file-descriptor behavior as a good fit for short-lived mutation locks so an `exec` path is less likely to leak lock ownership accidentally.
- Plain marker-file locking pattern — reject for v1 because it turns crash cleanup into a manual release problem and cannot distinguish stale descriptive state from a live writer reliably enough.
- Distributed lease managers, queues, and service-backed coordinators — reject for v1 because the repo’s architecture is same-host first and already has a resolved host-local layout with `state_root`.

## 3.2 Internal ground truth (code as spec)
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/workspace/fleki/README.md` — the public repo contract says the same graph is shared across Codex, Hermes, and OpenClaw, the canonical mutable graph lives outside the repo under `~/.fleki/knowledge`, and a fresh install can attach to an already populated shared root.
  - `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md` — the live skill contract already says canonical graph state may only be mutated through the shared `knowledge` contract and that the live graph root is `resolved_data_root`.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `apply_save(...)` is the authoritative bounded save write sequence: initialize layout, validate, persist sources, persist PDF render bundles, persist provenance notes, apply topic actions, then write the save receipt.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `apply_rebuild(...)` is the authoritative rebuild write sequence: initialize layout, apply page updates, refresh indexes, then write the rebuild receipt.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `_apply_topic_actions(...)`, `_persist_provenance_notes(...)`, `_apply_page_update(...)`, and `_refresh_indexes(...)` are the concrete read-modify-write collision points for topic pages, provenance files, and shared index files.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `search(...)`, `trace(...)`, `status(...)`, and `initialize_layout()` still write receipts or bootstrap files by default, so the current non-mutation path is lock-free but not literally side-effect-free.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` and `/Users/agents/workspace/fleki/src/knowledge_graph/models.py` — `state_root` is already a first-class resolved layout field, persisted in the install manifest and kept distinct from `data_root`.
  - `/Users/agents/workspace/fleki/tests/test_layout.py` — the layout contract already proves the default split is `.fleki`, `.fleki/knowledge`, `.fleki/state`, and `.fleki/install.json`, and that `state_root` already carries migrated operational state.
- Existing patterns to reuse:
  - `/Users/agents/workspace/fleki/tests/common.py` — `make_temp_repo()` already injects explicit `data_root`, `config_root`, and `state_root`, which is the clean test seam for same-layout lock coverage.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `status()` already aggregates operational state from receipts and layout info, so active mutation metadata can fit that surface without inventing a second inspector.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` and `/Users/agents/workspace/fleki/tests/test_cli.py` — the public CLI is already locked to five verbs and already accepts `--state-root`, so mutation visibility should be additive to `status`, not a sixth public command.
  - `/Users/agents/workspace/fleki/pyproject.toml` — the repo currently has no lock-specific dependency, which is evidence for a stdlib-first lock helper instead of a new package.

## 3.3 Open questions from research
- Should a later pass remove the incidental receipt and bootstrap writes from `search`, `trace`, and `status`, or is the current non-blocking read path good enough once writer serialization lands?
  - Evidence needed: a local idiomaticity review after the mutation lock lands, because current code still writes receipts and first-run layout files outside the heavy mutation path.
- If Fleki later needs first-class Windows support for the same shared-graph workflow, what backend should the same helper use there?
  - Evidence needed: an explicit supported-host decision beyond the current Unix-like install shape.
- Should the repair scripts that mutate source manifests and render bundles join the same lock discipline in a follow-up pass?
  - Evidence needed: an explicit decision about whether those repair tools are part of the same concurrent-operator story as `knowledge save` and `knowledge rebuild`.
<!-- arch_skill:block:research_grounding:end -->

<!-- arch_skill:block:external_research:start -->
# External Research (best-in-class references; plan-adjacent)

> Goal: anchor the plan in idiomatic, broadly accepted practices where applicable. This section intentionally avoids project-specific internals.

## Topics researched (and why)
- Unix advisory file locking for one same-host mutation boundary — this plan needs the smallest dependable primitive for one global writer lock.
- File-descriptor inheritance and release semantics — this plan depends on automatic release on exit and needs to avoid accidental lock leakage across `exec`.
- Marker-file-only locking vs kernel-managed exclusion — the user explicitly wants the simplest approach that does not create a stale-release problem.

## Findings + how we apply them

### Unix advisory file locking for one whole-file mutation boundary
- Best practices (synthesized):
  - Use a kernel-managed advisory file lock on a dedicated file when the system needs one same-host writer at a time.
  - Use non-blocking acquisition for fail-loud behavior instead of hidden waiting.
  - Prefer whole-file locking when the product contract is one global mutation boundary rather than byte-range coordination.
- Recommended default for this plan:
  - On Unix-like hosts, implement the v1 helper with `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on a dedicated file under `state_root/locks/`.
  - Keep that call behind one tiny helper so a later Windows backend can swap in without changing repository call sites.
  - Normalize busy-lock errors inside the helper and raise one repo-specific busy exception.
- Pitfalls / footguns:
  - `flock()` is advisory, so every canonical writer must keep going through the shared repository boundary.
  - `flock()` locks are associated with one open file description. The helper must hold one opened descriptor for the full mutation lifetime instead of reopening the file mid-mutation.
  - `flock()` semantics vary on network filesystems, so this default is for Fleki's current same-host, local-filesystem operating shape.
- Sources:
  - Python `fcntl` docs — https://docs.python.org/3/library/fcntl.html — official Python API surface for `fcntl.flock()` and `fcntl.lockf()`.
  - `flock(2)` Linux man page — https://man7.org/linux/man-pages/man2/flock.2.html — authoritative kernel/user-space semantics for advisory whole-file locks, non-blocking mode, and release behavior.

### Descriptor inheritance and automatic release
- Best practices (synthesized):
  - Keep the lock file descriptor non-inheritable across `exec`.
  - Treat descriptor close as the real release event, and keep metadata secondary.
  - Use the same held descriptor until the mutation finishes.
- Recommended default for this plan:
  - Open the lock file from Python and rely on Python's default non-inheritable file-descriptor behavior.
  - Keep the descriptor scoped to the mutation context manager so process exit or descriptor close releases the real lock.
  - Do not add a public manual unlock command in v1.
- Pitfalls / footguns:
  - Inference from the sources: non-inheritable prevents `exec` leakage, but `os.fork()` still duplicates descriptors on Unix. Fleki's mutation path should not fork children that keep the lock alive.
  - The JSON sidecar must never be treated as proof of live ownership; only the live lock is authoritative.
- Sources:
  - Python `os` docs — https://docs.python.org/3/library/os.html — official file-descriptor inheritance defaults and Unix `exec` behavior.
  - `flock(2)` Linux man page — https://man7.org/linux/man-pages/man2/flock.2.html — authoritative statement that the lock is tied to the open file description and released when descriptors close.

### Marker-file-only locking is the wrong failure shape
- Best practices (synthesized):
  - Separate authoritative writer exclusion from descriptive metadata.
  - Let the kernel own writer exclusion; let a sidecar file explain the current holder.
- Recommended default for this plan:
  - Keep a dedicated lock file for kernel-managed exclusion and a separate JSON sidecar only for status and error reporting.
  - If the sidecar exists after the real lock is free, replace it after successful acquisition instead of requiring manual stale cleanup.
- Pitfalls / footguns:
  - Inference from the sources: a marker file alone can say "someone was here," but it cannot provide the automatic release-on-exit guarantee this plan needs.
- Sources:
  - Python `fcntl` docs — https://docs.python.org/3/library/fcntl.html — official Python locking API reference.
  - `flock(2)` Linux man page — https://man7.org/linux/man-pages/man2/flock.2.html — authoritative release and ownership semantics for advisory locks.

## Adopt / Reject summary
- Adopt:
  - Unix-like v1 default: whole-file non-blocking `fcntl.flock()` on one dedicated lock file under `state_root/locks/`.
  - One tiny helper that owns busy-error normalization and metadata sidecar updates.
  - Default non-inheritable descriptors and no public manual unlock command.
  - Verification that an abrupt process exit does not require manual cleanup before the next writer.
- Reject:
  - `lockf` or byte-range locking for v1 because the product contract is one global mutation boundary, not sub-file coordination.
  - Marker-file-only locking because it cannot provide kernel-owned release semantics on process exit.
  - Cross-platform backend work in the first pass. Keep the helper seam, but optimize the first implementation for Fleki's current Unix-like operating context.

## Open questions (ONLY if truly not answerable)
- Do we need an explicit subprocess test for `fork` or `exec` leakage, or is a no-fork invariant in the mutation path enough? — evidence needed: implementation inspection of whether the mutation code ever spawns a child while holding the lock.
<!-- arch_skill:block:external_research:end -->

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
- `data_root` currently mixes canonical graph data and operational artifacts:
  - `topics/`, `provenance/`, `sources/`, and `assets/` hold canonical graph data.
  - `receipts/{save,search,trace,rebuild,status}/` and `search/` hold operational artifacts under the same root.
- There is no separate pre-commit staging lifecycle today. `save` writes directly into final `sources/**`, PDF render outputs, provenance notes, topic pages, and receipts.
- Even though no separate staging lifecycle exists today, the current source and PDF render paths already pass through `_stage_source_records(...)` and `_stage_pdf_render_bundles(...)`, which both accept an explicit `root` and are currently just pointed at `self.data_root`.
- `initialize_layout()` also creates `README.md` files under `data_root/` and `data_root/search/` on first use.
- `config_root` holds the install manifest.
- `state_root` is resolved and persisted today, but `KnowledgeRepository` does not currently store any runtime state there after construction.

## 4.2 Control paths (runtime)
- `knowledge` CLI always resolves a layout, constructs `KnowledgeRepository(layout)`, and dispatches directly to `status`, `search`, `trace`, `apply_save`, or `apply_rebuild`.
- `apply_save(...)` currently calls `initialize_layout()` first, then validates bindings and the decision payload, then writes source records with `shutil.copy2(...)` or pointer JSON, then runs `render_pdf_bundle(...)` for copied PDFs, then writes provenance notes, topic pages, and the save receipt.
- `apply_rebuild(...)` currently calls `initialize_layout()` first, then applies page updates, optionally refreshes indexes, and writes the rebuild receipt.
- `search(...)`, `trace(...)`, and `status(...)` each call `initialize_layout()` before reading graph files and each writes a receipt unless `write_receipt=False`.
- `layout._verify_migrated_install(...)` already calls `repo.status(write_receipt=False)` as part of install migration verification.
- `scripts/backfill_source_family.py` and `scripts/backfill_pdf_render_contract.py` instantiate `KnowledgeRepository` and mutate source-record files or render metadata directly outside `apply_save(...)` and `apply_rebuild(...)`.
- `_stage_source_records(...)` writes both raw source artifacts and `*.record.json` manifests with relative paths computed from the `root` parameter it receives.
- `render_pdf_bundle(root=..., raw_pdf_path=...)` writes `.render.md`, `.render.manifest.json`, and optional `.assets/` beside the raw PDF and records relative paths from the supplied `root`.
- `_persist_provenance_notes(...)` and `_write_save_receipt(...)` then copy those source and render relative paths into provenance frontmatter and receipt metadata, so the first root choice propagates through multiple saved artifacts.

## 4.3 Object model + key abstractions
- There is currently no lock-helper module, no active-mutation metadata dataclass, no small mutation-status helper, and no dedicated busy exception in the core library.
- `KnowledgeRepository.status()` returns one flat payload dict of counters, paths, and lists. It has no nested active-writer object today.
- `save` and `rebuild` currently return success payload dicts only. There is no typed "busy mutation" failure shape for direct repo callers.
- There is also no prepared-save object today, but the existing root-aware `_stage_source_records(...)` and `_stage_pdf_render_bundles(...)` helpers are already the natural seam for one.

## 4.4 Observability + failure behavior today
- `status()` is already the operational snapshot surface. It aggregates save receipts, rebuild receipts, topic files, and source-record manifests.
- CLI JSON output is already additive-friendly because it forwards the full payload from `status()`. Human status output is a fixed line list rendered from selected top-level keys.
- CLI errors already use one plain stderr envelope, `error: <message>`, for validation and not-found failures. A new busy failure would currently traceback unless the CLI adds an explicit catch.
- The current skill and README describe `save`, `rebuild`, and `status`, but they do not tell agents what to do on a lock conflict because no shared mutation lock exists yet.
- Busy mutation ownership is invisible today because there is no shared writer exclusion or active-writer metadata.
- `save` and `rebuild` have no rollback or journal today. A failure after partial writes leaves those files on disk.
- Because current `save` does long-running source capture and PDF render inline, a naive whole-method lock would hold the mutation boundary far longer than the new 10-second default budget allows.
- Concurrent-write failure today would show up indirectly as lost updates, duplicate provenance, index churn, or inconsistent topic pages.
- Existing subprocess coverage proves CLI invocation and repair-script execution, but there is no current inter-process same-layout contention test, no abrupt-exit release proof, and no busy-error formatting test.

## 4.5 UI surfaces (ASCII mockups, if UI work)
- The relevant user-facing surfaces are still the existing five knowledge verbs, plain stderr error messages, and `status` JSON plus human output. No graphical UI is in scope.
<!-- arch_skill:block:current_architecture:end -->

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
- Keep graph data where it already belongs:
  - `<data_root>/topics`
  - `<data_root>/provenance`
  - `<data_root>/sources`
  - `<data_root>/assets`
  - `<data_root>/receipts`
- Add host-local mutation state under `state_root`, for example:
  - `<state_root>/locks/knowledge-mutation.lock`
  - `<state_root>/locks/knowledge-mutation.json`
- If `save` needs temporary preparation files to keep the lock short, keep them in one attempt-scoped temp directory under `state_root`.
- Keep receipts where they already live under `data_root` in v1. The first pass does not move receipt storage into `state_root`.
- Keep the skill surface in the existing package:
  - `skills/knowledge/SKILL.md`
  - relevant `skills/knowledge/references/**`

## 5.2 Control paths (future)
- Read-only flows:
  - `search` and `trace` do not interact with the mutation lock.
  - `status` stays non-blocking. It may inspect the sidecar and do one non-blocking liveness probe, but it never waits behind an active writer and it never repairs metadata.
- Mutation flows:
  - Shared setup:
    1. Caller resolves the layout as today.
    2. The helper ensures `state_root/locks/` exists. That directory creation is outside the graph lock because it is lock-state bootstrap, not canonical graph mutation.
  - `save` prepare phase, outside the lock:
    1. Validate bindings and decision payload.
    2. Finish long-running source capture, PDF render, and other prep work before trying to acquire the lock.
    3. If that prep needs temporary files, keep them in one attempt-scoped temp directory under `state_root` and treat them as internal implementation detail, not graph state.
    4. Build the final commit inputs without touching live provenance, topic pages, or receipts yet.
    5. Only after those long-running steps finish does `save` try to acquire the mutation lock.
  - `save` commit phase, inside the lock:
    1. Open the dedicated lock file under `state_root/locks/` and acquire `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on one held file descriptor.
    2. If the lock is already held, read the JSON sidecar best-effort, clean any temp prep files best-effort, and raise `KnowledgeMutationConflict` before any shared graph commit begins. Do not wait, sleep, or retry inside the helper.
    3. If the lock is acquired, write active metadata for observability.
    4. Call `initialize_layout()`.
    5. Perform the canonical source, render, provenance, topic, and receipt writes against `data_root`.
    6. Clear active metadata best-effort, close the held descriptor, and clean any temp prep files best-effort.
  - `rebuild`:
    1. Rebuild has no comparable long-running preparation step today, so it acquires the same lock immediately before `initialize_layout()`.
    2. Inside the lock it runs `initialize_layout()`, page updates, index refresh, and the rebuild receipt.
    3. Then it clears metadata best-effort and closes the held descriptor.
- Observability flow:
  1. `status()` computes the current payload as it does today.
  2. It performs one non-blocking lock-file probe to determine whether a live writer exists right now.
  3. It reads the sidecar metadata best-effort for descriptive context when metadata exists, and it must still report a live writer truthfully even if the sidecar is absent or unreadable.
  4. It adds additive mutation fields to the payload and then writes the optional status receipt as today.
- CLI flow:
  - `save` and `rebuild` catch `KnowledgeMutationConflict` and keep the existing stderr `error: ...` envelope instead of adding a second JSON error protocol.
  - The human busy error is multiline and stable enough for both operators and skills to follow. It always includes the summary line plus `retry_after_seconds=1`, `timeout_seconds=10`, and the stop hint. Metadata lines such as `operation=...`, `started_at=...`, `pid=...`, and scope lines appear when that data is available.
  - `status --json` forwards the additive payload directly.
  - Human `status` output appends mutation lines without removing the existing operational lines.

## 5.3 Object model + abstractions (future)
- `src/knowledge_graph/mutation_lock.py`
  - owns lock-file acquisition and release
  - owns JSON sidecar encode/decode plus atomic replace
  - owns non-blocking liveness probing for `status`
  - owns busy-error normalization
  - owns the shared defaults for `retry_after_seconds=1` and `timeout_seconds=10`
  - never owns caller retry loops, backoff, or waiting behavior
- `ActiveKnowledgeMutation`
  - `operation`: `save` or `rebuild`
  - `started_at`
  - `pid`
  - `resolved_data_root`
  - `requested_topics`
  - `requested_scopes`
  - `retry_after_seconds`
  - `timeout_seconds`
- `KnowledgeMutationConflict(Exception)`
  - carries `active_mutation`
  - carries `retry_after_seconds` and `timeout_seconds`
  - renders one operator-readable message for the existing CLI stderr error path even when metadata is partial
- `KnowledgeRepository.status()` remains a dict-returning API. It gains additive keys:
  - `mutation_active`
  - `active_mutation`

## 5.4 Invariants and boundaries
- There is one active mutation lock per `state_root`.
- The lock guards the whole live-graph mutation boundary, not individual files.
- Any lock-related temp state lives under `state_root`, not `data_root`.
- The OS-backed lock is the truth. The JSON sidecar is only for inspection.
- The helper keeps one open lock-file descriptor for the full mutation lifetime. Closing that descriptor ends the authoritative lock.
- Busy mutation rejection happens before any locked shared-graph commit write in `save` or `rebuild`.
- `save` does long-running source capture and PDF render work before it opens the mutation lock. The lock opens only when the shared graph commit is ready.
- If `save` loses the lock race after preparation, it must clean any temp prep files best-effort before surfacing the busy failure.
- `save` may build candidate provenance payloads before lock acquisition, but provenance dedupe, topic reads, topic writes, and receipt writes still happen against live canonical state inside the lock.
- `rebuild` acquires the real lock before `initialize_layout()` because rebuild has no comparable long-running preparation step today.
- `search` and `trace` never touch the mutation lock.
- `status` may probe liveness, but it never waits on the mutation lock and it never rewrites stale sidecar metadata.
- V1 timeout semantics are: crash cleanup is automatic because the OS lock releases on process exit; caller retry behavior is bounded by `retry_after_seconds` and `timeout_seconds`; a still-live lock is never stolen automatically.
- The default timeout budget is 10 seconds. If the lock regularly needs longer, the lock scope is wrong and must be narrowed rather than silently extended.
- V1 does not add rollback or journaling. It only prevents overlapping writers through the official mutation entrypoints.
- No runtime-specific adapter may bypass the shared mutation boundary if it wants to write canonical graph state.
- No new task-coordination subsystem appears in v1.

## 5.5 UI surfaces (ASCII mockups, if UI work)
```text
save busy failure:
  error: another graph mutation is active
  operation=save
  started_at=2026-04-03T18:40:00+00:00
  pid=12345
  requested_scopes=product
  requested_topics=product/customer-io/current-setup
  retry_after_seconds=1
  timeout_seconds=10
  hint=wait 1 second and retry; if still blocked after 10 seconds, run `knowledge status --json --no-receipt` and stop

status:
  mutation_active=true
  mutation_operation=rebuild
  mutation_pid=12345
  mutation_scopes=product/customer-io
  mutation_started_at=2026-04-03T18:40:00+00:00
```
<!-- arch_skill:block:target_architecture:end -->

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## 6.1 Change map (table)

| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Save mutation boundary | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`, `/Users/agents/workspace/fleki/src/knowledge_graph/pdf_render.py` | `apply_save(...)`, `_persist_source_records(...)`, `_stage_source_records(...)`, `_persist_pdf_render_bundles(...)`, `_stage_pdf_render_bundles(...)`, `render_pdf_bundle(...)` | long-running source capture and PDF render happen inline in the current save path | split save into long-running pre-lock preparation and a short locked final write phase | the 10-second default budget only works if slow prep finishes before lock acquisition | one non-blocking lock attempt around the final canonical write phase | `tests/test_save.py`, new `tests/test_mutation_lock.py` |
| Rebuild mutation boundary | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `apply_rebuild(...)` | `initialize_layout()` and all later writes run with no inter-process exclusion | acquire the mutation lock before `initialize_layout()` and hold it through the final receipt write | same-layout rebuild/save writers can currently interleave across page, index, and receipt writes | `rebuild` raises `KnowledgeMutationConflict` on busy instead of racing | `tests/test_rebuild.py`, new `tests/test_mutation_lock.py` |
| Lock helper | `/Users/agents/workspace/fleki/src/knowledge_graph/mutation_lock.py` | new module | no mutation-lock abstraction exists | add the lock context manager, sidecar serializer, liveness probe, and busy-error normalization | keep OS-lock details out of repository methods and status assembly | `ActiveKnowledgeMutation`, `KnowledgeMutationConflict` | new `tests/test_mutation_lock.py` |
| Status payload | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `status()` | returns graph-health counters only | add minimal mutation fields for active-writer visibility | `status` is the inspection surface for active mutation ownership | `mutation_active`, `active_mutation` | `tests/test_search_trace_status.py`, `tests/test_cli.py` |
| CLI busy failure path | `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` | `main()`, `_command_status(...)` | catches validation/not-found failures only; human status output ignores mutation data | catch `KnowledgeMutationConflict` without traceback, emit the stable multiline busy error, and append mutation lines to human status output | busy failures must stay plain-English and operator-readable even when sidecar metadata is partial | stderr keeps `error: ...`; human status output grows additively | `tests/test_cli.py` |
| Existing status caller | `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` | `_verify_migrated_install(...)` | calls `repo.status(write_receipt=False)` during migration verification | keep the call working with additive status keys and no receipt write | migration verification is already a real status consumer | no behavior change beyond extra returned keys | `tests/test_layout.py` |
| Skill/docs contract | `/Users/agents/workspace/fleki/skills/knowledge/SKILL.md`, `/Users/agents/workspace/fleki/README.md`, relevant `skills/knowledge/references/**` | knowledge workflow docs | explain shared graph mutation conceptually but not active-write serialization, late lock acquisition, or retry behavior | teach that same-host writes are serialized only at the short final commit, that long-running preparation must finish before lock acquisition, that `status` shows active mutation ownership, and that agents should wait 1 second and retry until a 10-second budget is exhausted | docs must match live behavior and retry expectations | same-host mutation-lock doctrine plus lock-failure instructions | doc checks only |

## 6.2 Migration notes
- Keep the public verbs stable in the first pass.
- Treat the mutation lock as a core behavior change at the shared contract boundary, not as a runtime-specific add-on.
- Start with a global mutation lock per `state_root`. Only open scoped-locking work if the simple path proves too limiting.
- Narrow the lock to the short final shared-graph commit. Do not open it before long-running save preparation.
- If `save` needs temporary files to keep the lock short, keep them under `state_root` and clean them best-effort. The exact temp-file layout is internal, not a public design commitment.
- Use a dedicated whole-file non-blocking `fcntl.flock()` lock on Unix-like hosts plus sidecar metadata. Do not start with `lockf()` or a plain marker-file lock.
- Keep platform branching inside the helper so repository call sites stay stable if a later host backend is needed.
- `save` and `rebuild` keep their current success payload shapes. The new behavior is one typed busy failure plus additive status fields.
- Keep the CLI error contract simple. Busy failures should still render through the existing `error: ...` stderr path instead of inventing a second JSON error envelope.
- Use one explicit retry policy in the skill and the busy error: `retry_after_seconds=1`, `timeout_seconds=10`.
- Keep retry ownership in the skill and the agent. The helper and CLI report the retry guidance, but they do not sleep and retry internally.
- If sidecar metadata is missing or unreadable while the real lock is busy, keep the busy failure and status output truthful with minimal guaranteed fields plus the shared retry policy. Do not fabricate holder metadata.
- If the timeout budget is exceeded and the real lock is still live, report a stuck mutation and stop. Do not steal the lock automatically in v1.
- Prefer subprocess-based same-layout tests over thread-only tests because the lock guarantee we care about is inter-process writer exclusion.
- `search` and `trace` stay out of the mutation-lock helper in v1.
- `status` may probe liveness but must not repair stale sidecar metadata. Only the next successful writer replaces stale metadata.

## Pattern Consolidation Sweep (anti-blinders; scoped by plan)

| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| --- | --- | --- | --- | --- |
| Canonical writer entrypoints | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `apply_save(...)`, `apply_rebuild(...)` | one `state_root` mutation lock around the short final shared-graph commit for `save` and the full rebuild mutation body for `rebuild` | prevents the main same-layout writer races this plan exists to stop without letting `save` hold the lock during long-running preparation | include |
| Save preparation | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `_stage_source_records(...)`, `_stage_pdf_render_bundles(...)`; `/Users/agents/workspace/fleki/src/knowledge_graph/pdf_render.py` — `render_pdf_bundle(...)` | prepare sources and PDF renders before lock acquisition | keeps the lock budget short enough for the 10-second default to be credible | include |
| Status inspector | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `status(...)`; `/Users/agents/workspace/fleki/src/knowledge_graph/cli.py` — `_command_status(...)` | additive mutation snapshot plus non-blocking liveness probe | keeps operator visibility truthful without adding a new command | include |
| Existing status consumer | `/Users/agents/workspace/fleki/src/knowledge_graph/layout.py` — `_verify_migrated_install(...)` | tolerate additive status keys and keep `write_receipt=False` | avoids breaking the one existing non-CLI status consumer | include |
| Install/bootstrap script | `/Users/agents/workspace/fleki/scripts/install_knowledge_skill.py` | mutation-lock adoption | this script initializes layout but does not run canonical graph mutations | exclude |
| Read flows | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `search(...)`, `trace(...)` | mutation-lock interaction | avoids turning read commands into lock consumers | exclude |
<!-- arch_skill:block:call_site_audit:end -->

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan (tests optional). No fallbacks/runtime shims - the system must work correctly or fail loudly (delete superseded paths). Prefer programmatic checks per phase; defer manual/UI verification to finalization. Avoid negative-value tests (deletion checks, visual constants, doc-driven gates). Also: document new patterns/gotchas in code comments at the canonical boundary (high leverage, not comment spam).

## Phase 1 - Lock the same-host mutation contract and status story
- Goal
  - Finalize the minimal mutation-lock contract before coding.
- Work
- Freeze v1 as one global mutation lock per `state_root` using a whole-file non-blocking `fcntl.flock()` helper on Unix-like hosts.
- Confirm that `status` is the inspection surface and that no new public verb is added in v1.
- Freeze the save split: long-running source capture and PDF render preparation happen before lock acquisition; only the final commit is locked.
- Freeze the active-metadata field cut for errors and `status`: `operation`, `started_at`, `pid`, `resolved_data_root`, `requested_topics`, and `requested_scopes`.
- Freeze the lock-failure guidance: `retry_after_seconds=1`, `timeout_seconds=10`, and skill instructions that retry until the 10-second budget is exhausted, then stop and report blockage.
- Freeze retry ownership: the helper and CLI emit one busy failure only; the skill and the agent own any wait-and-retry behavior.
- Freeze the stale-sidecar rule: `status` reports it, but only the next successful writer replaces it.
- Keep release automatic. Do not add a manual public release command in v1.
- Verification (smallest signal)
  - One doc review pass can answer:
    - what is locked
    - where lock state lives
    - what stays lock-free
    - how a busy writer is reported
- Docs/comments (propagation; only if needed)
  - Keep the doctrine in the existing knowledge skill and docs.
- Exit criteria
  - The mutation-lock scope is concrete enough that implementation does not have to invent product behavior.
- Rollback
  - Docs-only at this phase.

## Phase 2 - Implement the shared mutation lock in the core library
- Goal
  - Add the smallest correct host-local write lock for the shared graph.
- Work
- Add `src/knowledge_graph/mutation_lock.py` with the lock context manager, sidecar serializer, non-blocking liveness probe, and `KnowledgeMutationConflict`.
- Split `apply_save(...)` into pre-lock preparation plus short locked commit.
- Wrap `apply_rebuild(...)` before `initialize_layout()`.
- Add `status()` visibility for active mutation state.
- Catch `KnowledgeMutationConflict` in the CLI, emit the clean multiline retryable busy error, and append additive mutation lines to human `status` output.
- Keep `search` and `trace` out of the mutation-lock helper.
- Do not add internal retry helpers, waiter commands, or repository-side sleep/backoff loops.
- Verification (smallest signal)
  - Targeted subprocess-level tests around acquire, busy failure, release, abrupt-exit reacquire, and `status`.
- Docs/comments (propagation; only if needed)
  - Add one short comment at the mutation boundary to explain why graph writes are serialized.
- Exit criteria
  - Two concurrent writers against one layout cannot interleave through the official contract.
- Rollback
  - Revert the helper and wrappers while leaving the read-only graph behavior unchanged.

## Phase 3 - Align the skill/docs surface with live behavior
- Goal
  - Make the new behavior obvious to runtime callers and human operators.
- Work
  - Update `skills/knowledge/SKILL.md`, the relevant references, and `README.md`.
  - Add or update CLI contract wording if the busy failure should be more operator-readable.
  - Run one same-layout smoke that proves failure on overlapping mutation attempts and continued read access.
- Verification (smallest signal)
  - One manual or subprocess smoke against a temp layout:
    - writer A acquires mutation lock
    - writer B gets busy failure
    - `status` shows the active mutation
    - `search` or `trace` still works
- Docs/comments (propagation; only if needed)
  - Keep replies and docs command-first and plain English.
- Exit criteria
  - The shared skill, CLI, and status surface all tell the same story.
- Rollback
  - Revert the doc rollout if the lock contract still changes under test.
<!-- arch_skill:block:phase_plan:end -->

# 8) Verification Strategy (common-sense; non-blocking)

## 8.1 Unit tests (contracts)
- Prefer targeted tests around the new lock helper, minimal status reporting, and repository wrappers.
- Avoid adding a new concurrency harness if ordinary unittest plus subprocess can prove the contract.

## 8.2 Integration tests (flows)
- Prefer separate-process same-layout checks over thread-only checks, because the guarantee we care about is inter-process writer exclusion.
- Prove that:
  - `save` blocks a second `save`
  - `save` blocks `rebuild`
  - `rebuild` blocks `save`
  - `status` reports the active mutation
  - abrupt process exit releases the real lock so the next writer succeeds without manual cleanup
- Reuse `tests/common.py::make_temp_repo()` plus the existing subprocess pattern from `tests/test_cli.py` and `tests/test_source_families.py`.

## 8.3 E2E / device tests (realistic)
- One same-host smoke with two callers against the same layout is enough.
- Keep reads in the smoke so we prove that the new write lock does not turn into a read lock.

# 9) Rollout / Ops / Telemetry

## 9.1 Rollout plan
- Roll this out as a core behavior change of the shared `knowledge` contract.
- Land the lock helper, then the status/docs alignment, then the smoke proof.
- Keep the runtime surface stable. The same change should protect Codex, Hermes, and OpenClaw because it lives below them.

## 9.2 Telemetry changes
- No new telemetry system is in scope.
- `status` and fail-loud error metadata are enough operational visibility for v1.

## 9.3 Operational runbook
- If a write fails because a mutation is active, wait 1 second and retry.
- Keep retrying until 10 seconds of total wait has elapsed.
- If the lock is still active after 10 seconds, inspect `knowledge status --json --no-receipt` once and stop. Treat that as a stuck mutation, not permission to force the lock open.
- If you extend `save`, finish source capture, PDF render, and any other long-running preparation before acquiring the mutation lock. Hold the lock only for the final shared-graph commit.
- If you only need to read, keep going.
- If the active metadata is stale relative to the live lock holder, replace or repair the metadata only after the real lock state proves no writer is active. Do not guess.
- Do not hand-edit the live graph to "get around" the lock.

# 10) Decision Log (append-only)

## 2026-04-03 - Move the locking plan to the shared graph mutation boundary

Context
- The first draft treated this as repo-worktree coordination. That did not match what Fleki actually owns.
- Fleki’s real shared mutable thing is the live graph under the resolved layout, shared across runtimes on the same host.
- A plain marker-file lock would leave exactly the "what if they never release?" problem the user wanted to avoid.

Options
- Add repo-worktree locking.
- Add a new generic coordination skill.
- Add one host-local mutation lock at the existing `knowledge` contract boundary.

Decision
- Put the plan at the shared graph mutation boundary, keep the existing `knowledge` skill as the public behavior surface, and use a real OS-backed non-blocking lock plus a small metadata sidecar.

Consequences
- The plan now matches Fleki’s actual ownership and current same-host multi-runtime design.
- The first pass can stay small because it reuses `state_root`, `status`, and the existing five-verb surface.
- Crash or abrupt-exit behavior is safer because the real lock releases with process exit.
- Deeper planning still needs to settle only the minimum active-metadata field cut and whether a later scoped-lock design is worth it.

Follow-ups
- Deep-dive the exact metadata field cut for busy failures and `status`.
- Confirm the concrete host-local lock primitive to use in the implementation.

## 2026-04-03 - Confirm the v1 lock shape after repo grounding

Context
- The plan was revised after deeper repo grounding showed that Fleki’s real shared mutable boundary is the live graph under the resolved layout.
- The remaining product choice was how to keep the first pass simple without creating a stale-lock cleanup problem.

Options
- Use a plain marker-file lock and a manual release story.
- Use a global non-blocking OS-backed lock per `state_root` plus descriptive metadata.
- Design scoped or topic-level locks immediately.

Decision
- Confirm v1 as one global non-blocking OS-backed mutation lock per `state_root`, with `status` as the inspection surface and no public manual release command.

Consequences
- Crash and abrupt-exit behavior stays safe because the real lock releases with process exit.
- The first pass stays small and runtime-neutral because it sits at the shared repository boundary.
- All graph mutations serialize in v1, which is simpler but coarser than a future scoped-lock design.

Follow-ups
- Deep-dive the metadata schema and exact lock primitive.

## 2026-04-03 - Set the current-host lock primitive from external research

Context
- The remaining design choice was which real lock primitive gives Fleki the simplest same-host writer exclusion without creating a stale-release problem.
- External research confirmed that Fleki's current install shape is well matched to a Unix advisory whole-file lock, and that Python already defaults new file descriptors to non-inheritable.

Options
- Use a byte-range or `lockf()`-style lock even though Fleki only needs one global mutation boundary.
- Use a whole-file non-blocking `fcntl.flock()` lock on a dedicated file and keep metadata separate.
- Use a marker-file-only lock and rely on manual stale cleanup.

Decision
- For the first implementation on Fleki's current Unix-like hosts, use one dedicated lock file under `state_root/locks/` and acquire a whole-file non-blocking `fcntl.flock()` lock through a small helper. Keep the JSON sidecar descriptive only.

Consequences
- The first implementation can stay smaller because it does not need byte-range coordination or a new dependency.
- Abrupt process exit is no longer a manual unlock problem because the kernel releases the real lock when the held descriptor closes.
- The helper must own busy-error normalization and keep one descriptor alive for the full mutation lifetime.
- Windows or non-Unix backends are explicitly deferred behind the same helper seam instead of being half-designed in v1.

Follow-ups
- Deep-dive the active-metadata field cut and busy-failure wording.
- Verify abrupt-exit reacquire behavior with a subprocess-level test.

## 2026-04-03 - Keep `status` truthful with a non-blocking liveness probe

Context
- A pure sidecar read would stay lightweight, but it could lie after a writer crashes because stale metadata may outlive the real OS lock.
- The plan still needs `status` to remain lightweight and must not turn it into a waiting command.

Options
- Read the sidecar only and accept stale false positives until the next writer repairs it.
- Let `status` wait on the real lock to get certainty.
- Let `status` do one non-blocking liveness probe and report stale metadata separately.

Decision
- Keep `search` and `trace` fully lock-free, but let `status` do one non-blocking liveness probe and use sidecar metadata only as descriptive context. Report `mutation_active` and `active_mutation`, and leave stale-sidecar replacement to the next successful writer.

Consequences
- `status` can stay truthful after abrupt exits without requiring a manual unlock command.
- The plan no longer needs to pretend `status` is literally lock-free, but it remains non-blocking and lightweight.
- Implementation needs only a small status helper plus additive CLI/status output, not a second coordination command.

Follow-ups
- Implement the small status helper and CLI catch path.
- Cover live-writer, stale-sidecar, and abrupt-exit cases with subprocess-level tests.

## 2026-04-03 - Treat bootstrap and receipts as part of the critical section

Context
- The deep-dive pass showed that `initialize_layout()` writes under `data_root` before either mutation path does any of its heavier work.
- The same pass showed that save and rebuild receipts are the final write in each mutation path, and that there is no rollback if a mutation fails after partial writes.

Options
- Acquire the lock after `initialize_layout()` and treat bootstrap writes as harmless.
- Acquire the lock before `initialize_layout()` and hold it through the matching receipt write.
- Expand v1 into rollback or journaling so partial-write cleanup becomes part of the feature.

Decision
- Historical intermediate decision: treat bootstrap and receipts as part of the critical section. This remains true for `rebuild`, and the later active plan keeps it true for the locked commit portion of `save` after staged preparation under `state_root`.

Consequences
- No live shared-graph commit write in the canonical mutation paths begins before writer exclusion is active.
- The critical section is concrete for `rebuild`, and for `save` it begins after long-running preparation is complete.
- Partial writes can still remain after a failure, but they will not overlap with another writer through the official mutation boundary.

Follow-ups
- Implement the helper and wrappers with one held file descriptor per mutation.
- Prove abrupt-exit release and same-layout contention with subprocess-level tests.

## 2026-04-03 - Make timeout behavior explicit without unsafe lock stealing

Context
- The user wants lock failures to be easy for agents to handle, the busy error to be clean, and stuck locks to time out instead of leaving callers in limbo.
- A real OS lock already solves the crash case safely, but stealing a still-live lock after a timeout would create overlapping writers unless the design grows into a heavier lease system.

Options
- Keep the error minimal and leave retry behavior entirely to each caller.
- Add explicit retry and timeout fields to the metadata, skill, and CLI error, but never steal a still-live lock automatically.
- Add a lease/heartbeat system that expires and can replace a live lock holder after timeout.

Decision
- Historical intermediate decision: make retry behavior explicit and uniform in the plan and skill, and never steal a still-live lock automatically. This entry was later tightened to a 10-second default budget.

Consequences
- Agents get one clear instruction path instead of inventing different retry behavior on each runtime.
- The design stays lightweight because it does not need heartbeats, leases, or lock stealing.
- A truly hung but still-live writer remains a manual intervention case in v1, but that is safer than creating two concurrent writers.
- The later active plan narrowed the default retry budget from 120 seconds to 10 seconds.

Follow-ups
- Reflect the exact retry instructions in `skills/knowledge/SKILL.md`.
- Cover the busy error format and timeout fields in CLI and repository tests.

## 2026-04-03 - Narrow `save` lock scope so the 10-second default stays credible

Context
- The user tightened the operating expectation: the default retry budget should be 10 seconds, and well-scoped mutations should not hold the lock longer than that under normal conditions.
- Repo grounding showed that `apply_save(...)` currently does long-running source capture and PDF render work inline before it writes provenance, topics, and receipts.
- Holding the mutation lock across that whole current save method would make the 10-second default misleading and would create avoidable contention.

Options
- Keep locking the whole current `save` method and quietly accept that the 10-second default will often be wrong.
- Raise the default timeout until whole-method save locking feels tolerable.
- Split `save` into a pre-lock preparation phase plus a short locked commit phase, and keep `rebuild` locked at its current mutation body because it has no comparable long-running prep today.

Decision
- Keep the retry budget at `retry_after_seconds=1` and `timeout_seconds=10`, and reshape `save` so it finishes long-running preparation before it opens the mutation lock. Only the final shared-graph commit stays inside the lock. `rebuild` still acquires the lock immediately before `initialize_layout()`.

Consequences
- The timeout guidance, skill instructions, and CLI busy error remain honest because the lock now covers the short contested part of `save`, not source copy or PDF render preparation.
- The implementation may need minimal temp preparation under `state_root` to keep the lock short, but that temp-file shape is internal detail, not part of the public design.
- The earlier assumption that both mutation paths should always lock before `initialize_layout()` is now superseded for `save` only.
- The earlier 120-second retry-budget assumption is superseded. The active plan default is 10 seconds.

Follow-ups
- Update the knowledge skill to say plainly that agents should do long-running preparation first and only open the lock when ready to commit.
- Cover staged-save contention and the 10-second default in repository and CLI tests.

## 2026-04-03 - Keep any save temp files minimal and internal

Context
- The current save code already has root-aware `_stage_source_records(...)` and `_stage_pdf_render_bundles(...)` helpers, and `render_pdf_bundle(...)` writes render metadata relative to the `root` it receives.
- The user does not want a larger temp-artifact subsystem, helper abstraction, or extra public design surface unless it is truly necessary.

Options
- Write directly into the live graph before the lock and accept long lock holds or race risk.
- Add a richer staged-save subsystem instead of keeping temp preparation internal.
- Keep any temp preparation minimal, internal, and under `state_root` only if the implementation actually needs it to keep the lock short.

Decision
- Do not treat temp preparation as a first-class architecture surface. If the implementation needs temp files to keep `save` out of the lock during slow work, keep them under `state_root`, clean them best-effort, and keep the exact shape internal.

Consequences
- The plan stays focused on the actual product behavior instead of over-designing temp-file mechanics.
- `data_root` stays reserved for canonical graph state and live receipts.
- Implementation can still choose the smallest working temp-file shape later if it turns out to be necessary.

Follow-ups
- Keep the implementation small when the repo work starts.
- Test user-visible behavior, not temp-file architecture.

## 2026-04-03 - Keep retry behavior in the skill, not in the lock helper

Context
- The agents that call `knowledge` can read the skill instructions, wait a moment, and try again on their own.
- Adding repository-side retry loops, waiter commands, or backoff harnesses would make the behavior harder to reason about and would duplicate logic the calling agent can already handle.
- The user wants the locking system to stay lightweight and minimally enforced.

Options
- Add helper-side sleep and retry behavior so callers do not need to think about lock conflicts.
- Add a separate retry harness or waiter command around `knowledge save` and `knowledge rebuild`.
- Keep the helper fail-loud and put the retry instructions in the skill and the busy error only.

Decision
- Keep retry ownership with the calling agent. The helper acquires once or raises `KnowledgeMutationConflict` once. The CLI prints the retry guidance, and the skill tells the agent to wait 1 second and retry for up to 10 seconds total.

Consequences
- The implementation stays small because it only needs one non-blocking acquire path and one clean busy failure path.
- Agents still get clear instructions because the busy error and the skill say exactly what to do next.
- There is no extra retry harness, queue, or helper command to keep in sync with the skill doctrine.

Follow-ups
- Reflect the same wording in `skills/knowledge/SKILL.md` when implementation starts.
- Keep tests focused on single-attempt acquire, busy failure, cleanup, and status truthfulness rather than internal retry behavior.

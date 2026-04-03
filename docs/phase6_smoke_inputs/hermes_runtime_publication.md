# Phase 6 Smoke Input: Hermes

This note exists only to prove the same shared `knowledge` graph can be updated
from Hermes after Codex has already written into it.

Knowledge worth preserving:

- The canonical `knowledge` skill is single-sourced in the `fleki` repo.
- Direct Codex discovers it from workspace `.agents/skills`.
- Hermes discovers it from the shared `agents/_shared/skills` publication path.
- Paperclip can discover it from repo-owned `skills/` packages without changing
  storage semantics.

Suggested semantic home:

- knowledge-system/runtime-integration

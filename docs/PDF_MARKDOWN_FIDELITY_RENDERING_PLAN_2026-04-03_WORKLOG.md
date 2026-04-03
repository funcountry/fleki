# Worklog

Plan doc: /Users/agents/workspace/fleki/docs/PDF_MARKDOWN_FIDELITY_RENDERING_PLAN_2026-04-03.md

## Initial entry
- Run started.
- Current phase: Phase 1 — Dependency Surface And Engine Confirmation.
- Intended end state: ship the PDF render-bundle path end to end, verify it with repo tests, and validate fidelity on the two real acceptance PDFs.

## Phase 1 (Dependency Surface And Engine Confirmation) Progress Update
- Work completed:
  - Added `/Users/agents/workspace/fleki/pyproject.toml` with Docling as the shipped dependency and PyMuPDF4LLM as a comparison extra.
  - Created `.venv` on Python 3.12 and installed the repo plus comparison dependencies successfully.
  - Ran a real Docling vs PyMuPDF4LLM bake-off against `Communication_Guidelines.pdf` and `2026-03-05_learning_to_intent_mockup_packet.pdf`.
  - Confirmed that Docling preserves richer heading structure on both acceptance PDFs and, with picture-image generation enabled, emits referenced image assets for the mockup packet.
- Tests run + results:
  - `PYTHONPATH=src:tests python3 -m unittest discover -s tests -p 'test_*.py' -v` — passed baseline before implementation.
  - `.venv/bin/python` bake-off script against the two acceptance PDFs — passed; results written under `/tmp/pdf_fidelity_bakeoff`.
- Issues / deviations:
  - Host default `python3` is 3.9.6, so the shipped install/test lane for this feature is Python 3.12, not the host default interpreter.
  - Docling default PDF options only emitted placeholder image markers; enabling `generate_picture_images=True` was required to get referenced image assets.
- Next steps:
  - Implement the Phase 2 source-adjacent render bundle and fail-loud save-path cutover.

## Phase 2 (Source-Adjacent Render Bundle Cutover) Progress Update
- Work completed:
  - Added `/Users/agents/workspace/fleki/src/knowledge_graph/pdf_render.py` as the repository-owned Docling render boundary and wired `KnowledgeRepository.apply_save(...)` through it before provenance/topic writes.
  - Extended source-record manifests with `source_family`, render eligibility, omission reasons, and pointers to `.render.manifest.json` / `.render.md`.
  - Implemented explicit omission handling for pointer-only and `secret_pointer_only` PDFs and kept PDF-derived assets out of `knowledge/assets/`.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_pdf_rendering tests.test_source_families tests.test_save tests.test_search_trace_status tests.test_contracts -v` — passed.
- Issues / deviations:
  - Docling model initialization adds a one-time weight-loading cost to the first PDF render in a process.
- Next steps:
  - Propagate render truth through provenance, receipts, trace, status, validation, and the published skill docs.

## Phase 3 (Provenance, Trace, Status, And Contract Hardening) Progress Update
- Work completed:
  - Extended provenance notes, save receipts, `trace(...)`, and `status(...)` to surface render manifests, render artifacts, and omission reasons without adding a second render SSOT.
  - Hardened `validate_save_decision(...)` against caller-owned render metadata and documented the semantic-vs-render boundary in `text.py`.
  - Updated both published `knowledge` skill packages and the shared test harness to match the new PDF render-backed evidence path.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_pdf_rendering tests.test_source_families tests.test_save tests.test_search_trace_status tests.test_contracts -v` — passed after the surface hardening changes.
- Issues / deviations:
  - None beyond the planned Python 3.12 interpreter requirement for the shipped Docling path.
- Next steps:
  - Run the full suite, compile verification, and the two-PDF acceptance smoke.

## Phase 4 (Real-PDF Acceptance, Cleanup, And Rollout Readiness) Progress Update
- Work completed:
  - Ran the real `save`, `trace`, and `status` flow on `Communication_Guidelines.pdf` and `2026-03-05_learning_to_intent_mockup_packet.pdf` through an isolated repository instance.
  - Confirmed materially richer stored markdown structure on the acceptance corpus: 27 heading markers / 4 referenced assets / 4 page breaks for the communication guide, and 41 heading markers / 6 referenced assets / 7 page breaks for the learning-to-intent packet.
  - Removed the generated `src/fleki_knowledge_graph.egg-info/` directory so the repo does not retain editable-install debris from the implementation lane.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed (15 tests).
  - `.venv/bin/python -m compileall src` — passed.
  - `.venv/bin/python` acceptance smoke script over the two real PDFs — passed; `trace(...)` returned render-manifest paths and `status(...)` reported `pdf_rendered_sources = 2` and `pdf_render_omitted_sources = 0`.
- Issues / deviations:
  - None blocking; the feature is implemented and verified in the Python 3.12 lane.
- Next steps:
  - Hand off to `arch-step audit-implementation`.

## Implementation Rerun (Scope Cleanup + Fresh Verification)
- Work completed:
  - Removed the leftover `legacy_pdf_without_render` status field so the shipped PDF fidelity path no longer carries pre-feature compatibility bookkeeping.
  - Reconfirmed that the current implementation remains a new-path-only feature: copied PDFs render, pointer-only PDFs omit explicitly, and no legacy/backfill surface is exposed.
- Tests run + results:
  - `PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` — passed (15 tests).
  - `.venv/bin/python -m compileall src` — passed.
  - `.venv/bin/python` acceptance smoke script over the two real PDFs — passed; `trace(...)` returned render-manifest paths, and `status(...)` reported `pdf_rendered_sources = 2` and `pdf_render_omitted_sources = 0`.
- Issues / deviations:
  - None blocking; this rerun only removed stale legacy bookkeeping and refreshed verification evidence.
- Next steps:
  - No further implementation work remains for this feature.

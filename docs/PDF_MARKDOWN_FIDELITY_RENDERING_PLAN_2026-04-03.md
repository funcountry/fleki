---
title: "Fleki - PDF Markdown Fidelity Rendering Plan - Architecture Plan"
date: 2026-04-03
status: complete
fallback_policy: forbidden
owners: [Amir]
reviewers: [Amir]
doc_type: architectural_change
related:
  - /Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md
  - /Users/agents/workspace/fleki/src/knowledge_graph/repository.py
  - /Users/agents/workspace/fleki/src/knowledge_graph/text.py
  - /Users/agents/workspace/fleki/tests/test_source_families.py
  - /Users/agents/workspace/agents/agents/agent_writer/artifacts/drive_inbox/2026-02-25/Communication_Guidelines.pdf
  - /Users/agents/workspace/agents/agents/agent_ux_analyst/artifacts/2026-03-05_learning_to_intent_mockup_packet.pdf
  - /Users/agents/workspace/agents/agents/agent_ux_analyst/artifacts/2026-03-05_learning_to_intent_mockup_packet.md
---

# TL;DR

- **Outcome:** Upgrade PDF ingest so the system preserves as much document structure and formatting as practical in a stored markdown-first render, instead of collapsing rich PDFs into a raw file plus a few summary bullets.
- **Problem:** The current knowledge flow preserves the raw PDF and semantic meaning, but it does not preserve formatting-rich structure. Real PDFs from `../agents` proved that headings, nested lists, quotes, embedded visual references, and section ordering are flattened because the current accepted markdown artifacts are limited to summary-style provenance plus `#`/`##` sections with bullet statements.
- **Approach:** Introduce one explicit Docling-backed PDF extraction boundary that produces a source-adjacent structured render bundle plus manifest-backed metadata before semantic filing. Keep semantic topic pages meaning-first, but let provenance and trace surfaces point to the richer formatted render and make fidelity or explicit omission state visible.
- **Plan:** First confirm the fidelity North Star and the no-silent-downgrade policy. Then research viable local PDF-to-markdown or equivalent structural extraction options. Then deep-dive the current save/provenance/render pipeline and define the target storage contract. Then implement in four stages: dependency surface plus engine bake-off, source-adjacent render-bundle cutover, provenance/trace/status contract propagation, and real-PDF acceptance plus cleanup.
- **Non-negotiables:**
  - Semantic topic pages remain meaning-first; formatted PDF renders are supporting evidence artifacts, not the primary browse model.
  - Original PDFs must still be preserved byte-for-byte alongside any derived render.
  - A PDF ingest may only claim high-fidelity preservation when it actually produced and stored the structured render; no silent downgrade to raw text while pretending fidelity succeeded.
  - Fidelity must be judged on real structured PDFs, not only toy text-only samples.
  - The PDF rendering path must stay local, explicit, and fail-loud; this plan does not authorize a generic network service or hidden daemon.
  - One bounded PDF render contract is preferred over ad hoc per-file heuristics.
  - The v1 runtime ships one PDF render engine and one writer for render metadata; evaluation baselines are allowed during implementation, but no dual converter runtime path ships.
  - Pointer-only or `secret_pointer_only` PDFs must not persist structured render content; omission must be explicit in manifests, provenance, and receipts.

<!-- arch_skill:block:implementation_audit:start -->
# Implementation Audit (authoritative)
Date: 2026-04-03
Verdict (code): COMPLETE
Manual QA: pending (non-blocking)

## Code blockers (why code is not done)
- none

## Reopened phases (false-complete fixes)
- none

## Missing items (code gaps; evidence-anchored; no tables)
- none

## Non-blocking follow-ups (manual QA / screenshots / human verification)
- Optional human spot-check: open one stored `.render.md` from each acceptance PDF and compare it against the original PDF for subjective fidelity beyond the scripted heading/image/page-break signals.
<!-- arch_skill:block:implementation_audit:end -->

<!-- arch_skill:block:planning_passes:start -->
<!--
arch_skill:planning_passes
deep_dive_pass_1: not started
external_research_grounding: done 2026-04-03
deep_dive_pass_2: done 2026-04-03
recommended_flow: deep dive -> external research grounding -> deep dive again -> phase plan -> implement
note: This is a warn-first checklist only. It should not hard-block execution.
-->
<!-- arch_skill:block:planning_passes:end -->

# 0) Holistic North Star

## 0.1 The claim (falsifiable)
> If we add a first-class PDF extraction path that emits a stored structured render plus manifest-backed fidelity metadata before semantic condensation, and validate it against real structured PDFs from `../agents`, then accepted PDF-backed knowledge will retain materially more heading hierarchy, list structure, quoted/callout structure, embedded image references, and section ordering than the current flow, while the semantic knowledge graph remains meaning-first and provenance-backed.

## 0.2 In scope
- UX surfaces (what users will see change):
  - PDF-backed provenance and trace flows can point to a formatted render artifact instead of only the raw PDF plus prose summary.
  - Operators can inspect whether a PDF ingest succeeded in high-fidelity mode or only limited-fidelity mode.
  - PDF-backed knowledge answers can cite the structured render path when formatting matters.
  - Real structured PDFs such as communication guides and UX mockup packets should preserve visibly richer markdown structure than the current flattened outputs.
- Technical scope (what code/docs/packaging will change):
  - A bounded PDF extraction contract that runs before semantic filing.
  - A storage model for structured PDF renders, render manifests, and any extracted assets or page references required to preserve structure.
  - Provenance, receipt, and trace surfaces that expose fidelity mode, render paths, and extraction gaps honestly.
  - Integration of the structured render into the existing `knowledge save/search/trace/status` flow without replacing meaning-first topic pages.
  - Real-PDF verification on representative files from `../agents`.

## 0.3 Out of scope
- UX surfaces (what users must NOT see change):
  - Replacing semantic topic pages with full-document transcriptions.
  - A new user-facing browse mode organized by PDF family instead of semantic topics.
  - Perfect pixel-level parity with arbitrary PDFs.
- Technical scope (explicit exclusions):
  - A general document-conversion platform for every file type in this pass.
  - A networked conversion service, daemon, or hidden control plane.
  - Reworking non-PDF modalities such as images, audio, or video in this plan.
  - A silent fallback path that downgrades to raw text while reporting success as if structure were preserved.
  - Broad OCR-first handling for scanned/unstructured PDFs unless research shows it is required for the concrete target corpus.
  - A runtime-pluggable or multi-engine PDF conversion framework in v1.
  - Redacted structured-render storage for pointer-only or secret PDFs in this pass.

## 0.4 Definition of done (acceptance evidence)
- The system preserves the original PDF and also stores a structured render artifact for supported PDFs.
- Provenance notes and receipts explicitly record fidelity mode, extraction gaps, and the path to the structured render.
- For `/Users/agents/workspace/agents/agents/agent_writer/artifacts/drive_inbox/2026-02-25/Communication_Guidelines.pdf`, the accepted render preserves the document's heading hierarchy and multi-level list structure materially better than the current flattened semantic output.
- For `/Users/agents/workspace/agents/agents/agent_ux_analyst/artifacts/2026-03-05_learning_to_intent_mockup_packet.pdf`, the accepted render preserves section hierarchy plus embedded mockup references or equivalent structural markers materially better than the current flattened semantic output.
- Search/trace can point from a PDF-backed claim to the semantic page, provenance note, raw source record, and the structured render artifact.
- Unsupported or failed high-fidelity PDF ingests fail loudly or are marked limited-fidelity explicitly; they are not silently reported as full-fidelity success.
- Smallest credible evidence for this plan:
  - contract tests for render manifest and provenance metadata
  - integration tests on fixture PDFs with meaningful structure
  - one local realistic smoke run on real PDFs from `../agents`

## 0.5 Key invariants (fix immediately if violated)
- Original PDFs remain preserved as immutable source artifacts.
- Semantic topic pages remain semantic summaries or decisions, not document mirrors.
- The system stores at most one canonical structured render per accepted PDF source/version unless a later explicit revision model is introduced.
- Render-eligible copied PDFs either persist a declared render bundle or fail before provenance/topic writes.
- Pointer-only and `secret_pointer_only` PDFs never persist rendered content; omission reason is explicit instead.
- A PDF ingest either produces a declared fidelity mode with explicit gaps or fails loudly.
- Receipts, provenance, and trace surfaces must agree about render availability and fidelity status.
- The PDF rendering path must be explicit and inspectable on disk; no hidden conversion side effects.
- The extraction contract must be local-first and deterministic enough that repeated ingest of the same PDF does not produce unexplained structural drift.
- Fallback policy (strict):
  - Default: **NO silent downgrade from high-fidelity PDF rendering to raw-text extraction**.
  - If a limited-fidelity mode is permitted later, it must be explicit in metadata, surfaced to the caller, and never presented as equivalent to structured preservation.

# 1) Key Design Considerations (what matters most)

## 1.1 Priorities (ranked)
1. Preserve real PDF structure materially better than the current flattened path.
2. Report fidelity honestly and fail loudly on unsupported high-fidelity cases.
3. Keep the semantic knowledge graph meaning-first.
4. Keep the PDF rendering path local, inspectable, and operationally simple.
5. Minimize architectural sprawl beyond the bounded PDF render contract.

## 1.2 Constraints
- The current repository already has a working semantic knowledge graph and PDF source-family preservation; this plan must extend that flow instead of replacing it wholesale.
- Current accepted markdown artifacts are produced by simple section-and-bullet renderers, so richer fidelity requires a new source-render layer rather than wishful prompt changes alone.
- The knowledge system already distinguishes raw sources, provenance, and semantic topics; the new render artifact must fit that layering cleanly.
- The prior system doctrine was intentionally skeptical of helper converters; this plan must either elevate PDF rendering to a first-class bounded subsystem or reject it explicitly after research.
- Real structured PDFs from `../agents` are available and should be the ground truth test corpus.

## 1.3 Architectural principles (rules we will enforce)
- Separate source-render fidelity from semantic condensation.
- Keep one explicit source of truth per layer:
  - raw PDF
  - structured render
  - provenance note
  - semantic topic page
- Make fidelity mode a first-class contract field, not an inference.
- Prefer one bounded PDF rendering contract over scattered special cases.
- Do not let a richer PDF render path mutate the system into a source-family-first wiki.
- Ship one runtime converter engine and one render-metadata writer in v1.
- Keep raw-source metadata and derived-render metadata in separate SSOT layers instead of duplicating the full contract everywhere.

## 1.4 Known tradeoffs (explicit)
- Better PDF fidelity will likely require a more deterministic extraction boundary than the original LLM-first-only ingest posture for PDFs.
- Markdown-first structured renders are more inspectable than opaque formats, but they will still lose some layout detail compared with the original PDF.
- Supporting embedded assets and page references increases storage and manifest complexity, but without them rich visual PDFs will continue to flatten.
- A stricter no-silent-downgrade rule may cause more explicit ingest failures, but that is preferable to false confidence.
- Shipping Docling as the lone runtime engine in v1 reduces optionality, but it avoids a dual-path abstraction before evidence shows we need one.

# 2) Problem Statement (existing architecture + why change)

## 2.1 What exists today
- `KnowledgeRepository.apply_save(...)` persists raw source files, provenance notes, semantic topic pages, and receipts.
- PDF sources are preserved under `knowledge/sources/pdf/...`, and the contract already allows `direct_local_pdf` as a reading mode.
- Provenance notes are rendered through a fixed summary template in `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py`.
- Semantic topic pages are rendered through `/Users/agents/workspace/fleki/src/knowledge_graph/text.py`, which currently emits a title, `##` headings, bullet statements, and a provenance list.
- Automated tests prove source-family preservation for PDFs, but they do not prove formatting preservation.

## 2.2 What’s broken / missing (concrete)
- Rich PDFs are flattened during accepted markdown output: headings, nested lists, callouts, embedded visuals, and page boundaries do not survive as structured markdown artifacts.
- The system stores the raw PDF but not a high-fidelity structured render that downstream users or agents can inspect.
- Provenance and receipt layers can report reading gaps, but there is no explicit PDF fidelity contract or render-manifest surface.
- Real PDFs from `../agents` showed the failure mode directly:
  - the communication guide retains meaningful structure in the PDF, but the accepted markdown output collapses it to three bullets
  - the learning-to-intent packet contains multiple mockup sections and embedded image references, but the accepted markdown output collapses them to a few semantic bullets

## 2.3 Constraints implied by the problem
- We need a new artifact boundary for structured PDF renders; prompt phrasing alone will not make the current renderer preserve layout-rich structure.
- The new boundary must coexist with the meaning-first graph rather than replace it.
- We need an explicit policy for unsupported PDFs: either limited-fidelity mode with surfaced gaps or a fail-loud ingest error.

<!-- arch_skill:block:research_grounding:start -->
# 3) Research Grounding (external + internal “ground truth”)

## 3.1 External anchors (papers, systems, prior art)
- Docling README + `DocumentConverter` / pipeline docs — **adopt as the primary candidate** for the structured-render boundary because it supports local execution, Markdown / HTML / lossless JSON export, OCR, and explicit image-export pipeline options that map cleanly onto this plan's render-manifest goal.
- PyMuPDF4LLM API + README — **adopt as the comparison baseline and possible thinner path** for simpler born-digital PDFs because it exposes direct Markdown output, page chunks, OCR controls, and image-writing options; **do not assume it as the default** because it is more Markdown-first than document-model-first and carries AGPL/commercial licensing.
- Marker README — **reject as the default in-core renderer for now** because, despite strong output claims, it adds PyTorch/model-stack weight plus GPL/model-license considerations that are disproportionate for this repo's currently thin Python core; keep it benchmark-only if later needed.
- MarkItDown README — **reject as the primary renderer** because its own documentation says it targets Markdown for text-analysis pipelines and may not be the best option for high-fidelity human-facing conversions.
- pdfplumber + PyMuPDF low-level extraction docs — **adopt only as debugging / QA anchors**, not as the primary architecture, because they provide geometry, tables, text blocks, and HTML / RAWDICT detail but would push us toward rebuilding a converter pipeline by hand.

## 3.2 Internal ground truth (code as spec)
- Authoritative behavior anchors (do not reinvent):
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `KnowledgeRepository.apply_save(...)` is the authoritative ingest boundary; `_persist_source_records(...)` copies the raw PDF and writes an adjacent `.record.json`, but it does not persist any structured render artifact today.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `_persist_provenance_notes(...)` records `source_reading_modes`, `reading_gaps`, and source-record paths in markdown frontmatter, but there is no field for render path, converter identity, OCR mode, or fidelity mode.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `_write_save_receipt(...)`, `trace(...)`, and `status(...)` already expose path-based observability surfaces; those are the natural places to extend with render-manifest and fidelity metadata instead of inventing a new reporting channel.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` — `_apply_topic_actions(...)` turns knowledge units into section bullets and hands page rendering to `render_page(...)`, proving that semantic topic pages are intentionally meaning-first and cannot become high-fidelity PDF mirrors without violating the current layer boundary.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` — `render_page(...)` only emits a title, `##` headings, section lines, and provenance refs; this is the direct technical reason that current accepted markdown artifacts flatten rich PDFs.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py` — `validate_save_decision(...)` is the authoritative save-contract validator for caller-owned semantic decisions; if render metadata ever becomes caller-supplied it must be added here, but the v1 target architecture keeps render metadata repository-owned to avoid duplicate writers.
  - `/Users/agents/workspace/fleki/src/knowledge_graph/frontmatter.py` — `dump_frontmatter(...)` and `split_frontmatter(...)` define the repo's current markdown-metadata pattern and should be reused for any markdown-backed render or provenance artifact instead of inventing a second metadata style.
  - `/Users/agents/workspace/fleki/tests/test_source_families.py` — current test coverage proves source-family placement and reading-mode labeling for PDFs, images, and runtime artifacts, but it does not prove structural fidelity.
  - `/Users/agents/workspace/fleki/tests/test_save.py` — current save tests prove the raw-source + provenance + topic + receipt pipeline and give us the existing seam to extend for render-artifact persistence.
  - `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` — current search / trace / status tests prove the path-citation and authority-aware retrieval surface that should later surface render artifacts instead of bypassing those commands.
  - `/Users/agents/workspace/fleki/tests/test_rebuild.py` — current rebuild behavior already treats source preservation and semantic reorganization as separate concerns, which supports the plan's goal of keeping renders as supporting artifacts while semantic pages remain reorganizable.
  - `/Users/agents/workspace/fleki/tests/common.py` — `make_temp_repo()` and `sample_save_decision(...)` are the existing lightweight harness for isolated repository tests; we should extend that harness for PDF fidelity checks instead of creating a bespoke testing framework.
  - `/Users/agents/workspace/fleki/docs/CROSS_AGENT_MARKDOWN_WIKI_SYSTEM_2026-04-02.md` — the prior architecture plan explicitly did not promise perfect PDF fidelity, so this plan is a real architecture extension, not a bugfix hidden inside existing doctrine.
  - `/Users/agents/workspace/agents/agents/agent_writer/artifacts/drive_inbox/2026-02-25/Communication_Guidelines.pdf` and `/Users/agents/workspace/agents/agents/agent_ux_analyst/artifacts/2026-03-05_learning_to_intent_mockup_packet.pdf` are the real current-host corpus that exposed the flattening problem and must remain the acceptance corpus.
  - Repo scan result: there is currently **no** `pyproject.toml`, `requirements.txt`, `setup.py`, `uv.lock`, or `poetry.lock` in this repo root, so introducing a converter dependency is not a trivial no-op; packaging and install posture are part of the architecture.
- Existing patterns to reuse:
  - Adjacent raw-artifact plus manifest pairing under `knowledge/sources/**`.
  - Relative-path citation surfaces in provenance, trace, and receipts rather than embedded opaque blobs.
  - JSON frontmatter for markdown artifacts via `dump_frontmatter(...)`.
  - Layer separation between raw source, provenance note, semantic topic, and receipt.
  - Authority-aware search / trace behavior rather than raw-source-first browsing.

## 3.3 Open questions from research
- Does the Docling-vs-PyMuPDF4LLM bake-off on the two real target PDFs confirm the current v1 assumption that Docling is the shipped runtime engine? — evidence needed: one local side-by-side render evaluation before implementation hardens the dependency choice.
- What smallest stable structural assertions from the communication guide and learning-to-intent packet will prove fidelity gains without turning tests into brittle goldens? — evidence needed: phase-plan fixture design against heading continuity, nested-list preservation, and referenced-image markers.
<!-- arch_skill:block:research_grounding:end -->

<!-- arch_skill:block:external_research:start -->
# External Research (best-in-class references; plan-adjacent)

> Goal: anchor the plan in idiomatic, broadly accepted practices where applicable. This section intentionally avoids project-specific internals.

## Topics researched (and why)
- Turnkey local PDF-to-markdown converters — the plan needs an existing library boundary instead of a custom parser.
- OCR and image-preserving export support — the target corpus includes embedded mockups and may later include scanned PDFs, so fidelity mode must be explicit.
- Low-level extraction libraries — the plan may need a narrow debugging or fallback aid, but should avoid rebuilding a full converter by hand.

## Findings + how we apply them

### Turnkey local PDF-to-markdown converters
- Best practices (synthesized):
  - Prefer libraries that can emit Markdown plus a richer structured representation, instead of Markdown alone.
  - Prefer local execution and inspectable outputs over cloud-only conversion paths.
  - Treat broad "convert anything to Markdown" tools cautiously when their own docs say they are not optimized for high-fidelity human-facing conversion.
- Recommended default for this plan:
  - Use **Docling** as the primary candidate for the structured PDF render boundary during `deep-dive` and the first implementation pass.
  - Keep **PyMuPDF4LLM** as the lightweight benchmark and possible fallback candidate for born-digital PDFs where a thinner dependency surface matters more than maximum structure fidelity.
  - Reject **MarkItDown** as the primary renderer for this plan.
  - Keep **Marker** as an optional benchmark only, not the default in-core dependency.
- Pitfalls / footguns:
  - Docling brings a larger pipeline surface than the current repo and can grow expensive when OCR, pictures, or table structure are all enabled.
  - PyMuPDF4LLM is materially lighter, but its abstraction is still Markdown-first and less expressive than a richer document model.
  - Marker's code and model licensing plus PyTorch/model-stack weight are a poor default fit for this repo's currently dependency-light, local-first Python core.
  - MarkItDown explicitly does not position itself as the best choice for high-fidelity document conversion for human consumption.
- Sources:
  - Docling GitHub README — https://github.com/docling-project/docling — authoritative project README; confirms Markdown / HTML / lossless JSON export, local execution, OCR support, and MIT license.
  - Docling `DocumentConverter` reference — https://docling-project.github.io/docling/reference/document_converter/ — authoritative API entry point for a local conversion boundary.
  - PyMuPDF4LLM docs — https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html — authoritative API for direct PDF-to-Markdown export with page chunks, OCR, image handling, and table options.
  - PyMuPDF4LLM GitHub README — https://github.com/pymupdf/pymupdf4llm — authoritative project README; confirms Markdown extraction focus, image extraction, page chunks, and AGPL/commercial license posture.
  - Marker GitHub README — https://github.com/datalab-to/marker — authoritative project README; confirms Markdown / JSON / HTML output, image extraction, LLM mode, PyTorch requirement, and GPL / model-license constraints.
  - MarkItDown GitHub README — https://github.com/microsoft/markitdown — authoritative project README; confirms broad Markdown conversion scope and explicitly warns it may not be the best option for high-fidelity human-facing conversions.

### OCR and image-preserving export support
- Best practices (synthesized):
  - Keep OCR explicit and off by default for born-digital PDFs; enable it only when the document class actually requires it.
  - Prefer referenced image export over embedding base64 blobs into stored Markdown artifacts.
  - Record render configuration and fidelity mode in manifest metadata so trace and provenance stay honest.
- Recommended default for this plan:
  - Use **referenced image export** for stored structured renders rather than embedded image payloads.
  - Prefer **Docling** when page, figure, or table images must be preserved alongside Markdown, because it already exposes image export modes and PDF pipeline options.
  - Preserve **PyMuPDF4LLM** as a lighter benchmark path because it can write image files and include Markdown references, but not as the first architecture choice for rich visual packets.
- Pitfalls / footguns:
  - OCR materially increases latency and operational complexity.
  - Embedded image payloads will bloat stored Markdown and make repo inspection harder.
  - A single "high-fidelity" label is misleading unless the manifest records OCR use, image export mode, and declared gaps.
- Sources:
  - Docling figure export example — https://docling-project.github.io/docling/examples/export_figures/ — authoritative example for page / figure / table image export and Markdown / HTML image-reference modes.
  - Docling pipeline options — https://docling-project.github.io/docling/reference/pipeline_options/ — authoritative options for OCR, table structure, timeout, and backend-text behavior.
  - PyMuPDF4LLM API — https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html — authoritative options for `write_images`, `embed_images`, `use_ocr`, and page-chunk output.

### Low-level extraction libraries
- Best practices (synthesized):
  - Keep low-level PDF extraction libraries as debugging, QA, or targeted-helper surfaces, not as the primary Markdown renderer when the product goal is high-fidelity structured output.
  - If a low-level library is used, consume page geometry, words, images, and tables as supporting data, not as a reason to rebuild a full converter pipeline in-house.
- Recommended default for this plan:
  - Use **pdfplumber** only as a targeted inspection / QA helper if `deep-dive` finds a need for table or layout debugging.
  - If we need a thinner internal debugging surface, prefer **PyMuPDF** page dictionaries / HTML / RAWDICT outputs over ad hoc `pdftotext` heuristics.
  - Do not plan a homegrown Markdown reconstruction layer on top of low-level coordinates as the primary architecture.
- Pitfalls / footguns:
  - Building our own Markdown reconstructor from low-level objects recreates the exact scope that the user wants us to avoid.
  - Low-level extraction can be accurate for specific tables or blocks while still failing to produce a coherent whole-document markdown artifact.
- Sources:
  - pdfplumber GitHub README — https://github.com/jsvine/pdfplumber — authoritative project README; confirms text, layout, coordinates, and table extraction, but not high-level Markdown rendering.
  - PyMuPDF `TextPage` docs — https://pymupdf.readthedocs.io/en/latest/textpage.html — authoritative low-level text / HTML / JSON / RAWDICT extraction surface.
  - PyMuPDF text extraction appendix — https://pymupdf.readthedocs.io/en/latest/app1.html — authoritative details on extraction modes and performance tradeoffs.

## Adopt / Reject summary
- Adopt:
  - Prefer **Docling** as the primary PDF render engine candidate, with Markdown output plus manifest-backed metadata and referenced images where needed.
  - Keep **PyMuPDF4LLM** as the direct comparison baseline and possible thinner fallback path for simple born-digital PDFs.
  - Make OCR explicit and configuration-backed, not ambient.
  - Add manifest fields that record converter identity, converter version, OCR mode, image export mode, and declared fidelity gaps.
- Reject:
  - Do not use **MarkItDown** as the default renderer for this plan because its own docs position it as a broad Markdown conversion utility, not a best-in-class high-fidelity PDF converter.
  - Do not use **Marker** as the default in-core dependency unless later benchmarking proves a decisive fidelity win that justifies GPL/model-license and PyTorch-stack costs.
  - Do not build a homegrown markdown reconstructor on top of **pdfplumber** or other low-level libraries as the primary design.

## Open questions (ONLY if truly not answerable)
- Does Docling materially outperform PyMuPDF4LLM on the two real target PDFs enough to justify the heavier dependency surface? — evidence needed: one side-by-side local bake-off on the communication guide and the learning-to-intent packet using the same evaluation rubric.
- Which smallest subset of Docling-native metadata must be normalized into `.render.manifest.json` so trace and provenance stay useful without persisting a second converter-native artifact? — evidence needed: phase-plan field cut for the manifest schema.
<!-- arch_skill:block:external_research:end -->

<!-- arch_skill:block:current_architecture:start -->
# 4) Current Architecture (as-is)

## 4.1 On-disk structure
- For copied PDFs, `_persist_source_records(...)` writes the raw artifact to `knowledge/sources/pdf/<safe_source_id>__<safe_name>.pdf` and an adjacent `...pdf.record.json` manifest. That manifest is the only machine-readable source metadata surface for PDFs today.
- For pointer-preserved or `secret_pointer_only` sources, the repository writes `...pointer.json` plus the same `.record.json` manifest shape; no render or redacted derivative exists.
- PDF provenance notes live under `knowledge/provenance/pdf/<provenance_id>.md` with frontmatter pointing back to `.record.json` paths, plus a markdown body limited to summary text supplied by the caller.
- Semantic pages live under `knowledge/topics/**.md` and store `knowledge_id`, `section_ids`, `section_support`, and authority posture, but the body only contains normalized `#` / `##` sections plus bullet statements.
- Save, search, trace, and status receipts live under `knowledge/receipts/**`. `knowledge/assets/` exists in the repo layout, but the current PDF ingest path never writes to it.

## 4.2 Control paths (runtime)
1. The caller reads the local PDF directly and builds a semantic `decision` payload plus `source_reading_reports`.
2. `KnowledgeRepository.apply_save(...)` validates only the semantic decision contract; there is no repository-owned PDF render phase and no caller-supplied render contract.
3. `_persist_source_records(...)` copies or pointers the raw PDF and writes the adjacent source manifest.
4. `_persist_provenance_notes(...)` writes provenance markdown with reading modes, gaps, and source-record references, but no render references or converter metadata.
5. `_apply_topic_actions(...)` writes meaning-first topic pages through `render_page(...)`.
6. `_write_save_receipt(...)` records raw-source, provenance, and semantic-page outputs only.
7. `trace(...)` can walk semantic page -> provenance -> source record. It cannot point to a structured PDF render because none exists.
8. `status(...)` aggregates rebuild queues, reading limits, and helper usage from save receipts. It has no notion of render eligibility, fidelity, or omission reasons.

## 4.3 Object model + key abstractions
- `SourceBinding` owns source path, source kind, authority tier, preserve mode, and sensitivity. It has no field for derived render state or render eligibility.
- `validate_save_decision(...)` enforces the semantic save contract only: ingest summary, source-reading reports, provenance notes, topic actions, conflicts, asset actions, and next step. The caller cannot declare a canonical render artifact today.
- `READING_MODES` distinguishes text, PDF, image, and multimodal reading, but not whether a PDF gained a structured render or why one was omitted.
- `render_page(...)` and `parse_sections(...)` intentionally model semantic pages, not source-faithful document renders.
- `_render_provenance_body(...)` only knows summary sections, so even provenance notes cannot currently present a structured-render bundle.

## 4.4 Observability + failure behavior today
- Missing source paths and schema-invalid decisions fail early, before any writes.
- After raw source persistence begins, the save path is not transactional: a later failure can leave copied sources or provenance files behind because there is no rollback boundary.
- A successful save can only report `saved_raw_sources`, `saved_source_records`, provenance paths, touched topics, and reading limitations. It cannot distinguish `rendered faithfully`, `render omitted for sensitivity`, or `render failed`.
- Operators can only discover PDF flattening by manually opening the raw PDF and comparing it to the semantic topic page or provenance note.
- Because `trace(...)` only returns source-record manifest paths, callers must inspect files manually to infer anything about the raw PDF; there is no first-class formatted artifact to inspect.

## 4.5 UI surfaces (ASCII mockups, if UI work)
- No dedicated UI is in scope.
- The real operator surfaces today are:
  - the `knowledge/**` filesystem layout
  - `knowledge trace` payloads
  - `knowledge status` payloads
  - the `knowledge` skill contract, which still tells the agent to inspect PDFs directly and treats semantic filing as the primary output
<!-- arch_skill:block:current_architecture:end -->

<!-- arch_skill:block:target_architecture:start -->
# 5) Target Architecture (to-be)

## 5.1 On-disk structure (future)
- Keep the raw PDF source bundle adjacent under `knowledge/sources/pdf/`; do not move PDF derivatives into `knowledge/assets/` in v1.
- Each render-eligible copied PDF gets one source-adjacent render bundle:

```text
knowledge/sources/pdf/
|-- <source>.pdf
|-- <source>.pdf.record.json
|-- <source>.render.md
|-- <source>.render.manifest.json
`-- <source>.assets/
```

- `.pdf.record.json` remains the source-layer SSOT for raw artifact identity, capture metadata, sensitivity, storage mode, and pointers to any derived render bundle.
- `.render.manifest.json` becomes the only SSOT for derived-render facts: engine id/version, fidelity mode, OCR mode, image-export mode, declared gaps, page count, anchor hints, and asset list.
- `.render.md` is the canonical human-inspectable formatted artifact; v1 does not persist a second converter-native JSON document into the graph unless the plan is revised.
- Pointer-only or `secret_pointer_only` PDFs do not get `.render.md` or `.assets/`; their `.pdf.record.json` must instead record an explicit omission reason such as `disallowed_by_sensitivity`.

## 5.2 Control paths (future)
1. `KnowledgeRepository.apply_save(...)` remains the single authoritative ingest entrypoint; there is no separate runtime conversion service and no caller-written render manifest.
2. During source persistence, every render-eligible copied PDF runs through one local shipped render engine: **Docling**. PyMuPDF4LLM remains bake-off evidence only until the doc is explicitly revised.
3. The render step emits `.render.md`, `.render.manifest.json`, and optional referenced assets before provenance notes, semantic topic pages, or save receipts are written.
4. For render-eligible PDFs, failure to materialize at least a declared `high_fidelity` or `limited_fidelity` render bundle aborts the save before provenance/topic writes. There is no raw-only success path for eligible copied PDFs.
5. For pointer-only or secret PDFs, the repository skips render generation, records `render_eligibility = false` plus an explicit omission reason, and never claims structured fidelity.
6. Provenance notes and save receipts mirror selected render fields and paths, but they only reference the render manifest; they do not become a second full render contract.
7. Semantic topic generation remains meaning-first and keeps using `render_page(...)`; topic pages may cite render-backed provenance, but they do not embed full PDF transcriptions or page images.
8. `trace(...)` becomes the canonical inspection surface for the chain `semantic topic -> provenance note -> source record -> structured render / omission reason`.
9. `apply_rebuild(...)` continues to move semantic topic pages only; source-adjacent render bundles stay pinned to source records and are not rehomed by topic-path changes.

## 5.3 Object model + abstractions (future)
- Introduce one repository-owned PDF render boundary, implemented as a narrow helper module (for example `src/knowledge_graph/pdf_render.py`) rather than a pluggable engine framework.
- That boundary returns a single `PdfRenderBundle`-style payload with:
  - `render_eligible`
  - `omission_reason`
  - `engine_id`
  - `engine_version`
  - `fidelity_mode` (`high_fidelity` or `limited_fidelity`)
  - `render_relative_path`
  - `render_manifest_relative_path`
  - `asset_relative_paths`
  - `ocr_mode`
  - `image_export_mode`
  - `page_count`
  - `anchor_hints`
  - `declared_gaps`
  - `source_sha256`
- Source-record manifests store pointer-level fields into that bundle such as `render_manifest_relative_path`, `render_relative_path`, `render_eligibility`, and `render_omission_reason`, but the detailed fidelity contract lives only in `.render.manifest.json`.
- Provenance frontmatter mirrors only decision-relevant subsets per source, for example:
  - `render_manifest_paths`
  - `render_paths`
  - `render_fidelity_by_source`
  - `render_gaps_by_source`
  - `render_omissions_by_source`
- Save receipts mirror only summary subsets, for example:
  - `saved_render_manifests`
  - `saved_renders`
  - `limited_fidelity_sources`
  - `render_omitted_sources`
- `trace(...)` grows direct `render_manifests` and `render_artifacts` outputs so callers no longer have to discover the bundle indirectly through source manifests.
- The caller-owned semantic `decision` schema stays meaning-first in v1. Render metadata is repository-owned and must not become a second caller-written contract.

## 5.4 Invariants and boundaries
- One runtime engine ships in v1: Docling. There is no runtime engine switch, plugin interface, or fallback converter path unless this plan is revised and the Decision Log records it.
- For copied PDFs that are eligible for render storage, `apply_save(...)` either writes the render bundle and declares a fidelity mode or fails before semantic artifacts are persisted.
- Pointer-only and `secret_pointer_only` PDFs never persist rendered content; their omission reason is explicit and traceable.
- The raw-source manifest and render manifest are separate SSOT layers. Provenance, trace, and receipts may mirror selected fields but must never invent or override render state.
- `.render.md` is a supporting evidence artifact, not a new browse model. Semantic topics remain the primary organized knowledge surface.
- Extracted images are file references stored beside the PDF render bundle; base64 payloads in markdown or frontmatter are forbidden.
- Pre-feature PDFs are out of scope for this feature; v1 only guarantees render bundles for PDFs ingested through the new path and does not promise bulk backfill.
- If the Docling bake-off fails to outperform the baseline sufficiently on the two acceptance PDFs, the plan must be revised before implementation rather than shipping a dual-engine compromise.

## 5.5 UI surfaces (ASCII mockups, if UI work)
- No viewer redesign is in scope.
- The intended operator-visible trace shape becomes:

```text
topic page -> provenance note -> source record manifest -> render manifest -> render markdown (+ assets)
```

- For ineligible sensitive PDFs, the same path ends with an explicit omission reason instead of a render artifact.
<!-- arch_skill:block:target_architecture:end -->

<!-- arch_skill:block:call_site_audit:start -->
# 6) Call-Site Audit (exhaustive change inventory)

## 6.1 Change map (table)

| Area | File | Symbol / Call site | Current behavior | Required change | Why | New API / contract | Tests impacted |
| ---- | ---- | ------------------ | ---------------- | --------------- | --- | ------------------ | -------------- |
| Packaging / install surface | `/Users/agents/workspace/fleki/pyproject.toml` or equivalent new repo-owned dependency file | repo dependency entrypoint | No Python dependency scaffold exists in this repo | Add one minimal install surface for the shipped PDF renderer and test dependencies; do not introduce multiple competing installers | Docling cannot land as a real dependency through ad hoc local state | one repo-owned dependency definition for `knowledge_graph` + PDF-render extras | all Python tests and local smoke setup |
| PDF render boundary | `/Users/agents/workspace/fleki/src/knowledge_graph/pdf_render.py` (new) | new render helper | No repository-owned PDF renderer exists | Add the Docling-backed render-bundle writer that emits `.render.md`, `.render.manifest.json`, referenced assets, or an explicit omission result | High-fidelity preservation needs one canonical writer | `PdfRenderBundle` / render-manifest contract | new `test_pdf_rendering.py`, `test_source_families.py` |
| Ingest orchestration | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `apply_save` | validate -> source record -> provenance -> topic -> receipt | Insert render-bundle creation after source persistence and gate later writes on eligible-PDF render success | The fail-loud fidelity boundary must happen before semantic artifacts are written | `apply_save` orchestrates raw-source + render-bundle + semantic writes | `test_save.py`, `test_search_trace_status.py` |
| Source persistence / manifests | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_persist_source_records` plus new internal helper | Writes raw copy or pointer plus `.record.json` only | Extend the source manifest with render pointers, eligibility, and omission fields; keep the render manifest as the derived-data SSOT | Operators need machine-readable linkage from source records to render bundles without duplicating the full render contract | source-record pointer fields into `.render.manifest.json` | `test_source_families.py`, `test_save.py` |
| Provenance metadata and body | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_persist_provenance_notes`, `_render_provenance_body` | Records reading modes and gaps only | Add render paths, fidelity or omission summaries, and a structured-render section in the markdown body | Provenance is the human-readable explanation surface for why the render can be trusted or omitted | provenance frontmatter mirrors selected render fields only | `test_save.py`, `test_pdf_rendering.py` |
| Receipt and inspection surfaces | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` | `_write_save_receipt`, `trace`, `status` | Save, trace, and status know nothing about renders | Surface saved renders, render manifests, limited-fidelity counts, and omission reasons where truthful | Users need one truthful inspection path for PDF fidelity | extended `save`, `trace`, and `status` payload fields | `test_save.py`, `test_search_trace_status.py` |
| Semantic page renderer boundary | `/Users/agents/workspace/fleki/src/knowledge_graph/text.py` | `render_page`, `parse_sections` | Semantic-only output with no explicit boundary guard | Keep behavior meaning-first and add a boundary comment or narrow test expectation so this layer is not overloaded into a PDF renderer | The architecture only works if semantic pages stay semantic | no new PDF-render responsibilities in `text.py` | existing semantic tests if touched |
| Shared contract constants | `/Users/agents/workspace/fleki/src/knowledge_graph/authority.py` | new fidelity / omission constants | No shared constants exist for render fidelity or omission reasons | Add canonical enums/constants for render fidelity and render omission reasons | Prevent string drift across manifests, receipts, provenance, and tests | `PDF_RENDER_FIDELITY_MODES`, `PDF_RENDER_OMISSION_REASONS` | contract tests and repository tests |
| Save validation boundary | `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py` | `validate_save_decision` | Validates semantic decision only and implicitly tolerates unknown extra fields | Keep the semantic save contract unchanged, but explicitly reject caller-owned render metadata blocks if introduced | One writer must own render metadata; the repository is that writer | no caller-supplied `pdf_render` or `render_manifest` contract in `decision` | `test_contracts.py` |
| Typed model surface | `/Users/agents/workspace/fleki/src/knowledge_graph/models.py` | new render dataclass(es) if used | Only source bindings and rebuild models are typed today | Add a small typed object for the render bundle if implementation chooses typed returns over ad hoc dicts | The new boundary is sharp enough to deserve one shared shape | `PdfRenderBundle` or equivalent | repository tests and new render tests |
| Skill contract | `/Users/agents/workspace/fleki/skills_or_tools/knowledge/SKILL.md` and `/Users/agents/workspace/fleki/.agents/skills/knowledge/SKILL.md` | `knowledge save` guidance | The skill describes direct PDF inspection and semantic filing, but not persisted render bundles or omission rules | Update the public contract to explain render-backed PDF saves, sensitive-source omission rules, and traceable fidelity reporting | User-facing behavior must match the architecture | revised PDF save / trace contract | doc verification and live smoke |
| Shared test harness | `/Users/agents/workspace/fleki/tests/common.py` | repo fixture helpers | Only text-style sample save helpers exist | Add helper fixtures for render-eligible PDF sources and pointer-only PDF cases without creating a new harness framework | Keep tests small and reusable | reusable PDF fixture helpers | all new PDF-render tests |
| PDF source-family coverage | `/Users/agents/workspace/fleki/tests/test_source_families.py` | family placement assertions | Proves PDF, image, and runtime placement only | Extend to assert render-bundle placement for eligible PDFs and explicit omission metadata for pointer-only PDFs | Family coverage should prove the new on-disk contract | source-adjacent render bundle + omission assertions | this file |
| Save flow coverage | `/Users/agents/workspace/fleki/tests/test_save.py` | save integration assertions | Proves raw source, provenance, topic, and receipt writes only | Assert save receipts, provenance, and source manifests expose render fields and fail-loud behavior | Save is the main changed flow | extended save payload and provenance contract | this file |
| Trace / status coverage | `/Users/agents/workspace/fleki/tests/test_search_trace_status.py` | trace and status assertions | Proves provenance/source-record path reporting only | Assert trace returns render bundle paths and status counts fidelity or omission categories | User-visible inspection changes land here | extended trace/status contract | this file |
| New fidelity regression coverage | `/Users/agents/workspace/fleki/tests/test_pdf_rendering.py` (new) | render-bundle contract and structural assertions | No fidelity-specific module exists | Add structure-aware contract tests against stable fixture PDFs or controlled fixtures; use real-PDF smokes outside the unit suite | This plan needs a real fidelity proof without brittle golden files | render manifest + markdown structure assertions | new file |

## 6.2 Migration notes
- Deprecated APIs (if any): none; `apply_save(...)` remains the authoritative write entrypoint.
- Delete list (what must be removed; include superseded shims/parallel paths if any):
  - none in the current repo, but implementation must not ship a runtime engine switch, a second global asset store for PDF-derived files under `knowledge/assets/`, or caller-written render manifests.
- Cleanup notes:
  - Do not add compatibility work or hidden bulk backfill for pre-feature PDFs in this pass.
  - `apply_rebuild(...)` and `tests/test_rebuild.py` should remain largely unchanged because render bundles are source-anchored, not topic-anchored.
  - If implementation uses temporary bake-off scripts, ad hoc export directories, or converter-comparison artifacts, they must be deleted before landing.

## Pattern Consolidation Sweep (anti-blinders; scoped by plan)

| Area | File / Symbol | Pattern to adopt | Why (drift prevented) | Proposed scope (include/defer/exclude) |
| ---- | ------------- | ---------------- | ---------------------- | ------------------------------------- |
| Source artifacts | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` / `_persist_source_records` | source-adjacent derived-artifact bundle with manifest pointers | Keeps raw PDF, render markdown, manifest, and assets in one lifecycle unit instead of scattering files | include |
| Provenance surfaces | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` / `_persist_provenance_notes` | mirror selected render facts, never full-contract duplication | Prevents provenance markdown from becoming a second render SSOT | include |
| Receipt / trace surfaces | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` / `_write_save_receipt`, `trace`, `status` | summary-only render reporting backed by manifest paths | Prevents each command from inventing its own render state vocabulary | include |
| Validation policy | `/Users/agents/workspace/fleki/src/knowledge_graph/validation.py` | single-writer render-metadata rule | Prevents future drift into caller-written render manifests | include |
| Skill contract | `/Users/agents/workspace/fleki/skills_or_tools/knowledge/SKILL.md` | semantic-topic-first plus render-backed evidence chain | Prevents the skill from drifting into raw artifact filing or misleading PDF claims | include |
| Global asset store | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` / `assets_root` | keep PDF-derived assets beside the source bundle instead of reusing `knowledge/assets/` | Prevents dual homes and ambiguous cleanup semantics for PDF assets | exclude |
| Rebuild path | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` / `apply_rebuild` | leave render bundles source-anchored, not topic-anchored | Prevents semantic rehomes from mutating source provenance storage | exclude |
| Other source families | `/Users/agents/workspace/fleki/src/knowledge_graph/repository.py` / image and other-family handling | source-adjacent derived-artifact bundle pattern | Same pattern may help future image or multimodal derivatives, but it would expand scope here | defer |
<!-- arch_skill:block:call_site_audit:end -->

<!-- arch_skill:block:phase_plan:start -->
# 7) Depth-First Phased Implementation Plan (authoritative)

> Rule: systematic build, foundational first; every phase has exit criteria + explicit verification plan (tests optional). No fallbacks/runtime shims - the system must work correctly or fail loudly (delete superseded paths). Prefer programmatic checks per phase; defer manual/UI verification to finalization. Avoid negative-value tests (deletion checks, visual constants, doc-driven gates). Also: document new patterns/gotchas in code comments at the canonical boundary (high leverage, not comment spam).

## Phase 1 — Dependency Surface And Engine Confirmation

Status: COMPLETE

* Goal:
  - Make the dependency/install surface real and confirm that Docling is still the only shipped runtime engine worth integrating.
* Work:
  - Add one minimal repo-owned Python packaging/install surface for the knowledge graph runtime and PDF-render dependencies.
  - Add the narrowest possible comparison path needed to render the two acceptance PDFs with Docling and PyMuPDF4LLM without introducing a reusable dual-engine runtime abstraction.
  - Lock the normalized `.render.manifest.json` field cut needed by provenance, trace, and receipts.
  - Use the acceptance rubric from this plan on `/Users/agents/workspace/agents/agents/agent_writer/artifacts/drive_inbox/2026-02-25/Communication_Guidelines.pdf` and `/Users/agents/workspace/agents/agents/agent_ux_analyst/artifacts/2026-03-05_learning_to_intent_mockup_packet.pdf`.
  - If Docling does not materially clear the bar, stop and reopen the plan instead of continuing toward a dual-engine runtime.
* Verification (smallest signal):
  - The repo can install the chosen dependency surface in a clean environment.
  - Side-by-side outputs exist for both acceptance PDFs and show that Docling preserves the required structure materially better than the baseline.
  - The manifest field cut is fixed without persisting a second converter-native artifact.
* Docs/comments (propagation; only if needed):
  - Add one high-leverage comment at the future `pdf_render.py` boundary explaining raw-source-manifest SSOT vs render-manifest SSOT.
* Exit criteria:
  - The shipped engine decision is confirmed.
  - The manifest schema field cut is locked.
  - No dual-engine runtime abstraction has been introduced.
* Rollback:
  - Remove the new dependency surface and any temporary comparison-only code if Docling fails the gate or the repo cost is unacceptable.
* Completed work:
  - Added a repo-owned `pyproject.toml` with a Python 3.12 packaging surface, Docling as the shipped dependency, and PyMuPDF4LLM as a comparison-only extra.
  - Created a local Python 3.12 virtualenv and installed the repo plus the comparison extra successfully.
  - Ran the acceptance-PDF bake-off on both target files; Docling preserved materially richer heading structure on both, and with `generate_picture_images=True` it also produced referenced image assets for the mockup packet.

## Phase 2 — Source-Adjacent Render Bundle Cutover

Status: COMPLETE

* Goal:
  - Make `apply_save(...)` capable of writing or explicitly omitting the PDF render bundle before any semantic artifacts are persisted.
* Work:
  - Add the repository-owned PDF render boundary, shared fidelity/omission constants, and any small typed bundle object required by the implementation.
  - Implement source-adjacent bundle writing for copied PDFs: `.render.md`, `.render.manifest.json`, and referenced assets beside the raw PDF.
  - Extend `.pdf.record.json` with render pointers, eligibility flags, and omission reasons while keeping `.render.manifest.json` as the derived-render SSOT.
  - Treat pointer-only and `secret_pointer_only` PDFs as render-ineligible with explicit omission metadata.
  - Integrate the render step into `apply_save(...)` so eligible copied PDFs fail before provenance/topic writes if the render bundle cannot be materialized.
  - Keep PDF-derived assets out of `knowledge/assets/` and out of semantic topic pages.
* Verification (smallest signal):
  - Focused repository tests prove that eligible PDFs create the expected source-adjacent render bundle and that pointer-only PDFs record explicit omission metadata instead.
  - A fixture-backed `apply_save(...)` run produces render files and manifest pointers for a copied PDF.
  - No PDF-derived files land under `knowledge/assets/`.
* Docs/comments (propagation; only if needed):
  - Add one comment at the `repository.py` integration point explaining that render generation is the fail-loud boundary before provenance/topic writes.
* Exit criteria:
  - The render bundle contract is live through `apply_save(...)`.
  - Eligibility, omission, and fail-loud rules are enforced.
  - The raw-source and render-manifest SSOT split is reflected on disk.
* Rollback:
  - Revert the save-path cutover and the new render-bundle writer rather than shipping a partial raw-only success path for eligible PDFs.
* Completed work:
  - Added the repository-owned `pdf_render.py` Docling boundary and wired `apply_save(...)` through a fail-loud render-bundle phase before provenance or topic writes.
  - Extended `.record.json` source manifests with `source_family`, render eligibility, render omission reasons, and pointers into the source-adjacent `.render.manifest.json` / `.render.md` bundle.
  - Verified copied PDFs create source-adjacent render bundles, pointer-only PDFs record explicit omission metadata, and PDF-derived files do not land under `knowledge/assets/`.

## Phase 3 — Provenance, Trace, Status, And Contract Hardening

Status: COMPLETE

* Goal:
  - Propagate truthful render state through every caller-visible inspection surface without duplicating the render contract or weakening the semantic-page boundary.
* Work:
  - Extend provenance frontmatter and markdown bodies with render paths, fidelity or omission summaries, and declared gaps.
  - Extend save receipts, `trace(...)`, and `status(...)` with render-manifest paths, render-artifact paths, limited-fidelity summaries, and omission counts where truthful.
  - Keep `render_page(...)` semantic-only and add the smallest boundary guard needed so it is not repurposed into a document renderer.
  - Update validation so caller-owned `decision` payloads cannot start carrying render-manifest fields.
  - Update the `knowledge` skill contract in both canonical publication locations so PDF saves and traces match the new render-backed evidence path.
  - Extend the shared test harness and the affected contract / save / trace / status suites to cover the new surfaces.
* Verification (smallest signal):
  - `python3 -m unittest discover -s tests -p 'test_*.py' -v` passes with the extended suites.
  - `trace(...)` returns render manifest and render artifact paths for eligible PDFs, and explicit omission state for ineligible ones.
  - `status(...)` reports the new fidelity/omission categories for the new PDF render path without inventing unsupported compatibility behavior.
* Docs/comments (propagation; only if needed):
  - Add one comment in `text.py` or the relevant test boundary clarifying that semantic pages remain meaning-first and are not the PDF render layer.
* Exit criteria:
  - Provenance, receipts, trace, status, validation, and skill docs all agree on render truth.
  - Semantic pages remain meaning-first.
  - No duplicate render SSOT has appeared.
* Rollback:
  - Revert the caller-visible metadata extensions and keep the render bundle internal until the surface contract is corrected.
* Completed work:
  - Extended provenance notes, save receipts, `trace(...)`, and `status(...)` so render manifests, render artifacts, and omission reasons now flow from the repository-owned render contract.
  - Hardened validation against caller-owned render metadata and added the semantic-boundary comment in `text.py` so topic pages remain meaning-first.
  - Updated both published `knowledge` skill packages plus the shared test harness and contract/save/trace/status suites to reflect the render-backed PDF path.

## Phase 4 — Real-PDF Acceptance, Cleanup, And Rollout Readiness

Status: COMPLETE

* Goal:
  - Prove the shipped path materially improves fidelity on the acceptance corpus and land a clean, non-experimental implementation state.
* Work:
  - Run the real `save`, `trace`, and `status` flow on the two acceptance PDFs and inspect the stored render bundles.
  - Verify that heading hierarchy, nested lists, and referenced-image or mockup markers are materially better than the current flattened outputs.
  - Remove any temporary comparison-only code, ad hoc export directories, or benchmark artifacts used during Phase 1.
  - Refresh any stale rollout, verification, or skill wording that changed during implementation.
* Verification (smallest signal):
  - `python3 -m unittest discover -s tests -p 'test_*.py' -v` passes.
  - `python3 -m compileall src` passes.
  - One local realistic smoke on both acceptance PDFs shows materially richer stored markdown structure and truthful `trace(...)` / `status(...)` outputs.
* Docs/comments (propagation; only if needed):
  - Update the implementation worklog with the real-PDF acceptance evidence and any remaining known limits.
* Exit criteria:
  - The acceptance corpus passes the fidelity bar.
  - No temporary benchmark helpers or stray comparison artifacts remain.
  - The implementation is ready for `audit-implementation`.
* Rollback:
  - Revert the feature before merge rather than shipping a degraded contract, a dual-engine compromise, or leftover benchmark scaffolding.
* Completed work:
  - Ran the real `save`, `trace`, and `status` flow on `Communication_Guidelines.pdf` and `2026-03-05_learning_to_intent_mockup_packet.pdf` through the shipped repository path.
  - Confirmed materially richer stored markdown structure on the acceptance corpus: 27 heading markers / 4 referenced assets / 4 page breaks for the communication guide, and 41 heading markers / 6 referenced assets / 7 page breaks for the learning-to-intent packet.
  - Cleared the generated repo-local egg-info artifact and finished with a clean Python 3.12 test lane plus passing compile verification.
* Manual QA (non-blocking):
  - Optional human spot-check: open one stored `.render.md` from each acceptance PDF and compare it against the original PDF for subjective fidelity beyond the scripted heading/image/page-break signals.
<!-- arch_skill:block:phase_plan:end -->

# 8) Verification Strategy (common-sense; non-blocking)

- Avoid verification bureaucracy.
- Prefer the smallest existing signal.
- Default to a small set of contract plus flow checks.
- Do not add proof tests for deletions, visual constants, or doc inventories.

## 8.1 Unit tests (contracts)
- Validate render manifest schema, fidelity-mode reporting, and provenance metadata shape.
- Validate that unsupported fidelity paths cannot report full-fidelity success.

## 8.2 Integration tests (flows)
- Start with the Docling vs PyMuPDF4LLM bake-off on the two real target PDFs before treating Docling as the final shipped engine.
- Exercise `save`, `trace`, and `status` for PDF sources with structured render outputs present.
- Verify that structured render paths and fidelity gaps propagate through receipts and provenance.

## 8.3 E2E / device tests (realistic)
- Run at least one realistic local smoke against the two real structured PDFs from `../agents`.
- Compare preserved structure qualitatively against the raw PDFs and, where available, adjacent source markdown.
- If Marker is evaluated at all, treat it as a benchmark-only branch rather than a required shipped dependency.

# 9) Rollout / Ops / Telemetry

## 9.1 Rollout plan
- Ship this as a bounded PDF-path upgrade inside the existing knowledge system rather than a whole-system rewrite.
- Prefer opt-in or explicit scope-limited rollout for PDF ingest first if deep-dive shows significant operational risk.

## 9.2 Telemetry changes
- Receipts and provenance should expose fidelity mode and render availability.
- If status expands, it should do so only with a small truthful surface such as counts of limited-fidelity ingests or render failures.

## 9.3 Operational runbook
- Operators should be able to inspect:
  - the raw PDF source path
  - the structured render path
  - the render manifest
  - any declared fidelity gaps
- Repair steps should prefer re-ingest or explicit failure messages over hidden fallback behavior.

# 10) Decision Log (append-only)

## 2026-04-03 - Plan high-fidelity PDF rendering as a first-class follow-on change

### Context
- The current knowledge architecture intentionally prioritized semantic filing over PDF layout fidelity.
- Local testing on real PDFs from `../agents` showed that accepted markdown artifacts flatten rich structure materially.
- The user explicitly wants the PDF rendering system to preserve as much formatting as possible and points out that better PDF-to-markdown mechanisms exist.

### Options
- Keep the current flow and accept low-fidelity PDF handling as a permanent limitation.
- Try to improve fidelity only through prompt changes while keeping the current artifact layers unchanged.
- Introduce a bounded first-class PDF rendering contract that stores structured renders before semantic condensation.

### Decision
- Create a dedicated architecture plan for the third option and treat PDF fidelity as a real subsystem boundary, not as an incidental prompt tweak.

### Consequences
- This work may introduce a more deterministic PDF extraction boundary than the original LLM-first-only PDF posture.
- The plan must preserve the existing meaning-first graph and avoid turning PDF mirrors into the primary browsing model.
- Research must now compare real PDF rendering mechanisms instead of assuming the current path is sufficient.

### Follow-ups
- Confirm the North Star for this plan.
- Run `research` on viable local PDF-to-markdown or equivalent structural extraction mechanisms.
- Use `deep-dive` to lock storage, provenance, and trace integration boundaries.

## 2026-04-03 - Prefer Docling as the primary library candidate

### Context
- External research was requested specifically to find a neat existing-library approach for higher-fidelity PDF rendering.
- The plan needs a local, inspectable, fail-loud path that can preserve richer structure than the current flattened semantic artifacts.
- The repo currently has no package-management scaffold and a deliberately thin Python core, so dependency weight and license posture matter.

### Options
- Use Docling as the primary structured-render candidate.
- Use PyMuPDF4LLM as the primary structured-render candidate.
- Use Marker as the primary structured-render candidate.
- Use MarkItDown or a low-level library stack as the primary renderer.

### Decision
- Prefer **Docling** as the primary library candidate for the structured render boundary.
- Keep **PyMuPDF4LLM** as the comparison baseline and possible thinner fallback candidate for simpler PDFs.
- Reject **MarkItDown** as the primary renderer for this plan.
- Reject **Marker** as the default in-core choice unless later benchmarking shows a decisive fidelity win that outweighs its license and runtime costs.

### Consequences
- The target architecture can assume an existing document-model-capable converter rather than inventing a custom PDF parser.
- Deep-dive now needs to decide whether to persist only Markdown + manifest or also a richer Docling-side JSON representation.
- Verification should include a real bake-off between Docling and PyMuPDF4LLM on the two target PDFs.

### Follow-ups
- Use `deep-dive` to wire the converter recommendation into storage, manifest, provenance, and trace boundaries.
- Keep license and dependency posture explicit if implementation later evaluates Marker despite the default rejection.

## 2026-04-03 - Lock the render-bundle contract and single-engine runtime

### Context
- Research and local inspection proved that the current PDF path preserves raw files but not structure-rich accepted markdown artifacts.
- The repo already has a strong adjacent-artifact pattern for raw sources and manifests, but no equivalent derived-render contract.
- The system already supports pointer-only and `secret_pointer_only` sources, so any PDF render plan must respect that sensitivity boundary instead of accidentally copying sensitive content into markdown.

### Options
- Put all render metadata into the existing `.pdf.record.json` source manifest and avoid a second manifest.
- Add a dedicated render manifest beside the raw PDF and mirror only selected fields into provenance, receipts, and trace.
- Support multiple runtime engines or a switchable converter abstraction from the first implementation pass.
- Ship one runtime engine and require a plan revision before any later engine swap.

### Decision
- Keep `.pdf.record.json` as the raw-source SSOT and add a separate `.render.manifest.json` as the derived-render SSOT.
- Store the canonical `.render.md` and any extracted assets adjacent to the raw PDF under `knowledge/sources/pdf/`; do not reuse `knowledge/assets/` for this bundle in v1.
- Ship **Docling** as the single planned runtime engine in v1. PyMuPDF4LLM remains bake-off evidence only and does not justify a dual-engine runtime contract.
- Treat pointer-only and `secret_pointer_only` PDFs as render-ineligible in this pass. They keep explicit omission metadata and must never claim structured-fidelity success.
- Keep caller-owned `decision` payloads meaning-first; render metadata is repository-owned and must not become a second caller-written contract.

### Consequences
- The implementation can stay narrowly scoped around one new render helper and one render-manifest schema instead of inventing a plugin system.
- Trace, provenance, and receipts can report render state truthfully without duplicating the entire render contract.
- Pre-feature PDFs are out of scope for this feature; no compatibility or backfill behavior is promised here.

### Follow-ups
- Use `phase-plan` to sequence packaging, render-helper creation, repository integration, contract updates, and verification.
- Keep the Docling-vs-PyMuPDF4LLM bake-off as a pre-implementation check, not a shipped runtime abstraction.

## 2026-04-03 - Do not treat pre-feature PDFs as a supported compatibility target

### Context
- During the implementation audit, the plan still carried stale language about reporting or supporting legacy pre-render PDFs.
- The user clarified that this is a brand-new feature and should not carry legacy-support requirements.
- The shipped implementation is designed around the new ingest path and already proves the render contract on newly ingested PDFs.

### Options
- Keep legacy-pre-feature PDF counting and compatibility expectations in scope for this feature.
- Remove legacy-support expectations from the plan and audit the feature against the new ingest path only.

### Decision
- Remove legacy-support and legacy-count expectations from this plan.
- Audit completeness against the new PDF render path only; pre-feature PDFs are explicitly out of scope unless a later plan adds migration or backfill work.

### Consequences
- The implementation audit does not treat missing pre-feature PDF compatibility behavior as a blocker.
- The plan now matches the user's scope clarification and the shipped new-path evidence.
- Any future migration or backfill for old PDFs requires a separate explicit plan.

### Follow-ups
- If old PDFs ever need render bundles, create a separate migration/backfill plan instead of extending this feature implicitly.
- If the bake-off disproves Docling as the right shipped engine, the plan must be revised before implementation instead of accumulating a compatibility layer.

## 2026-04-03 - Sequence engine confirmation before save-path cutover

### Context
- The target architecture already assumes Docling is the only shipped runtime engine, but external research still leaves one evidence question: whether Docling materially clears the acceptance corpus better than PyMuPDF4LLM.
- The repo currently has no packaging surface, so even the comparison step requires a real dependency decision.
- The prior placeholder phase outline was too coarse to make the bake-off an explicit gate.

### Options
- Integrate the save path first and leave the Docling-vs-PyMuPDF4LLM comparison until late verification.
- Run the engine comparison first, then cut over the save path only after the shipped engine decision is confirmed.

### Decision
- Make dependency setup plus the Docling-vs-PyMuPDF4LLM bake-off the first implementation phase.
- Treat a failed Docling bake-off as a plan-reopen event, not as a reason to ship a dual-engine runtime or a soft fallback.

### Consequences
- Phase 1 now owns both dependency setup and engine confirmation.
- Save-path integration does not begin until the shipped engine and manifest field cut are confirmed.
- The authoritative execution order is now explicit enough for `implement` to follow without guessing.

### Follow-ups
- Keep the comparison path as narrow and disposable as possible.
- Delete any temporary comparison-only helper or export artifact before implementation is considered complete.

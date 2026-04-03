from __future__ import annotations

import contextlib
import importlib.metadata
import io
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable

from .models import PdfRenderBundle


class PdfRenderError(RuntimeError):
    pass


INLINE_LIST_MARKER_RE = re.compile(r"(?<=\S)\s+(?=(?:\d+\.\s+|[-*]\s+))")
INLINE_SECTION_MARKER_RE = re.compile(
    r"(?<=\S)\s+(?=(?:Section|Sections|Chapter|Part|Appendix|Example|Examples|Notes?|Summary|Overview):\s)"
)


@lru_cache(maxsize=1)
def _docling_converter():
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    options = PdfPipelineOptions()
    options.do_ocr = False
    options.generate_picture_images = True
    options.images_scale = 2.0

    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def _anchor_hints(markdown_text: str) -> tuple[str, ...]:
    headings = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading = stripped.lstrip("#").strip()
        if heading:
            headings.append(heading)
        if len(headings) >= 12:
            break
    if headings:
        return tuple(headings)

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped:
            return (stripped[:120],)
    return ()


def _cleanup_empty_dirs(path: Path) -> None:
    if not path.exists():
        return
    if any(path.iterdir()):
        return
    path.rmdir()


def _rewrite_asset_paths(markdown_text: str, *, asset_dir: Path) -> str:
    if not asset_dir.exists():
        return markdown_text
    relative_asset_dir = Path(asset_dir.name).as_posix()
    absolute_asset_dir = asset_dir.resolve().as_posix()
    rewritten = markdown_text.replace(absolute_asset_dir, relative_asset_dir)

    # Some exporters emit absolute file URIs or repeated separators; normalize them.
    rewritten = rewritten.replace(f"file://{absolute_asset_dir}", relative_asset_dir)
    rewritten = rewritten.replace(f"({absolute_asset_dir}/", f"({relative_asset_dir}/")
    return rewritten


def _render_artifact_paths(raw_pdf_path: Path) -> tuple[Path, Path, Path]:
    return (
        raw_pdf_path.with_suffix(".render.md"),
        raw_pdf_path.with_suffix(".render.manifest.json"),
        raw_pdf_path.with_suffix(".assets"),
    )


def _relative_paths(root: Path, paths: Iterable[Path]) -> tuple[str, ...]:
    return tuple(path.relative_to(root).as_posix() for path in paths)


def _run_quietly(callback: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        return callback(*args, **kwargs)


def _restore_markdown_structure(markdown_text: str) -> str:
    blocks = markdown_text.split("\n\n")
    restored_blocks: list[str] = []
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            restored_blocks.append("")
            continue
        if stripped.startswith(("#", "|", "```", "![", "<!--")):
            restored_blocks.append(block)
            continue

        rewritten = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if re.match(r"^(?:\d+\.\s+|[-*]\s+)", rewritten):
            rewritten = INLINE_LIST_MARKER_RE.sub("\n", rewritten)
        rewritten = INLINE_SECTION_MARKER_RE.sub("\n", rewritten)
        restored_blocks.append(rewritten)
    return "\n\n".join(restored_blocks)


def render_pdf_bundle(
    *,
    root: Path | str,
    raw_pdf_path: Path | str,
    source_id: str,
    source_sha256: str,
    timestamp: str,
) -> PdfRenderBundle:
    root_path = Path(root)
    raw_path = Path(raw_pdf_path)
    render_path, manifest_path, assets_dir = _render_artifact_paths(raw_path)

    try:
        from docling_core.types.doc import ImageRefMode
        from docling.datamodel.base_models import ConversionStatus
    except ImportError as exc:
        raise PdfRenderError("docling is required for PDF render bundle generation") from exc

    converter = _run_quietly(_docling_converter)
    result = _run_quietly(converter.convert, raw_path)
    if result.status != ConversionStatus.SUCCESS:
        raise PdfRenderError(
            f"docling conversion failed for {raw_path.name}: {result.status!s}"
        )

    render_path.parent.mkdir(parents=True, exist_ok=True)

    # Raw-source manifests own identity and storage mode; render manifests own derived-render facts.
    _run_quietly(
        result.document.save_as_markdown,
        render_path,
        artifacts_dir=assets_dir,
        image_mode=ImageRefMode.REFERENCED,
        page_break_placeholder="<!-- page break -->",
        escape_html=False,
    )

    markdown_text = render_path.read_text()
    markdown_text = _rewrite_asset_paths(markdown_text, asset_dir=assets_dir)
    markdown_text = _restore_markdown_structure(markdown_text)
    render_path.write_text(markdown_text)

    if not markdown_text.strip():
        raise PdfRenderError(f"docling produced an empty markdown render for {raw_path.name}")

    asset_paths = tuple(sorted(path for path in assets_dir.rglob("*") if path.is_file())) if assets_dir.exists() else ()
    if not asset_paths:
        _cleanup_empty_dirs(assets_dir)

    render_relative_path = render_path.relative_to(root_path).as_posix()
    asset_relative_paths = _relative_paths(root_path, asset_paths)
    manifest_relative_path = manifest_path.relative_to(root_path).as_posix()

    manifest_payload = {
        "source_id": source_id,
        "source_sha256": source_sha256,
        "engine_id": "docling",
        "engine_version": importlib.metadata.version("docling"),
        "fidelity_mode": "high_fidelity",
        "render_format": "markdown",
        "render_relative_path": render_relative_path,
        "asset_relative_paths": list(asset_relative_paths),
        "ocr_mode": "disabled",
        "image_export_mode": "referenced_picture_assets",
        "page_count": len(result.pages),
        "anchor_hints": list(_anchor_hints(markdown_text)),
        "declared_gaps": [],
        "created_at": timestamp,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True))

    return PdfRenderBundle(
        source_id=source_id,
        render_eligible=True,
        engine_id="docling",
        engine_version=manifest_payload["engine_version"],
        fidelity_mode="high_fidelity",
        render_relative_path=render_relative_path,
        render_manifest_relative_path=manifest_relative_path,
        asset_relative_paths=asset_relative_paths,
        ocr_mode="disabled",
        image_export_mode="referenced_picture_assets",
        page_count=manifest_payload["page_count"],
        anchor_hints=tuple(manifest_payload["anchor_hints"]),
        declared_gaps=(),
        source_sha256=source_sha256,
    )

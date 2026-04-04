from __future__ import annotations

import posixpath
import re
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from ..frontmatter import dump_frontmatter, split_frontmatter
from ..ids import safe_filename
from ..repository import KnowledgeRepository
from ..text import parse_sections
from .layout import resolve_review_wiki_layout


GRAPH_REF_RE = re.compile(r"`([^`\n]+?\.md)`")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")


@dataclass(frozen=True)
class ExportFile:
    relative_path: str
    content: bytes

    @classmethod
    def from_text(cls, relative_path: str, text: str) -> ExportFile:
        return cls(relative_path=relative_path, content=text.encode("utf-8"))

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")


@dataclass(frozen=True)
class ExportSnapshot:
    files: tuple[ExportFile, ...]


@dataclass(frozen=True)
class _SourcePage:
    kind: str
    graph_relative_path: str
    export_relative_path: str
    title: str
    metadata: Mapping[str, Any]
    body: str


@dataclass(frozen=True)
class _ExportBundle:
    snapshot: ExportSnapshot
    topic_pages: tuple[str, ...]
    provenance_pages: tuple[str, ...]
    artifact_pages_by_source: Mapping[str, str]


def build_export_snapshot(repository: KnowledgeRepository) -> ExportSnapshot:
    return _build_export_bundle(repository).snapshot


def export_review_wiki(
    repository: KnowledgeRepository,
    destination_root: Path | str | None = None,
) -> dict[str, Any]:
    repository.initialize_layout()
    content_root = (
        Path(destination_root)
        if destination_root is not None
        else resolve_review_wiki_layout(repository.layout).content_root
    )
    bundle = _build_export_bundle(repository)
    materialize_export_snapshot(bundle.snapshot, content_root)
    return {
        "content_root": str(content_root),
        "topic_pages": list(bundle.topic_pages),
        "provenance_pages": list(bundle.provenance_pages),
        "artifact_pages_by_source": dict(bundle.artifact_pages_by_source),
        "exported_files": [export_file.relative_path for export_file in bundle.snapshot.files],
    }


def materialize_export_snapshot(snapshot: ExportSnapshot, content_root: Path) -> None:
    content_root.mkdir(parents=True, exist_ok=True)
    expected_paths = set()
    for export_file in snapshot.files:
        target = content_root / export_file.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(export_file.content)
        expected_paths.add(target.resolve())

    if not content_root.exists():
        return
    for path in sorted(content_root.rglob("*"), reverse=True):
        resolved = path.resolve()
        if path.is_file() and resolved not in expected_paths:
            path.unlink()
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                continue


def _build_export_bundle(repository: KnowledgeRepository) -> _ExportBundle:
    repository.initialize_layout()
    pages = _collect_source_pages(repository.data_root)
    pages_by_graph_path = {page.graph_relative_path: page for page in pages}
    topics_by_current_path = {
        str(page.metadata["current_path"]): page
        for page in pages
        if page.kind == "topic" and page.metadata.get("current_path")
    }
    provenance_map = repository._load_provenance_map()
    artifact_summaries = _collect_artifact_summaries(repository, provenance_map)
    artifact_pages = _artifact_pages_by_source(artifact_summaries)

    topic_pages: list[str] = []
    provenance_pages: list[str] = []
    exports_by_path: dict[str, bytes] = {}

    def add_export(export_file: ExportFile) -> None:
        existing = exports_by_path.get(export_file.relative_path)
        if existing is not None:
            if existing != export_file.content:
                raise ValueError(f"conflicting export content for {export_file.relative_path}")
            return
        exports_by_path[export_file.relative_path] = export_file.content

    for export_file in _build_summary_pages(pages):
        add_export(export_file)

    for page in pages:
        rendered = _render_export_page(
            repository=repository,
            page=page,
            pages_by_graph_path=pages_by_graph_path,
            topics_by_current_path=topics_by_current_path,
            provenance_map=provenance_map,
            artifact_summaries=artifact_summaries,
            artifact_pages=artifact_pages,
        )
        add_export(ExportFile.from_text(page.export_relative_path, rendered))
        if page.kind == "topic":
            topic_pages.append(page.export_relative_path)
        elif page.kind == "provenance":
            provenance_pages.append(page.export_relative_path)

    for source_id, artifact in artifact_summaries.items():
        artifact_page = artifact_pages[source_id]
        add_export(
            ExportFile.from_text(
                artifact_page.as_posix(),
                dump_frontmatter(
                    _artifact_page_metadata(artifact),
                    _render_artifact_body(artifact=artifact, artifact_relative_path=artifact_page),
                ),
            )
        )
        for export_file in _build_artifact_files(repository, artifact):
            add_export(export_file)

    exported_files = tuple(
        ExportFile(relative_path=relative_path, content=content)
        for relative_path, content in sorted(exports_by_path.items())
    )
    return _ExportBundle(
        snapshot=ExportSnapshot(files=exported_files),
        topic_pages=tuple(sorted(topic_pages)),
        provenance_pages=tuple(sorted(provenance_pages)),
        artifact_pages_by_source={source_id: path.as_posix() for source_id, path in artifact_pages.items()},
    )


def _collect_source_pages(data_root: Path) -> List[_SourcePage]:
    pages: List[_SourcePage] = []
    pages.extend(_scan_markdown_tree(data_root / "topics", data_root, topic_mode=True))
    pages.extend(_scan_markdown_tree(data_root / "provenance", data_root, topic_mode=False))
    return pages


def _scan_markdown_tree(root: Path, data_root: Path, *, topic_mode: bool) -> List[_SourcePage]:
    pages: List[_SourcePage] = []
    if not root.exists():
        return pages
    for path in sorted(root.rglob("*.md")):
        if path.name == "README.md":
            continue
        metadata, body = split_frontmatter(path.read_text())
        title, _ = parse_sections(body)
        graph_relative_path = path.relative_to(data_root).as_posix()
        if topic_mode and path.is_relative_to(root / "indexes"):
            export_relative_path = Path("indexes") / path.relative_to(root / "indexes")
            kind = "index"
        elif topic_mode:
            export_relative_path = Path("topics") / path.relative_to(root)
            kind = "topic"
        else:
            export_relative_path = Path("provenance") / path.relative_to(root)
            kind = "provenance"
        pages.append(
            _SourcePage(
                kind=kind,
                graph_relative_path=graph_relative_path,
                export_relative_path=export_relative_path.as_posix(),
                title=title,
                metadata=metadata,
                body=body,
            )
        )
    return pages


def _build_summary_pages(pages: Sequence[_SourcePage]) -> List[ExportFile]:
    topic_pages = [page for page in pages if page.kind == "topic"]
    index_pages = [page for page in pages if page.kind == "index"]
    provenance_pages = [page for page in pages if page.kind == "provenance"]

    topic_domains = sorted(
        {page.export_relative_path.split("/", 2)[1] for page in topic_pages if "/" in page.export_relative_path}
    )
    provenance_families = sorted(
        {page.export_relative_path.split("/", 2)[1] for page in provenance_pages if "/" in page.export_relative_path}
    )

    return [
        ExportFile.from_text(
            "index.md",
            dump_frontmatter(
                {"title": "Fleki Knowledge Review", "publish": True},
                "\n".join(
                    [
                        "# Fleki Knowledge Review",
                        "",
                        "Human-readable review site for the live Fleki knowledge graph.",
                        "",
                        "## Browse",
                        f"- [Topics](topics) ({len(topic_pages)} pages)",
                        f"- [Indexes](indexes) ({len(index_pages)} pages)",
                        f"- [Provenance](provenance) ({len(provenance_pages)} notes)",
                        "",
                    ]
                ),
            ),
        ),
        ExportFile.from_text(
            "topics/index.md",
            dump_frontmatter(
                {"title": "Topics", "publish": True},
                "\n".join(
                    [
                        "# Topics",
                        "",
                        "Browse semantic topics by domain.",
                        "",
                        *[f"- [{_humanize_slug(domain)}]({domain})" for domain in topic_domains],
                        "",
                    ]
                ),
            ),
        ),
        ExportFile.from_text(
            "indexes/index.md",
            dump_frontmatter(
                {"title": "Indexes", "publish": True},
                "\n".join(
                    [
                        "# Indexes",
                        "",
                        "Browse generated navigation pages.",
                        "",
                        *[
                            f"- [{page.title}]({_relative_page_href('indexes/index.md', page.export_relative_path)})"
                            for page in index_pages
                        ],
                        "",
                    ]
                ),
            ),
        ),
        ExportFile.from_text(
            "provenance/index.md",
            dump_frontmatter(
                {"title": "Provenance", "publish": True},
                "\n".join(
                    [
                        "# Provenance",
                        "",
                        "Browse supporting notes grouped by source family.",
                        "",
                        *[f"- [{_humanize_slug(family)}]({family})" for family in provenance_families],
                        "",
                    ]
                ),
            ),
        ),
    ]


def _render_export_page(
    *,
    repository: KnowledgeRepository,
    page: _SourcePage,
    pages_by_graph_path: Mapping[str, _SourcePage],
    topics_by_current_path: Mapping[str, _SourcePage],
    provenance_map: Mapping[str, Mapping[str, Any]],
    artifact_summaries: Mapping[str, Mapping[str, Any]],
    artifact_pages: Mapping[str, PurePosixPath],
) -> str:
    metadata = _export_frontmatter(page)
    body = _rewrite_graph_refs(page.body, page.export_relative_path, pages_by_graph_path)
    body = _rewrite_topic_path_refs(body, page.export_relative_path, topics_by_current_path)
    if page.kind == "provenance":
        body = _append_connected_topics(body, page, topics_by_current_path)

    source_ids: list[str] = []
    if page.kind == "topic":
        source_ids = _source_ids_for_topic(repository, page, provenance_map, artifact_summaries)
        body = _inject_artifact_section(
            body,
            source_ids=source_ids,
            artifact_pages=artifact_pages,
            page_relative_path=PurePosixPath(page.export_relative_path),
            keep_provenance_last=True,
        )
    elif page.kind == "provenance":
        source_ids = [
            str(source_id)
            for source_id in page.metadata.get("source_ids", [])
            if str(source_id) in artifact_summaries
        ]
        body = _inject_artifact_section(
            body,
            source_ids=source_ids,
            artifact_pages=artifact_pages,
            page_relative_path=PurePosixPath(page.export_relative_path),
            keep_provenance_last=False,
        )

    return dump_frontmatter(metadata, body)


def _export_frontmatter(page: _SourcePage) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "title": page.title,
        "publish": True,
    }
    if page.kind == "topic":
        metadata.update(
            _without_none(
                {
                    "page_kind": page.metadata.get("page_kind"),
                    "knowledge_id": page.metadata.get("knowledge_id"),
                    "current_path": page.metadata.get("current_path"),
                    "aliases": list(page.metadata.get("aliases", [])),
                    "authority_posture": page.metadata.get("authority_posture"),
                    "lifecycle_state": page.metadata.get("lifecycle_state"),
                    "last_supported_at": page.metadata.get("last_supported_at"),
                    "last_updated_at": page.metadata.get("last_updated_at"),
                }
            )
        )
        modified = page.metadata.get("last_reorganized_at") or page.metadata.get("last_updated_at")
        if modified:
            metadata["modified"] = modified
    elif page.kind == "provenance":
        created = page.metadata.get("created_at")
        metadata.update(
            _without_none(
                {
                    "page_kind": "provenance",
                    "provenance_id": page.metadata.get("provenance_id"),
                    "source_ids": list(page.metadata.get("source_ids", [])),
                    "created_at": created,
                    "created": created,
                    "modified": created,
                }
            )
        )
    elif page.kind == "index":
        generated = page.metadata.get("generated_at")
        if generated:
            metadata["modified"] = generated
    return metadata


def _rewrite_graph_refs(
    body: str,
    from_export_relative_path: str,
    pages_by_graph_path: Mapping[str, _SourcePage],
) -> str:
    lines = body.splitlines()
    rewritten: List[str] = []
    in_code_block = False
    for line in lines:
        if line.startswith("```"):
            in_code_block = not in_code_block
            rewritten.append(line)
            continue
        if in_code_block:
            rewritten.append(line)
            continue
        rewritten.append(
            GRAPH_REF_RE.sub(
                lambda match: _graph_ref_replacement(
                    match.group(1),
                    from_export_relative_path=from_export_relative_path,
                    pages_by_graph_path=pages_by_graph_path,
                ),
                line,
            )
        )
    return "\n".join(rewritten).rstrip() + "\n"


def _graph_ref_replacement(
    graph_reference: str,
    *,
    from_export_relative_path: str,
    pages_by_graph_path: Mapping[str, _SourcePage],
) -> str:
    normalized_reference = graph_reference.removeprefix("knowledge/")
    target_page = pages_by_graph_path.get(normalized_reference)
    if target_page is None:
        return f"`{graph_reference}`"
    return f"[{target_page.title}]({_relative_page_href(from_export_relative_path, target_page.export_relative_path)})"


def _append_connected_topics(
    body: str,
    page: _SourcePage,
    topics_by_current_path: Mapping[str, _SourcePage],
) -> str:
    touched = page.metadata.get("knowledge_sections_touched", [])
    if not isinstance(touched, list):
        return body

    rendered_links = []
    seen = set()
    for item in touched:
        if not isinstance(item, MappingABC):
            continue
        topic_path = item.get("topic_path")
        if not isinstance(topic_path, str) or topic_path in seen:
            continue
        seen.add(topic_path)
        topic_page = topics_by_current_path.get(topic_path)
        if topic_page is None:
            continue
        rendered_links.append(
            f"- [{topic_page.title}]({_relative_page_href(page.export_relative_path, topic_page.export_relative_path)})"
        )

    if not rendered_links:
        return body

    lines = [body.rstrip(), "", "## Connected Topics", *rendered_links, ""]
    return "\n".join(lines)


def _rewrite_topic_path_refs(
    body: str,
    from_export_relative_path: str,
    topics_by_current_path: Mapping[str, _SourcePage],
) -> str:
    lines = body.splitlines()
    rewritten: List[str] = []
    in_code_block = False
    for line in lines:
        if line.startswith("```"):
            in_code_block = not in_code_block
            rewritten.append(line)
            continue
        if in_code_block:
            rewritten.append(line)
            continue
        rewritten.append(
            CODE_SPAN_RE.sub(
                lambda match: _topic_path_replacement(
                    match.group(1),
                    from_export_relative_path=from_export_relative_path,
                    topics_by_current_path=topics_by_current_path,
                ),
                line,
            )
        )
    return "\n".join(rewritten).rstrip() + "\n"


def _topic_path_replacement(
    value: str,
    *,
    from_export_relative_path: str,
    topics_by_current_path: Mapping[str, _SourcePage],
) -> str:
    topic_page = topics_by_current_path.get(value)
    if topic_page is None:
        return f"`{value}`"
    return f"[{topic_page.title}]({_relative_page_href(from_export_relative_path, topic_page.export_relative_path)})"


def _inject_artifact_section(
    body: str,
    *,
    source_ids: Iterable[str],
    artifact_pages: Mapping[str, PurePosixPath],
    page_relative_path: PurePosixPath,
    keep_provenance_last: bool,
) -> str:
    title, sections = parse_sections(body)
    sections.pop("Artifacts", None)
    provenance_lines = list(sections.pop("Provenance Notes", [])) if keep_provenance_last else []

    lines: list[str] = [f"# {title}", ""]
    for heading, section_lines in sections.items():
        lines.append(f"## {heading}")
        if section_lines:
            lines.extend(section_lines)
        else:
            lines.append("- Pending content")
        lines.append("")

    artifact_lines = _artifact_section_lines(
        source_ids=source_ids,
        artifact_pages=artifact_pages,
        page_relative_path=page_relative_path,
    )
    if artifact_lines:
        lines.append("## Artifacts")
        lines.extend(artifact_lines)
        lines.append("")

    if keep_provenance_last and provenance_lines:
        lines.append("## Provenance Notes")
        lines.extend(provenance_lines)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _artifact_section_lines(
    *,
    source_ids: Iterable[str],
    artifact_pages: Mapping[str, PurePosixPath],
    page_relative_path: PurePosixPath,
) -> list[str]:
    lines: list[str] = []
    for source_id in source_ids:
        artifact_relative_path = artifact_pages.get(source_id)
        if artifact_relative_path is None:
            continue
        lines.append(
            f"- [{source_id}]({_relative_page_href(page_relative_path, artifact_relative_path)})"
        )
    return lines


def _collect_artifact_summaries(
    repository: KnowledgeRepository,
    provenance_map: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    source_record_paths = _dedupe_preserve_order(
        [
            str(relative_path)
            for provenance_entry in sorted(
                provenance_map.values(),
                key=lambda item: item["relative_path"],
            )
            for relative_path in provenance_entry["metadata"].get("source_record_paths", [])
        ]
    )
    manifests = repository._load_source_record_manifests(source_record_paths)
    artifact_summaries: dict[str, dict[str, Any]] = {}
    for source_record, manifest in manifests.items():
        source_id = str(manifest.get("source_id") or "")
        if not source_id:
            continue
        artifact_summary = repository._artifact_summary_from_manifest(
            source_record=source_record,
            manifest=manifest,
        )
        artifact_summary["source_id"] = source_id
        existing = artifact_summaries.get(source_id)
        if existing is not None and existing != artifact_summary:
            raise ValueError(f"conflicting artifact summaries for source_id {source_id}")
        artifact_summaries[source_id] = artifact_summary
    return artifact_summaries


def _artifact_pages_by_source(
    artifact_summaries: Mapping[str, Mapping[str, Any]],
) -> dict[str, PurePosixPath]:
    paths: dict[str, PurePosixPath] = {}
    claimed_names: dict[str, str] = {}
    for source_id in sorted(artifact_summaries):
        artifact_name = f"{safe_filename(source_id)}.md"
        claimed_by = claimed_names.get(artifact_name)
        if claimed_by is not None and claimed_by != source_id:
            raise ValueError(f"artifact page name collision between {claimed_by} and {source_id}")
        claimed_names[artifact_name] = source_id
        paths[source_id] = PurePosixPath("artifacts") / artifact_name
    return paths


def _source_ids_for_topic(
    repository: KnowledgeRepository,
    page: Mapping[str, Any],
    provenance_map: Mapping[str, Mapping[str, Any]],
    artifact_summaries: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    source_ids: list[str] = []
    for provenance_id in repository._supporting_provenance_for_section(
        page_metadata=page.metadata,
        section_id=None,
    ):
        provenance_entry = provenance_map.get(provenance_id)
        if provenance_entry is None:
            continue
        for source_id in provenance_entry["metadata"].get("source_ids", []):
            source_id_value = str(source_id)
            if source_id_value not in artifact_summaries:
                continue
            if source_id_value not in source_ids:
                source_ids.append(source_id_value)
    return source_ids


def _artifact_page_metadata(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return _without_none(
        {
            "title": f"Artifact - {artifact['source_id']}",
            "publish": True,
            "page_kind": "artifact",
            "source_id": artifact.get("source_id"),
            "source_family": artifact.get("source_family"),
            "source_kind": artifact.get("source_kind"),
            "sensitivity": artifact.get("sensitivity"),
            "storage_mode": artifact.get("storage_mode"),
            "primary_artifact_kind": artifact.get("primary_artifact_kind"),
            "captured_at": artifact.get("captured_at"),
            "source_observed_at": artifact.get("source_observed_at"),
        }
    )


def _render_artifact_body(
    *,
    artifact: Mapping[str, Any],
    artifact_relative_path: PurePosixPath,
) -> str:
    source_id = str(artifact["source_id"])
    lines = [
        f"# Artifact - {source_id}",
        "",
        "## Summary",
        f"- Source family: `{artifact['source_family']}`",
        f"- Source kind: `{artifact['source_kind']}`",
        f"- Sensitivity: `{artifact['sensitivity']}`",
        f"- Storage mode: `{artifact['storage_mode']}`",
        f"- Captured at: `{artifact['captured_at']}`",
    ]
    if artifact.get("source_observed_at"):
        lines.append(f"- Source observed at: `{artifact['source_observed_at']}`")
    if artifact.get("sha256"):
        lines.append(f"- SHA256: `{artifact['sha256']}`")
    lines.extend(["", "## Primary Artifact"])

    primary_artifact_path = PurePosixPath("files") / str(artifact["primary_artifact_path"])
    lines.append(
        f"- [Open preserved artifact]({_relative_file_href(artifact_relative_path, primary_artifact_path)})"
    )
    if artifact["primary_artifact_kind"] == "pointer_record":
        lines.append("- Raw copied content is not stored for `secret_pointer_only`.")
    lines.append("")

    render_links = _render_link_lines(artifact_relative_path, artifact)
    if render_links:
        lines.append("## PDF Render")
        lines.extend(render_links)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_link_lines(
    artifact_relative_path: PurePosixPath,
    artifact: Mapping[str, Any],
) -> list[str]:
    lines: list[str] = []
    render_markdown_path = artifact.get("render_markdown_path")
    if render_markdown_path:
        lines.append(
            f"- [Render markdown]({_relative_file_href(artifact_relative_path, PurePosixPath('files') / str(render_markdown_path))})"
        )
    render_manifest_path = artifact.get("render_manifest_path")
    if render_manifest_path:
        lines.append(
            f"- [Render manifest]({_relative_file_href(artifact_relative_path, PurePosixPath('files') / str(render_manifest_path))})"
        )
    for asset_path in artifact.get("render_asset_paths", []):
        lines.append(
            f"- [Render asset `{asset_path}`]({_relative_file_href(artifact_relative_path, PurePosixPath('files') / str(asset_path))})"
        )
    omission_reason = artifact.get("render_omission_reason")
    if omission_reason:
        lines.append(f"- Render omitted: `{omission_reason}`")
    contract_gap = artifact.get("render_contract_gap")
    if contract_gap:
        lines.append(f"- Render contract gap: `{contract_gap}`")
    return lines


def _build_artifact_files(
    repository: KnowledgeRepository,
    artifact: Mapping[str, Any],
) -> list[ExportFile]:
    export_files = [
        _build_artifact_file(repository, str(artifact["primary_artifact_path"])),
    ]
    render_markdown_path = artifact.get("render_markdown_path")
    if render_markdown_path:
        export_files.append(_build_artifact_file(repository, str(render_markdown_path)))
    render_manifest_path = artifact.get("render_manifest_path")
    if render_manifest_path:
        export_files.append(_build_artifact_file(repository, str(render_manifest_path)))
    for asset_path in artifact.get("render_asset_paths", []):
        export_files.append(_build_artifact_file(repository, str(asset_path)))
    return export_files


def _build_artifact_file(repository: KnowledgeRepository, graph_relative_path: str) -> ExportFile:
    source_path = repository.data_root / graph_relative_path
    if not source_path.exists():
        raise FileNotFoundError(f"missing artifact file for export: {source_path}")
    export_relative_path = PurePosixPath("files") / graph_relative_path
    return ExportFile(relative_path=export_relative_path.as_posix(), content=source_path.read_bytes())


def _relative_page_href(
    from_export_relative_path: str | PurePosixPath,
    to_export_relative_path: str | PurePosixPath,
) -> str:
    from_dir = PurePosixPath(str(from_export_relative_path)).parent
    target = PurePosixPath(str(to_export_relative_path))
    if target.name == "index.md":
        target = target.parent
    else:
        target = target.with_suffix("")
    if str(target) == ".":
        return "."
    return posixpath.relpath(str(target), str(from_dir) or ".")


def _relative_file_href(
    from_export_relative_path: PurePosixPath,
    to_export_relative_path: PurePosixPath,
) -> str:
    return posixpath.relpath(
        to_export_relative_path.as_posix(),
        start=from_export_relative_path.parent.as_posix(),
    )


def _humanize_slug(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()


def _without_none(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metadata.items()
        if value is not None and value != []
    }


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered

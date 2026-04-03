from __future__ import annotations

import json
import posixpath
import shutil
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, List, Mapping

from ..ids import safe_filename
from ..repository import KnowledgeRepository
from ..text import parse_sections


def export_review_wiki(
    repository: KnowledgeRepository,
    destination_root: Path | str | None = None,
) -> dict[str, Any]:
    repository.initialize_layout()
    content_root = (
        Path(destination_root)
        if destination_root is not None
        else repository.state_root / "review-wiki" / "content"
    )
    if content_root.exists():
        shutil.rmtree(content_root)
    content_root.mkdir(parents=True, exist_ok=True)

    topics = sorted(
        repository._load_topics(),
        key=lambda page: page["metadata"]["current_path"],
    )
    provenance_map = repository._load_provenance_map()
    artifact_summaries = _collect_artifact_summaries(repository, provenance_map)
    artifact_pages_by_source = _artifact_pages_by_source(artifact_summaries)
    exported_files: set[str] = set()

    for source_id, artifact in artifact_summaries.items():
        _export_artifact_files(
            repository=repository,
            content_root=content_root,
            artifact=artifact,
            exported_files=exported_files,
        )
        artifact_relative_path = artifact_pages_by_source[source_id]
        _write_markdown_page(
            content_root / _native_path(artifact_relative_path),
            metadata=_artifact_page_metadata(artifact),
            body=_render_artifact_body(
                artifact=artifact,
                artifact_relative_path=artifact_relative_path,
            ),
        )

    exported_topic_pages: list[str] = []
    for page in topics:
        topic_relative_path = PurePosixPath("topics") / f"{page['metadata']['current_path']}.md"
        topic_artifacts = _source_ids_for_topic(repository, page, provenance_map, artifact_summaries)
        _write_markdown_page(
            content_root / _native_path(topic_relative_path),
            metadata=_topic_page_metadata(page),
            body=_render_topic_body(
                page=page,
                source_ids=topic_artifacts,
                artifact_pages_by_source=artifact_pages_by_source,
                page_relative_path=topic_relative_path,
            ),
        )
        exported_topic_pages.append(topic_relative_path.as_posix())

    exported_provenance_pages: list[str] = []
    for provenance_entry in sorted(
        provenance_map.values(),
        key=lambda item: item["relative_path"],
    ):
        provenance_relative_path = PurePosixPath(provenance_entry["relative_path"])
        provenance_source_ids = [
            str(source_id)
            for source_id in provenance_entry["metadata"].get("source_ids", [])
            if source_id in artifact_summaries
        ]
        _write_markdown_page(
            content_root / _native_path(provenance_relative_path),
            metadata=_provenance_page_metadata(provenance_entry),
            body=_render_provenance_body(
                provenance_entry=provenance_entry,
                source_ids=provenance_source_ids,
                artifact_pages_by_source=artifact_pages_by_source,
                page_relative_path=provenance_relative_path,
            ),
        )
        exported_provenance_pages.append(provenance_relative_path.as_posix())

    return {
        "content_root": str(content_root),
        "topic_pages": exported_topic_pages,
        "provenance_pages": exported_provenance_pages,
        "artifact_pages_by_source": {
            source_id: relative_path.as_posix()
            for source_id, relative_path in artifact_pages_by_source.items()
        },
        "exported_files": sorted(exported_files),
    }


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
        page_metadata=page["metadata"],
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


def _render_topic_body(
    *,
    page: Mapping[str, Any],
    source_ids: Iterable[str],
    artifact_pages_by_source: Mapping[str, PurePosixPath],
    page_relative_path: PurePosixPath,
) -> str:
    title, sections = parse_sections(str(page["body"]))
    provenance_lines = list(sections.pop("Provenance Notes", []))
    sections.pop("Artifacts", None)
    return _render_page_body(
        title=title,
        sections=sections,
        source_ids=source_ids,
        artifact_pages_by_source=artifact_pages_by_source,
        page_relative_path=page_relative_path,
        provenance_lines=provenance_lines,
    )


def _render_provenance_body(
    *,
    provenance_entry: Mapping[str, Any],
    source_ids: Iterable[str],
    artifact_pages_by_source: Mapping[str, PurePosixPath],
    page_relative_path: PurePosixPath,
) -> str:
    title, sections = parse_sections(str(provenance_entry["body"]))
    sections.pop("Artifacts", None)
    return _render_page_body(
        title=title,
        sections=sections,
        source_ids=source_ids,
        artifact_pages_by_source=artifact_pages_by_source,
        page_relative_path=page_relative_path,
        provenance_lines=(),
    )


def _render_page_body(
    *,
    title: str,
    sections: Mapping[str, List[str]],
    source_ids: Iterable[str],
    artifact_pages_by_source: Mapping[str, PurePosixPath],
    page_relative_path: PurePosixPath,
    provenance_lines: Iterable[str],
) -> str:
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
        artifact_pages_by_source=artifact_pages_by_source,
        page_relative_path=page_relative_path,
    )
    if artifact_lines:
        lines.append("## Artifacts")
        lines.extend(artifact_lines)
        lines.append("")

    trailing_provenance = list(provenance_lines)
    if trailing_provenance:
        lines.append("## Provenance Notes")
        lines.extend(trailing_provenance)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _artifact_section_lines(
    *,
    source_ids: Iterable[str],
    artifact_pages_by_source: Mapping[str, PurePosixPath],
    page_relative_path: PurePosixPath,
) -> list[str]:
    lines: list[str] = []
    for source_id in source_ids:
        artifact_relative_path = artifact_pages_by_source.get(source_id)
        if artifact_relative_path is None:
            continue
        artifact_link = _relative_link(page_relative_path, artifact_relative_path)
        lines.append(f"- [{source_id}]({artifact_link})")
    return lines


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
        f"- [Open preserved artifact]({_relative_link(artifact_relative_path, primary_artifact_path)})"
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
            f"- [Render markdown]({_relative_link(artifact_relative_path, PurePosixPath('files') / str(render_markdown_path))})"
        )
    render_manifest_path = artifact.get("render_manifest_path")
    if render_manifest_path:
        lines.append(
            f"- [Render manifest]({_relative_link(artifact_relative_path, PurePosixPath('files') / str(render_manifest_path))})"
        )
    for asset_path in artifact.get("render_asset_paths", []):
        lines.append(
            f"- [Render asset `{asset_path}`]({_relative_link(artifact_relative_path, PurePosixPath('files') / str(asset_path))})"
        )
    omission_reason = artifact.get("render_omission_reason")
    if omission_reason:
        lines.append(f"- Render omitted: `{omission_reason}`")
    contract_gap = artifact.get("render_contract_gap")
    if contract_gap:
        lines.append(f"- Render contract gap: `{contract_gap}`")
    return lines


def _export_artifact_files(
    *,
    repository: KnowledgeRepository,
    content_root: Path,
    artifact: Mapping[str, Any],
    exported_files: set[str],
) -> None:
    _copy_export_file(
        repository=repository,
        content_root=content_root,
        graph_relative_path=str(artifact["primary_artifact_path"]),
        exported_files=exported_files,
    )
    render_markdown_path = artifact.get("render_markdown_path")
    if render_markdown_path:
        _copy_export_file(
            repository=repository,
            content_root=content_root,
            graph_relative_path=str(render_markdown_path),
            exported_files=exported_files,
        )
    render_manifest_path = artifact.get("render_manifest_path")
    if render_manifest_path:
        _copy_export_file(
            repository=repository,
            content_root=content_root,
            graph_relative_path=str(render_manifest_path),
            exported_files=exported_files,
        )
    for asset_path in artifact.get("render_asset_paths", []):
        _copy_export_file(
            repository=repository,
            content_root=content_root,
            graph_relative_path=str(asset_path),
            exported_files=exported_files,
        )


def _copy_export_file(
    *,
    repository: KnowledgeRepository,
    content_root: Path,
    graph_relative_path: str,
    exported_files: set[str],
) -> None:
    source_path = repository.data_root / graph_relative_path
    if not source_path.exists():
        raise FileNotFoundError(f"missing artifact file for export: {source_path}")
    export_relative_path = PurePosixPath("files") / graph_relative_path
    destination_path = content_root / _native_path(export_relative_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)
    exported_files.add(export_relative_path.as_posix())


def _topic_page_metadata(page: Mapping[str, Any]) -> dict[str, Any]:
    metadata = page["metadata"]
    return _without_none(
        {
            "title": page["title"],
            "page_kind": metadata.get("page_kind"),
            "knowledge_id": metadata.get("knowledge_id"),
            "current_path": metadata.get("current_path"),
            "aliases": list(metadata.get("aliases", [])),
            "authority_posture": metadata.get("authority_posture"),
            "lifecycle_state": metadata.get("lifecycle_state"),
            "last_supported_at": metadata.get("last_supported_at"),
            "last_updated_at": metadata.get("last_updated_at"),
        }
    )


def _provenance_page_metadata(provenance_entry: Mapping[str, Any]) -> dict[str, Any]:
    metadata = provenance_entry["metadata"]
    title, _ = parse_sections(str(provenance_entry["body"]))
    return _without_none(
        {
            "title": title,
            "page_kind": "provenance",
            "provenance_id": metadata.get("provenance_id"),
            "source_ids": list(metadata.get("source_ids", [])),
            "created_at": metadata.get("created_at"),
        }
    )


def _artifact_page_metadata(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return _without_none(
        {
            "title": f"Artifact - {artifact['source_id']}",
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


def _write_markdown_page(path: Path, *, metadata: Mapping[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml_frontmatter(metadata, body))


def _dump_yaml_frontmatter(metadata: Mapping[str, Any], body: str) -> str:
    yaml_lines = _yaml_lines(metadata)
    body_text = body.lstrip("\n")
    return f"---\n{chr(10).join(yaml_lines)}\n---\n{body_text}"


def _yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, Mapping):
                if item:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_yaml_lines(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {{}}")
                continue
            if isinstance(item, list):
                if item:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_yaml_lines(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: []")
                continue
            lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, Mapping):
                lines.append(f"{prefix}-")
                lines.extend(_yaml_lines(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return json.dumps(value)
    return json.dumps(str(value))


def _relative_link(from_relative_path: PurePosixPath, to_relative_path: PurePosixPath) -> str:
    return posixpath.relpath(
        to_relative_path.as_posix(),
        start=from_relative_path.parent.as_posix(),
    )


def _native_path(path: PurePosixPath) -> Path:
    return Path(*path.parts)


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

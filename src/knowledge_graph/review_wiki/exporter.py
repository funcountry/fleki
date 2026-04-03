from __future__ import annotations

import posixpath
import re
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Sequence

from ..frontmatter import dump_frontmatter, split_frontmatter
from ..repository import KnowledgeRepository
from ..text import parse_sections


GRAPH_REF_RE = re.compile(r"`([^`\n]+?\.md)`")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")


@dataclass(frozen=True)
class ExportFile:
    relative_path: str
    text: str


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


def build_export_snapshot(repository: KnowledgeRepository) -> ExportSnapshot:
    repository.initialize_layout()
    pages = _collect_source_pages(repository.data_root)
    pages_by_graph_path = {
        page.graph_relative_path: page for page in pages
    }
    topics_by_current_path = {
        page.metadata["current_path"]: page
        for page in pages
        if page.kind == "topic"
    }

    exported: List[ExportFile] = [
        *_build_summary_pages(pages),
    ]
    for page in pages:
        exported.append(
            ExportFile(
                relative_path=page.export_relative_path,
                text=_render_export_page(page, pages_by_graph_path, topics_by_current_path),
            )
        )

    exported.sort(key=lambda item: item.relative_path)
    return ExportSnapshot(files=tuple(exported))


def materialize_export_snapshot(snapshot: ExportSnapshot, content_root: Path) -> None:
    content_root.mkdir(parents=True, exist_ok=True)
    expected_paths = set()
    for export_file in snapshot.files:
        target = content_root / export_file.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(export_file.text)
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

    topic_domains = sorted({page.export_relative_path.split("/", 2)[1] for page in topic_pages if "/" in page.export_relative_path})
    provenance_families = sorted(
        {page.export_relative_path.split("/", 2)[1] for page in provenance_pages if "/" in page.export_relative_path}
    )

    summary_pages = [
        ExportFile(
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
        ExportFile(
            "topics/index.md",
            dump_frontmatter(
                {"title": "Topics", "publish": True},
                "\n".join(
                    [
                        "# Topics",
                        "",
                        "Browse semantic topics by domain.",
                        "",
                        *[
                            f"- [{_humanize_slug(domain)}]({domain})"
                            for domain in topic_domains
                        ],
                        "",
                    ]
                ),
            ),
        ),
        ExportFile(
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
                            f"- [{page.title}]({_relative_href('indexes/index.md', page.export_relative_path)})"
                            for page in index_pages
                        ],
                        "",
                    ]
                ),
            ),
        ),
        ExportFile(
            "provenance/index.md",
            dump_frontmatter(
                {"title": "Provenance", "publish": True},
                "\n".join(
                    [
                        "# Provenance",
                        "",
                        "Browse supporting notes grouped by source family.",
                        "",
                        *[
                            f"- [{_humanize_slug(family)}]({family})"
                            for family in provenance_families
                        ],
                        "",
                    ]
                ),
            ),
        ),
    ]
    return summary_pages


def _render_export_page(
    page: _SourcePage,
    pages_by_graph_path: Mapping[str, _SourcePage],
    topics_by_current_path: Mapping[str, _SourcePage],
) -> str:
    metadata = _export_frontmatter(page)
    body = _rewrite_graph_refs(page.body, page.export_relative_path, pages_by_graph_path)
    body = _rewrite_topic_path_refs(body, page.export_relative_path, topics_by_current_path)
    if page.kind == "provenance":
        body = _append_connected_topics(body, page, topics_by_current_path)
    return dump_frontmatter(metadata, body)


def _export_frontmatter(page: _SourcePage) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "title": page.title,
        "publish": True,
    }
    if page.kind == "topic":
        aliases = list(page.metadata.get("aliases", []))
        if aliases:
            metadata["aliases"] = aliases
        modified = page.metadata.get("last_reorganized_at") or page.metadata.get("last_updated_at")
        if modified:
            metadata["modified"] = modified
    elif page.kind == "provenance":
        created = page.metadata.get("created_at")
        if created:
            metadata["created"] = created
            metadata["modified"] = created
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
    return f"[{target_page.title}]({_relative_href(from_export_relative_path, target_page.export_relative_path)})"


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
            f"- [{topic_page.title}]({_relative_href(page.export_relative_path, topic_page.export_relative_path)})"
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
    return f"[{topic_page.title}]({_relative_href(from_export_relative_path, topic_page.export_relative_path)})"


def _relative_href(from_export_relative_path: str, to_export_relative_path: str) -> str:
    from_dir = PurePosixPath(from_export_relative_path).parent
    target = PurePosixPath(to_export_relative_path)
    if target.name == "index.md":
        target = target.parent
    else:
        target = target.with_suffix("")
    if str(target) == ".":
        return "."
    return posixpath.relpath(str(target), str(from_dir) or ".")


def _humanize_slug(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()

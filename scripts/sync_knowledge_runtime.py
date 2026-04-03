#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
import tomllib
from pathlib import Path

import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from knowledge_graph.install_targets import sync_tree  # noqa: E402


def main() -> int:
    project_metadata = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    skill_root = REPO_ROOT / "skills" / "knowledge"
    if not skill_root.exists():
        raise SystemExit(f"missing canonical skill package: {skill_root}")

    with tempfile.TemporaryDirectory(prefix="knowledge-runtime.") as temp_dir:
        staging_root = Path(temp_dir) / "runtime"
        write_runtime_package(
            repo_root=REPO_ROOT,
            runtime_root=staging_root,
            project_metadata=project_metadata,
        )
        sync_tree(staging_root, skill_root / "runtime")

    print(f"synchronized runtime: {skill_root / 'runtime'}")
    return 0


def write_runtime_package(
    *,
    repo_root: Path,
    runtime_root: Path,
    project_metadata: dict[str, object],
) -> None:
    runtime_source_root = repo_root / "src" / "knowledge_graph"
    if not runtime_source_root.exists():
        raise SystemExit(f"missing runtime source root: {runtime_source_root}")

    runtime_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(runtime_source_root, runtime_root / "src" / "knowledge_graph")
    (runtime_root / "pyproject.toml").write_text(render_runtime_pyproject(project_metadata))
    (runtime_root / "README.md").write_text(render_runtime_readme())


def render_runtime_pyproject(project_metadata: dict[str, object]) -> str:
    build_system = project_metadata.get("build-system", {})
    project = project_metadata.get("project", {})
    if not isinstance(build_system, dict) or not isinstance(project, dict):
        raise SystemExit("pyproject.toml is missing build-system or project metadata")

    lines = [
        "[build-system]",
        f"requires = {json.dumps(build_system.get('requires', ['setuptools>=69', 'wheel']))}",
        f'build-backend = {json.dumps(build_system.get("build-backend", "setuptools.build_meta"))}',
        "",
        "[project]",
        f'name = {json.dumps(project["name"])}',
        f'version = {json.dumps(project["version"])}',
        f'description = {json.dumps(project["description"])}',
        'readme = "README.md"',
        f'requires-python = {json.dumps(project["requires-python"])}',
        f"dependencies = {json.dumps(project.get('dependencies', []))}",
        "",
        "[project.scripts]",
    ]

    scripts = project.get("scripts", {})
    if not isinstance(scripts, dict) or not scripts:
        raise SystemExit("pyproject.toml must declare project.scripts for the knowledge CLI")
    for name, target in sorted(scripts.items()):
        lines.append(f"{name} = {json.dumps(target)}")

    optional_dependencies = project.get("optional-dependencies", {})
    if isinstance(optional_dependencies, dict) and optional_dependencies:
        lines.append("")
        lines.append("[project.optional-dependencies]")
        for extra_name, dependencies in sorted(optional_dependencies.items()):
            lines.append(f"{extra_name} = {json.dumps(dependencies)}")

    lines.extend(
        [
            "",
            "[tool.setuptools]",
            'package-dir = {"" = "src"}',
            "",
            "[tool.setuptools.packages.find]",
            'where = ["src"]',
            "",
        ]
    )

    return "\n".join(lines)


def render_runtime_readme() -> str:
    return (
        "# Fleki Knowledge Runtime\n\n"
        "This directory is the generated Python runtime that ships inside the `knowledge` skill.\n"
        "It lets the installed skill install and refresh the `knowledge` CLI without depending on a Fleki repo checkout.\n\n"
        "Naming crosswalk:\n"
        "- distribution package: `fleki-knowledge-graph`\n"
        "- Python module: `knowledge_graph`\n"
        "- CLI: `knowledge`\n"
        "- skill key: `fleki/knowledge`\n\n"
        "Persistent-root note:\n"
        "- installing or refreshing the CLI does not clear an existing graph\n"
        "- the shared graph root resolves under `~/.fleki/knowledge` unless an install manifest says otherwise\n\n"
        "Save contract notes:\n"
        '- bindings may include `timestamp` as ISO 8601 source-observed time\n'
        "- `knowledge_units[].temporal_scope`: `evergreen`, `time_bound`, `ephemeral`\n"
        "- `topic_actions[].lifecycle_state`: `current` or `historical`\n"
        "- `knowledge rebuild` owns `stale` and delete\n\n"
        "Minimal valid save example:\n\n"
        "Create `bindings.json`:\n\n"
        "```json\n"
        "[\n"
        "  {\n"
        '    "source_id": "note.customerio.current",\n'
        '    "local_path": "/absolute/path/to/customer-io.md",\n'
        '    "source_kind": "markdown_doc",\n'
        '    "authority_tier": "live_doctrine",\n'
        '    "timestamp": "2026-04-03T12:00:00+00:00"\n'
        "  }\n"
        "]\n"
        "```\n\n"
        "Create `decision.json`:\n\n"
        "```json\n"
        "{\n"
        '  "ingest_summary": {\n'
        '    "source_ids": ["note.customerio.current"],\n'
        '    "primary_domains": ["product"],\n'
        '    "authority_tier": "live_doctrine",\n'
        '    "sensitivity": "internal",\n'
        '    "semantic_summary": "Customer.io setup guidance."\n'
        "  },\n"
        '  "source_reading_reports": [\n'
        "    {\n"
        '      "source_id": "note.customerio.current",\n'
        '      "reading_mode": "direct_local_text",\n'
        '      "approved_helpers_used": [],\n'
        '      "readable_units": ["full text"],\n'
        '      "gaps": [],\n'
        '      "confidence_notes": []\n'
        "    }\n"
        "  ],\n"
        '  "topic_actions": [\n'
        "    {\n"
        '      "topic_path": "product/customer-io/current-setup",\n'
        '      "page_kind": "topic",\n'
        '      "action": "create",\n'
        '      "lifecycle_state": "current",\n'
        '      "candidate_title": "Customer.io Current Setup",\n'
        '      "why": "Capture the current setup guidance.",\n'
        '      "knowledge_units": [\n'
        "        {\n"
        '          "kind": "fact",\n'
        '          "temporal_scope": "time_bound",\n'
        '          "target_section": {\n'
        '            "section_id": null,\n'
        '            "heading": "Current Understanding"\n'
        "          },\n"
        '          "statement": "Customer.io is configured through the current workspace flow.",\n'
        '          "rationale": "This source describes the current setup path.",\n'
        '          "authority_posture": "live_doctrine",\n'
        '          "confidence": "high",\n'
        '          "evidence": [\n'
        "            {\n"
        '              "source_id": "note.customerio.current",\n'
        '              "locator": "entire note",\n'
        '              "notes": ""\n'
        "            }\n"
        "          ]\n"
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "provenance_notes": [\n'
        "    {\n"
        '      "source_ids": ["note.customerio.current"],\n'
        '      "bundle_rationale": null,\n'
        '      "title": "Customer.io setup provenance",\n'
        '      "summary": "Current setup guidance from the local source.",\n'
        '      "source_reading_summary": "Read directly from the local filesystem.",\n'
        '      "what_this_source_contributes": ["Current Customer.io setup guidance."],\n'
        '      "knowledge_sections_touched": [\n'
        "        {\n"
        '          "topic_path": "product/customer-io/current-setup",\n'
        '          "section_heading": "Current Understanding"\n'
        "        }\n"
        "      ],\n"
        '      "sensitivity_notes": "internal"\n'
        "    }\n"
        "  ],\n"
        '  "conflicts_or_questions": [],\n'
        '  "asset_actions": [],\n'
        '  "recommended_next_step": {\n'
        '    "action": "queue_rebuild_topic",\n'
        '    "scope": ["product/customer-io"],\n'
        '    "why": "Refresh nearby semantic neighbors later if needed."\n'
        "  }\n"
        "}\n"
        "```\n\n"
        "Apply it with:\n\n"
        "```bash\n"
        "knowledge save --bindings bindings.json --decision decision.json\n"
        "```\n\n"
        "Included behavior:\n"
        "- `knowledge status`\n"
        "- `knowledge search`\n"
        "- `knowledge trace`\n"
        "- `knowledge save`\n"
        "- `knowledge rebuild`\n"
        "- bundled PDF render support through `docling`\n\n"
        "Install the CLI from this directory:\n\n"
        "```bash\n"
        "uv tool install --force .\n"
        "```\n\n"
        "This directory is generated. Edit `src/knowledge_graph/**`, `pyproject.toml`, or `skills/knowledge/**` in Fleki, then regenerate the runtime bundle.\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())

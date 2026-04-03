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
SKILL_ROOT = REPO_ROOT / "skills" / "knowledge"
EXAMPLES_ROOT = SKILL_ROOT / "references" / "examples"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from knowledge_graph.install_targets import sync_tree  # noqa: E402
from knowledge_graph.validation import SOURCE_FAMILIES  # noqa: E402


def main() -> int:
    project_metadata = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    skill_root = SKILL_ROOT
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
    shutil.copytree(
        runtime_source_root,
        runtime_root / "src" / "knowledge_graph",
        ignore=shutil.ignore_patterns("__pycache__", "review_wiki"),
    )
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
    bindings_example = _render_example_json(EXAMPLES_ROOT / "minimal-save-bindings.json")
    decision_example = _render_example_json(EXAMPLES_ROOT / "minimal-save-decision.json")
    rendered_families = ", ".join(f"`{family}`" for family in sorted(SOURCE_FAMILIES))
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
        "Search/trace contract:\n"
        "- `knowledge search` is deterministic candidate discovery; use the returned `trace_ref` as the handoff into trace\n"
        "- `knowledge search` stays literal; rewrite paraphrases into exact page text, paths, aliases, or headings when needed\n"
        "- `knowledge trace` accepts exact refs only: `knowledge_id`, `knowledge_id#section_id`, `current_path`, page alias, or `current_path#section_alias`\n"
        "- section aliases accept deterministic normalization like `current_understanding`, `current-understanding`, or `Current Understanding`\n"
        "- page-level trace returns `supported_sections`; it does not guess a best section\n\n"
        "Save contract notes:\n"
        "- `knowledge save` applies immediately; there is no preview, validate-only, or dry-run save path\n"
        f"- bindings must include `source_family`: {rendered_families}\n"
        '- bindings must include `timestamp` as ISO 8601 source-observed time\n'
        "- if source-observed time is unknown, stop instead of inventing it\n"
        "- `ingest_summary.authority_tier`: `live_doctrine`, `raw_runtime`, `historical_support`, `generated_mirror`, `mixed`\n"
        "- `knowledge_units[].authority_posture`: `live_doctrine`, `supported_by_runtime`, `supported_by_internal_session`, `tentative`, `mixed`\n"
        "- do not swap `authority_tier` and `authority_posture`\n"
        "- `knowledge_units[].kind`: `fact`, `principle`, `playbook`, `decision`, `pattern`, `regression`, `glossary`, `question`\n"
        "- `knowledge_units[].temporal_scope`: `evergreen`, `time_bound`, `ephemeral`\n"
        "- `topic_actions[].lifecycle_state`: `current` or `historical`\n"
        "- `knowledge rebuild` owns `stale` and delete\n\n"
        "Status contract notes:\n"
        "- `ingests_with_reading_limits` counts unread or missing content only\n"
        "- `ingests_with_confidence_caveats` counts confidence notes that do not imply unread content\n\n"
        "Minimal valid save example:\n\n"
        "Create `bindings.json`:\n\n"
        "```json\n"
        f"{bindings_example}\n"
        "```\n\n"
        "Create `decision.json`:\n\n"
        "```json\n"
        f"{decision_example}\n"
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


def _render_example_json(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"missing runtime README example source: {path}")
    payload = json.loads(path.read_text())
    return json.dumps(payload, indent=2, sort_keys=False)


if __name__ == "__main__":
    raise SystemExit(main())

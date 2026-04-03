from __future__ import annotations

from pathlib import Path
from typing import Dict

from .install_targets import (
    CANONICAL_SKILL_KEY,
    codex_managed_install_root,
    codex_managed_skill_path,
    discover_hermes_homes,
    discover_openclaw_roots,
    hermes_skill_paths,
    openclaw_skill_paths,
)
from .layout import resolve_knowledge_layout
from .models import ResolvedKnowledgeLayout, RuntimeInstallManifest


def _skill_dir(repo_root: Path | str) -> Path:
    return Path(repo_root).expanduser().resolve() / "skills" / "knowledge"

def _coerce_layout(
    repo_root: Path | str,
    layout: ResolvedKnowledgeLayout | None,
) -> ResolvedKnowledgeLayout:
    if layout is not None:
        return layout
    return resolve_knowledge_layout(repo_root=Path(repo_root).expanduser().resolve())


def codex_runtime_manifest(
    repo_root: Path | str,
    *,
    layout: ResolvedKnowledgeLayout | None = None,
) -> Dict[str, object]:
    resolved_layout = _coerce_layout(repo_root, layout)
    manifest = RuntimeInstallManifest(
        runtime="codex",
        skill_name="knowledge",
        skill_package_path=_skill_dir(repo_root),
        data_root=resolved_layout.data_root,
        install_manifest_path=resolved_layout.install_manifest_path,
        adapter_mode="upstream_global_manager",
        target_skill_paths=(codex_managed_skill_path(),),
        notes=(
            f"Codex installs the managed bundle under {codex_managed_install_root()}",
            "The repo installer uses the upstream npx skills add flow for Codex",
        ),
    )
    return manifest.to_dict()


def hermes_runtime_manifest(
    repo_root: Path | str,
    *,
    layout: ResolvedKnowledgeLayout | None = None,
) -> Dict[str, object]:
    resolved_layout = _coerce_layout(repo_root, layout)
    homes = discover_hermes_homes()
    manifest = RuntimeInstallManifest(
        runtime="hermes",
        skill_name="knowledge",
        skill_package_path=_skill_dir(repo_root),
        data_root=resolved_layout.data_root,
        install_manifest_path=resolved_layout.install_manifest_path,
        adapter_mode="per_home_native_copy",
        target_skill_paths=hermes_skill_paths(),
        notes=(
            "Hermes profiles are independent HERMES_HOME roots with their own skills directories",
            f"Detected Hermes homes: {', '.join(str(path) for path in homes) if homes else 'none'}",
        ),
    )
    return manifest.to_dict()


def openclaw_runtime_manifest(
    repo_root: Path | str,
    *,
    layout: ResolvedKnowledgeLayout | None = None,
) -> Dict[str, object]:
    resolved_layout = _coerce_layout(repo_root, layout)
    roots = discover_openclaw_roots()
    manifest = RuntimeInstallManifest(
        runtime="openclaw",
        skill_name="knowledge",
        skill_package_path=_skill_dir(repo_root),
        data_root=resolved_layout.data_root,
        install_manifest_path=resolved_layout.install_manifest_path,
        adapter_mode="per_root_native_copy",
        target_skill_paths=openclaw_skill_paths(),
        canonical_skill_key=CANONICAL_SKILL_KEY,
        notes=(
            "OpenClaw installs use real copied bundles inside each discovered managed skills root",
            f"Detected OpenClaw roots: {', '.join(str(path) for path in roots) if roots else 'none'}",
        ),
    )
    return manifest.to_dict()

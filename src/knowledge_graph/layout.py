from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .frontmatter import (
    dump_frontmatter,
    split_frontmatter_for_migration,
    uses_legacy_json_frontmatter,
)
from .models import KnowledgeInstallManifest, ResolvedKnowledgeLayout
from .validation import ValidationError


def default_root(*, home: Path | str | None = None, platform_name: Optional[str] = None) -> Path:
    del platform_name
    return _base_home(home) / ".fleki"


def default_config_root(*, home: Path | str | None = None, platform_name: Optional[str] = None) -> Path:
    return default_root(home=home, platform_name=platform_name)


def default_data_root(*, home: Path | str | None = None, platform_name: Optional[str] = None) -> Path:
    return default_root(home=home, platform_name=platform_name) / "knowledge"


def default_state_root(*, home: Path | str | None = None, platform_name: Optional[str] = None) -> Path:
    return default_root(home=home, platform_name=platform_name) / "state"


def default_install_manifest_path(
    *,
    home: Path | str | None = None,
    platform_name: Optional[str] = None,
) -> Path:
    return default_config_root(home=home, platform_name=platform_name) / "install.json"


def resolve_knowledge_layout(
    *,
    data_root: Path | str | None = None,
    config_root: Path | str | None = None,
    state_root: Path | str | None = None,
    install_manifest_path: Path | str | None = None,
    repo_root: Path | str | None = None,
    home: Path | str | None = None,
    platform_name: Optional[str] = None,
) -> ResolvedKnowledgeLayout:
    normalized_repo_root = Path(repo_root).expanduser().resolve() if repo_root is not None else None
    normalized_config_root = _normalize_optional_absolute(
        config_root,
        label="config_root",
    ) or default_config_root(home=home, platform_name=platform_name)
    normalized_install_manifest_path = _normalize_optional_absolute(
        install_manifest_path,
        label="install_manifest_path",
    ) or default_install_manifest_path(home=home, platform_name=platform_name)

    install_manifest = None
    if normalized_install_manifest_path.exists():
        install_manifest = load_install_manifest(normalized_install_manifest_path)

    if install_manifest is not None:
        if data_root is not None:
            explicit_data_root = _normalize_required_absolute(data_root, label="data_root")
            if explicit_data_root != install_manifest.data_root:
                raise ValidationError(
                    "explicit data_root does not match install manifest data_root"
                )
        if config_root is not None:
            explicit_config_root = _normalize_required_absolute(config_root, label="config_root")
            if explicit_config_root != install_manifest.config_root:
                raise ValidationError(
                    "explicit config_root does not match install manifest config_root"
                )
        if state_root is not None:
            explicit_state_root = _normalize_required_absolute(state_root, label="state_root")
            if explicit_state_root != install_manifest.state_root:
                raise ValidationError(
                    "explicit state_root does not match install manifest state_root"
                )
        layout = ResolvedKnowledgeLayout(
            data_root=install_manifest.data_root,
            config_root=install_manifest.config_root,
            state_root=install_manifest.state_root,
            install_manifest_path=normalized_install_manifest_path,
            install_manifest=install_manifest,
            legacy_repo_graph_path=_legacy_repo_graph_path(
                normalized_repo_root,
                install_manifest.data_root,
            ),
        )
        return layout

    normalized_data_root = _normalize_optional_absolute(
        data_root,
        label="data_root",
    ) or default_data_root(home=home, platform_name=platform_name)
    normalized_state_root = _normalize_optional_absolute(
        state_root,
        label="state_root",
    ) or default_state_root(home=home, platform_name=platform_name)

    return ResolvedKnowledgeLayout(
        data_root=normalized_data_root,
        config_root=normalized_config_root,
        state_root=normalized_state_root,
        install_manifest_path=normalized_install_manifest_path,
        install_manifest=None,
        legacy_repo_graph_path=_legacy_repo_graph_path(
            normalized_repo_root,
            normalized_data_root,
        ),
    )


def build_install_manifest(
    layout: ResolvedKnowledgeLayout,
    *,
    canonical_skill_path: Path | str | None = None,
    codex_managed_skill_path: Path | str | None = None,
    hermes_skill_paths: tuple[Path | str, ...] = (),
    openclaw_skill_paths: tuple[Path | str, ...] = (),
    legacy_repo_root: Path | str | None = None,
) -> KnowledgeInstallManifest:
    return KnowledgeInstallManifest(
        version=2,
        data_root=layout.data_root,
        config_root=layout.config_root,
        state_root=layout.state_root,
        install_manifest_path=layout.install_manifest_path,
        canonical_skill_path=_normalize_optional_absolute(
            canonical_skill_path,
            label="canonical_skill_path",
        ),
        codex_managed_skill_path=_normalize_optional_absolute(
            codex_managed_skill_path,
            label="codex_managed_skill_path",
        ),
        hermes_skill_paths=tuple(
            _normalize_required_absolute(path, label="hermes_skill_paths")
            for path in hermes_skill_paths
        ),
        openclaw_skill_paths=tuple(
            _normalize_required_absolute(path, label="openclaw_skill_paths")
            for path in openclaw_skill_paths
        ),
        legacy_repo_root=_normalize_optional_absolute(legacy_repo_root, label="legacy_repo_root"),
    )


def load_install_manifest(path: Path | str) -> KnowledgeInstallManifest:
    manifest_path = _normalize_required_absolute(path, label="install_manifest_path")
    payload = json.loads(manifest_path.read_text())
    return KnowledgeInstallManifest.from_dict(payload)


def write_install_manifest(manifest: KnowledgeInstallManifest) -> Path:
    manifest.install_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.install_manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
    )
    return manifest.install_manifest_path


def migrate_legacy_install(
    *,
    repo_root: Path | str | None = None,
    home: Path | str | None = None,
) -> Dict[str, Any] | None:
    normalized_repo_root = Path(repo_root).expanduser().resolve() if repo_root is not None else None
    target_layout = resolve_knowledge_layout(
        data_root=default_data_root(home=home),
        config_root=default_config_root(home=home),
        state_root=default_state_root(home=home),
        install_manifest_path=default_install_manifest_path(home=home),
        repo_root=normalized_repo_root,
    )
    if target_layout.install_manifest_path.exists():
        return None
    if _path_has_content(target_layout.config_root):
        raise ValidationError(
            f"default Fleki root already exists without install.json: {target_layout.config_root}"
        )

    legacy_manifest_path = _find_legacy_install_manifest_path(home=home)
    if legacy_manifest_path is not None:
        legacy_manifest = load_install_manifest(legacy_manifest_path)
        copy_pairs = _legacy_copy_pairs(legacy_manifest, target_layout)
        for source_root, target_root in copy_pairs:
            if not source_root.exists():
                continue
            shutil.copytree(source_root, target_root, dirs_exist_ok=True)

        migrated_manifest = KnowledgeInstallManifest(
            version=legacy_manifest.version,
            data_root=target_layout.data_root,
            config_root=target_layout.config_root,
            state_root=target_layout.state_root,
            install_manifest_path=target_layout.install_manifest_path,
            canonical_skill_path=legacy_manifest.canonical_skill_path,
            codex_managed_skill_path=legacy_manifest.codex_managed_skill_path,
            hermes_skill_paths=legacy_manifest.hermes_skill_paths,
            openclaw_skill_paths=legacy_manifest.openclaw_skill_paths,
            legacy_repo_root=legacy_manifest.legacy_repo_root,
        )
        write_install_manifest(migrated_manifest)
        verification = _verify_migrated_install(target_layout, copy_pairs)
        delete_roots = _legacy_delete_roots(legacy_manifest)
        _delete_legacy_roots(delete_roots)
        return {
            "migrated": True,
            "kind": "legacy_install",
            "from_install_manifest": str(legacy_manifest_path),
            "to_install_manifest": str(target_layout.install_manifest_path),
            "deleted_roots": [str(path) for path in delete_roots],
            "verification": verification,
        }

    if normalized_repo_root is None:
        return None
    legacy_graph_root = normalized_repo_root / "knowledge"
    if not legacy_graph_root.exists():
        return None

    result = migrate_legacy_repo_graph(repo_root=normalized_repo_root, layout=target_layout)
    manifest = build_install_manifest(target_layout, legacy_repo_root=normalized_repo_root)
    write_install_manifest(manifest)
    verification = _verify_migrated_install(target_layout, ((legacy_graph_root, target_layout.data_root),))
    return {
        "migrated": True,
        "kind": "repo_graph",
        "from_repo_graph": str(legacy_graph_root),
        "to_install_manifest": str(target_layout.install_manifest_path),
        "verification": verification,
        "repo_graph_result": result,
    }


def migrate_legacy_repo_graph(
    *,
    repo_root: Path | str,
    layout: ResolvedKnowledgeLayout,
) -> Dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    legacy_root = normalized_repo_root / "knowledge"
    if not legacy_root.exists():
        return {
            "legacy_root": str(legacy_root),
            "copied_files": 0,
            "verified": True,
            "switched": False,
        }

    if layout.data_root.exists() and any(layout.data_root.iterdir()):
        raise ValidationError("canonical data_root must be empty before migration")

    shutil.copytree(legacy_root, layout.data_root, dirs_exist_ok=True)
    ported_files = port_graph_frontmatter(layout.data_root)
    rewritten_files = _rewrite_legacy_graph_paths(layout.data_root)
    source_count = _file_count(legacy_root)
    copied_count = _file_count(layout.data_root)
    if copied_count < source_count:
        raise ValidationError("migration copy did not reproduce the full legacy graph")

    return {
        "legacy_root": str(legacy_root),
        "data_root": str(layout.data_root),
        "copied_files": copied_count,
        "verified": copied_count == source_count,
        "rewritten_files": rewritten_files + ported_files,
        "switched": copied_count == source_count,
    }


def _base_home(home: Path | str | None) -> Path:
    if home is None:
        return Path.home()
    return Path(home).expanduser().resolve()

def _legacy_repo_graph_path(repo_root: Optional[Path], data_root: Path) -> Optional[Path]:
    if repo_root is None:
        return None
    legacy_path = repo_root / "knowledge"
    if legacy_path == data_root:
        return None
    return legacy_path


def _normalize_optional_absolute(value: Path | str | None, *, label: str) -> Optional[Path]:
    if value is None:
        return None
    return _normalize_required_absolute(value, label=label)


def _normalize_required_absolute(value: Path | str, *, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValidationError(f"{label} must be an absolute path")
    return Path(os.path.abspath(path))


def _file_count(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.is_file())


def _path_has_content(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def port_graph_frontmatter(data_root: Path) -> int:
    ported = 0
    for top_level in ("topics", "provenance", "receipts", "search"):
        target_root = data_root / top_level
        if not target_root.exists():
            continue
        for path in target_root.rglob("*.md"):
            if _port_legacy_frontmatter(path):
                ported += 1
    return ported


def _find_legacy_install_manifest_path(*, home: Path | str | None = None) -> Optional[Path]:
    for path in _legacy_install_manifest_candidates(home=home):
        if path.exists():
            return path
    return None


def _legacy_install_manifest_candidates(*, home: Path | str | None = None) -> tuple[Path, ...]:
    base_home = _base_home(home)
    raw_candidates = [
        base_home / "Library" / "Application Support" / "Fleki" / "install.json",
        base_home / ".config" / "fleki" / "install.json",
    ]
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        raw_candidates.append(Path(xdg_config_home).expanduser() / "fleki" / "install.json")

    seen: set[Path] = set()
    candidates = []
    for path in raw_candidates:
        normalized = Path(os.path.abspath(path.expanduser()))
        if normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(normalized)
    return tuple(candidates)


def _legacy_copy_pairs(
    legacy_manifest: KnowledgeInstallManifest,
    target_layout: ResolvedKnowledgeLayout,
) -> tuple[tuple[Path, Path], ...]:
    pairs = [(legacy_manifest.config_root, target_layout.config_root)]
    if not _is_relative_to(legacy_manifest.data_root, legacy_manifest.config_root):
        pairs.append((legacy_manifest.data_root, target_layout.data_root))
    if (
        legacy_manifest.state_root != legacy_manifest.data_root
        and not _is_relative_to(legacy_manifest.state_root, legacy_manifest.config_root)
    ):
        pairs.append((legacy_manifest.state_root, target_layout.state_root))

    deduped = []
    seen: set[tuple[Path, Path]] = set()
    for pair in pairs:
        if pair in seen:
            continue
        seen.add(pair)
        deduped.append(pair)
    return tuple(deduped)


def _legacy_delete_roots(legacy_manifest: KnowledgeInstallManifest) -> tuple[Path, ...]:
    candidates = [legacy_manifest.config_root]
    if not _is_relative_to(legacy_manifest.data_root, legacy_manifest.config_root):
        candidates.append(legacy_manifest.data_root)
    if (
        legacy_manifest.state_root != legacy_manifest.data_root
        and not _is_relative_to(legacy_manifest.state_root, legacy_manifest.config_root)
    ):
        candidates.append(legacy_manifest.state_root)
    return _prune_nested_paths(candidates)


def _verify_migrated_install(
    layout: ResolvedKnowledgeLayout,
    copy_pairs: tuple[tuple[Path, Path], ...],
) -> Dict[str, Any]:
    from .repository import KnowledgeRepository

    repo = KnowledgeRepository(layout)
    repo.initialize_layout()
    status = repo.status(write_receipt=False)
    if status["resolved_data_root"] != str(layout.data_root):
        raise ValidationError("migrated install verification failed: resolved_data_root mismatch")
    if status["install_manifest_path"] != str(layout.install_manifest_path):
        raise ValidationError("migrated install verification failed: install_manifest_path mismatch")

    file_checks = []
    for source_root, target_root in copy_pairs:
        if not source_root.exists():
            continue
        source_files = _file_count(source_root)
        target_files = _file_count(target_root) if target_root.exists() else 0
        if target_files < source_files:
            raise ValidationError(
                f"migrated install verification failed: {target_root} has fewer files than {source_root}"
            )
        file_checks.append(
            {
                "source_root": str(source_root),
                "target_root": str(target_root),
                "source_files": source_files,
                "target_files": target_files,
            }
        )

    return {
        "verified": True,
        "status": {
            "resolved_data_root": status["resolved_data_root"],
            "install_manifest_path": status["install_manifest_path"],
            "topic_count": status["topic_count"],
        },
        "file_checks": file_checks,
    }


def _delete_legacy_roots(paths: tuple[Path, ...]) -> None:
    for path in paths:
        if not path.exists():
            continue
        shutil.rmtree(path)
        if path.name == "knowledge" and path.parent.name == "fleki":
            _remove_if_empty(path.parent)


def _remove_if_empty(path: Path) -> None:
    try:
        path.rmdir()
    except OSError:
        return


def _prune_nested_paths(paths: list[Path]) -> tuple[Path, ...]:
    unique_paths = []
    for path in sorted({Path(os.path.abspath(item)) for item in paths}, key=lambda item: (len(item.parts), str(item))):
        if any(_is_relative_to(path, existing) for existing in unique_paths):
            continue
        unique_paths.append(path)
    return tuple(unique_paths)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _rewrite_legacy_graph_paths(data_root: Path) -> int:
    rewritten = 0
    for path in data_root.rglob("*.json"):
        if path.parent.name == "sources" or any(parent.name == "sources" for parent in path.parents):
            if _rewrite_json_paths(path):
                rewritten += 1

    for top_level in ("topics", "provenance", "receipts", "search"):
        target_root = data_root / top_level
        if not target_root.exists():
            continue
        for path in target_root.rglob("*.md"):
            if _rewrite_frontmatter_paths(path):
                rewritten += 1
    return rewritten


def _rewrite_json_paths(path: Path) -> bool:
    payload = json.loads(path.read_text())
    updated = _rewrite_legacy_values(payload)
    if updated == payload:
        return False
    path.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n")
    return True


def _rewrite_frontmatter_paths(path: Path) -> bool:
    try:
        metadata, body = split_frontmatter_for_migration(path.read_text())
    except ValueError:
        return False

    updated_metadata = _rewrite_legacy_values(metadata)
    updated_body = body.replace("`knowledge/", "`")
    if updated_metadata == metadata and updated_body == body:
        return False
    path.write_text(dump_frontmatter(updated_metadata, updated_body))
    return True


def _port_legacy_frontmatter(path: Path) -> bool:
    text = path.read_text()
    try:
        is_legacy = uses_legacy_json_frontmatter(text)
        metadata, body = split_frontmatter_for_migration(text)
    except ValueError:
        return False
    if not is_legacy:
        return False
    path.write_text(dump_frontmatter(metadata, body))
    return True


def _rewrite_legacy_values(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("knowledge/"):
            return value.removeprefix("knowledge/")
        return value
    if isinstance(value, list):
        return [_rewrite_legacy_values(item) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_legacy_values(item) for key, item in value.items()}
    return value

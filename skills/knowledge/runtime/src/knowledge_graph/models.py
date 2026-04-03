from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


@dataclass(frozen=True)
class SourceBinding:
    source_id: str
    local_path: Path
    source_kind: str
    source_family: str
    authority_tier: str = "historical_support"
    sensitivity: str = "internal"
    timestamp: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "local_path", Path(self.local_path))


@dataclass(frozen=True)
class RebuildPageUpdate:
    knowledge_id: str
    new_current_path: Optional[str] = None
    add_supersedes: Tuple[str, ...] = field(default_factory=tuple)
    lifecycle_state: Optional[str] = None
    delete_page: bool = False
    note: Optional[str] = None


@dataclass(frozen=True)
class RebuildPlan:
    scope: Tuple[str, ...]
    page_updates: Tuple[RebuildPageUpdate, ...] = field(default_factory=tuple)
    open_questions: Tuple[str, ...] = field(default_factory=tuple)
    refresh_indexes: bool = True


@dataclass(frozen=True)
class KnowledgeInstallManifest:
    version: int
    data_root: Path
    config_root: Path
    state_root: Path
    install_manifest_path: Path
    canonical_skill_path: Optional[Path] = None
    codex_managed_skill_path: Optional[Path] = None
    hermes_skill_paths: Tuple[Path, ...] = field(default_factory=tuple)
    openclaw_skill_paths: Tuple[Path, ...] = field(default_factory=tuple)
    legacy_repo_root: Optional[Path] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_root", Path(self.data_root))
        object.__setattr__(self, "config_root", Path(self.config_root))
        object.__setattr__(self, "state_root", Path(self.state_root))
        object.__setattr__(self, "install_manifest_path", Path(self.install_manifest_path))
        for field_name in [
            "canonical_skill_path",
            "codex_managed_skill_path",
            "legacy_repo_root",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, Path(value))
        object.__setattr__(
            self,
            "hermes_skill_paths",
            tuple(Path(path) for path in self.hermes_skill_paths),
        )
        object.__setattr__(
            self,
            "openclaw_skill_paths",
            tuple(Path(path) for path in self.openclaw_skill_paths),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "version": self.version,
            "data_root": str(self.data_root),
            "config_root": str(self.config_root),
            "state_root": str(self.state_root),
            "install_manifest_path": str(self.install_manifest_path),
        }
        for field_name in [
            "canonical_skill_path",
            "codex_managed_skill_path",
            "legacy_repo_root",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                payload[field_name] = str(value)
        payload["hermes_skill_paths"] = [str(path) for path in self.hermes_skill_paths]
        payload["openclaw_skill_paths"] = [str(path) for path in self.openclaw_skill_paths]
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "KnowledgeInstallManifest":
        canonical_skill_path = _optional_path(
            payload.get("canonical_skill_path")
            or payload.get("shipped_skill_path")
            or payload.get("source_skill_path")
        )
        codex_managed_skill_path = _optional_path(
            payload.get("codex_managed_skill_path")
            or payload.get("managed_skill_path")
            or payload.get("shared_skill_path")
        )
        return cls(
            version=int(payload.get("version", 1)),
            data_root=Path(payload["data_root"]),
            config_root=Path(payload["config_root"]),
            state_root=Path(payload["state_root"]),
            install_manifest_path=Path(payload["install_manifest_path"]),
            canonical_skill_path=canonical_skill_path,
            codex_managed_skill_path=codex_managed_skill_path,
            hermes_skill_paths=_optional_path_list(payload.get("hermes_skill_paths")),
            openclaw_skill_paths=_optional_path_list(payload.get("openclaw_skill_paths")),
            legacy_repo_root=_optional_path(payload.get("legacy_repo_root")),
        )


@dataclass(frozen=True)
class ResolvedKnowledgeLayout:
    data_root: Path
    config_root: Path
    state_root: Path
    install_manifest_path: Path
    install_manifest: Optional[KnowledgeInstallManifest] = None
    legacy_repo_graph_path: Optional[Path] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_root", Path(self.data_root))
        object.__setattr__(self, "config_root", Path(self.config_root))
        object.__setattr__(self, "state_root", Path(self.state_root))
        object.__setattr__(self, "install_manifest_path", Path(self.install_manifest_path))
        if self.legacy_repo_graph_path is not None:
            object.__setattr__(self, "legacy_repo_graph_path", Path(self.legacy_repo_graph_path))


@dataclass(frozen=True)
class RuntimeInstallManifest:
    runtime: str
    skill_name: str
    skill_package_path: Path
    data_root: Path
    install_manifest_path: Path
    adapter_mode: str
    target_skill_paths: Tuple[Path, ...] = field(default_factory=tuple)
    canonical_skill_key: Optional[str] = None
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "skill_package_path", Path(self.skill_package_path))
        object.__setattr__(self, "data_root", Path(self.data_root))
        object.__setattr__(self, "install_manifest_path", Path(self.install_manifest_path))
        object.__setattr__(
            self,
            "target_skill_paths",
            tuple(Path(path) for path in self.target_skill_paths),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "runtime": self.runtime,
            "skill_name": self.skill_name,
            "skill_package_path": str(self.skill_package_path),
            "data_root": str(self.data_root),
            "install_manifest_path": str(self.install_manifest_path),
            "adapter_mode": self.adapter_mode,
            "target_skill_paths": [str(path) for path in self.target_skill_paths],
            "notes": list(self.notes),
        }
        if self.canonical_skill_key is not None:
            payload["canonical_skill_key"] = self.canonical_skill_key
        return payload


def _optional_path(value: Any) -> Optional[Path]:
    if value in {None, ""}:
        return None
    return Path(value)


def _optional_path_list(value: Any) -> Tuple[Path, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(Path(item) for item in value if item not in {None, ""})
    if value in {None, ""}:
        return ()
    return (Path(value),)


@dataclass(frozen=True)
class PdfRenderBundle:
    source_id: str
    render_eligible: bool
    omission_reason: Optional[str] = None
    engine_id: Optional[str] = None
    engine_version: Optional[str] = None
    fidelity_mode: Optional[str] = None
    render_relative_path: Optional[str] = None
    render_manifest_relative_path: Optional[str] = None
    asset_relative_paths: Tuple[str, ...] = field(default_factory=tuple)
    ocr_mode: Optional[str] = None
    image_export_mode: Optional[str] = None
    page_count: Optional[int] = None
    anchor_hints: Tuple[str, ...] = field(default_factory=tuple)
    declared_gaps: Tuple[str, ...] = field(default_factory=tuple)
    source_sha256: Optional[str] = None

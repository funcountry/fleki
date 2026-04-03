from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Tuple

from .validation import ValidationError


KNOWLEDGE_SKILL_NAME = "knowledge"
CANONICAL_SKILL_KEY = "fleki/knowledge"


def codex_managed_install_root(*, home: Path | str | None = None) -> Path:
    return _base_home(home) / ".agents" / "skills"


def codex_managed_skill_path(
    skill_name: str = KNOWLEDGE_SKILL_NAME,
    *,
    home: Path | str | None = None,
) -> Path:
    return codex_managed_install_root(home=home) / skill_name


def discover_hermes_homes(*, home: Path | str | None = None) -> Tuple[Path, ...]:
    base_home = _base_home(home)
    candidates = []

    hermes_home_override = os.environ.get("HERMES_HOME", "").strip()
    if hermes_home_override:
        candidates.append(Path(hermes_home_override).expanduser())

    default_home = base_home / ".hermes"
    candidates.append(default_home)

    candidates.extend(_hermes_profile_homes_from_cli(base_home))

    profiles_root = default_home / "profiles"
    if profiles_root.is_dir():
        for path in sorted(profiles_root.iterdir()):
            if path.is_dir():
                candidates.append(path)

    return tuple(path for path in _dedupe_paths(candidates) if path.is_dir())


def hermes_skill_paths(
    skill_name: str = KNOWLEDGE_SKILL_NAME,
    *,
    home: Path | str | None = None,
) -> Tuple[Path, ...]:
    return tuple(path / "skills" / skill_name for path in discover_hermes_homes(home=home))


def hermes_skill_disabled(
    hermes_home: Path | str,
    *,
    skill_name: str = KNOWLEDGE_SKILL_NAME,
) -> bool:
    config_path = Path(hermes_home).expanduser() / "config.yaml"
    if not config_path.exists():
        return False

    text = config_path.read_text()
    in_skills = False
    in_disabled = False
    skills_indent = None
    disabled_indent = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if not in_skills:
            if stripped == "skills:":
                in_skills = True
                skills_indent = indent
            continue

        if indent <= (skills_indent or 0) and not stripped.startswith("- "):
            in_skills = False
            in_disabled = False
            skills_indent = None
            disabled_indent = None
            if stripped == "skills:":
                in_skills = True
                skills_indent = indent
            continue

        if not in_disabled:
            if stripped == "disabled:":
                in_disabled = True
                disabled_indent = indent
            continue

        if indent <= (disabled_indent or 0):
            in_disabled = False
            disabled_indent = None
            if stripped == "disabled:":
                in_disabled = True
                disabled_indent = indent
            continue

        if stripped.startswith("- ") and stripped[2:].strip() == skill_name:
            return True

    return False


def discover_openclaw_roots(*, home: Path | str | None = None) -> Tuple[Path, ...]:
    base_home = _base_home(home)
    candidates = []

    live_root = _openclaw_root_from_live_skills()
    if live_root is not None:
        candidates.append(live_root)

    for path in sorted(base_home.glob(".openclaw*")):
        if path.is_dir():
            candidates.append(path)

    return tuple(
        path
        for path in _dedupe_paths(candidates)
        if path.is_dir() and _looks_like_openclaw_root(path)
    )


def openclaw_skill_paths(
    skill_name: str = KNOWLEDGE_SKILL_NAME,
    *,
    home: Path | str | None = None,
) -> Tuple[Path, ...]:
    return tuple(path / "skills" / skill_name for path in discover_openclaw_roots(home=home))


def sync_tree(source_root: Path | str, target_root: Path | str, *, replace: bool = True) -> None:
    source = Path(source_root).expanduser().resolve()
    target = Path(os.path.abspath(Path(target_root).expanduser()))
    if not source.is_dir():
        raise ValidationError(f"source tree does not exist: {source}")

    if target.is_symlink():
        if not replace:
            raise ValidationError(f"refusing to replace symlink target: {target}")
        target.unlink()
    elif target.exists() and not target.is_dir():
        if not replace:
            raise ValidationError(f"refusing to replace non-directory target: {target}")
        target.unlink()

    target.mkdir(parents=True, exist_ok=True)

    source_relatives = set()
    for source_path in sorted(source.rglob("*")):
        relative_path = source_path.relative_to(source)
        source_relatives.add(relative_path)
        target_path = target / relative_path
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

    for target_path in sorted(target.rglob("*"), reverse=True):
        relative_path = target_path.relative_to(target)
        if relative_path in source_relatives:
            continue
        if target_path.is_dir():
            target_path.rmdir()
            continue
        target_path.unlink()


def materialize_skill_copy(
    source_tree_path: Path | str,
    target_skill_path: Path | str,
    *,
    replace: bool = True,
) -> None:
    sync_tree(source_tree_path, target_skill_path, replace=replace)


def _hermes_profile_homes_from_cli(base_home: Path) -> Tuple[Path, ...]:
    if shutil.which("hermes") is None:
        return ()
    try:
        result = subprocess.run(
            ["hermes", "profile", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ()
    if result.returncode != 0:
        return ()

    names = []
    for line in result.stdout.splitlines():
        stripped = line.strip().lstrip("◆").strip()
        if not stripped:
            continue
        name = stripped.split()[0]
        if name == "default" or _looks_like_profile_name(name):
            names.append(name)

    homes = []
    for name in names:
        if name == "default":
            homes.append(base_home / ".hermes")
        else:
            homes.append(base_home / ".hermes" / "profiles" / name)
    return tuple(homes)


def _openclaw_root_from_live_skills() -> Path | None:
    if shutil.which("openclaw") is None:
        return None
    try:
        result = subprocess.run(
            ["openclaw", "skills", "list", "--json", "--eligible"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    managed_skills_dir = payload.get("managedSkillsDir")
    if not managed_skills_dir:
        return None
    path = Path(str(managed_skills_dir)).expanduser()
    return path.parent


def _looks_like_openclaw_root(path: Path) -> bool:
    return (path / "skills").is_dir() or (path / "workspace").is_dir()


def _base_home(home: Path | str | None) -> Path:
    if home is None:
        return Path.home()
    return Path(home).expanduser().resolve()


def _looks_like_profile_name(value: str) -> bool:
    return bool(value) and all(char.islower() or char.isdigit() or char in {"_", "-"} for char in value)


def _dedupe_paths(paths: Iterable[Path | str]) -> Tuple[Path, ...]:
    ordered = []
    seen = set()
    for path in paths:
        normalized = Path(path).expanduser().resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)

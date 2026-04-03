#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from knowledge_graph import (  # noqa: E402
    KnowledgeRepository,
    build_install_manifest,
    load_install_manifest,
    migrate_legacy_install,
    resolve_knowledge_layout,
    write_install_manifest,
)
from knowledge_graph.install_targets import (  # noqa: E402
    KNOWLEDGE_SKILL_NAME,
    codex_managed_skill_path,
    discover_hermes_homes,
    discover_openclaw_roots,
    hermes_skill_disabled,
    hermes_skill_paths,
    materialize_skill_copy,
    openclaw_skill_paths,
)


SURFACES = ("codex", "hermes", "openclaw")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="install_knowledge_skill.py",
        description="Install the repo-local knowledge skill into detected runtimes.",
    )
    parser.add_argument(
        "--surface",
        action="append",
        choices=SURFACES,
        help="Limit install to one or more runtimes. Defaults to all detected runtimes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show detected runtimes and target paths without writing anything.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing file or symlink targets when materializing copied bundles.",
    )
    args = parser.parse_args(argv)

    skill_root = REPO_ROOT / "skills" / KNOWLEDGE_SKILL_NAME
    if not skill_root.exists():
        raise SystemExit(f"missing canonical skill package: {skill_root}")

    selected_surfaces = tuple(args.surface) if args.surface else auto_detected_surfaces()
    if not selected_surfaces:
        print("No supported runtime was detected on this machine.")
        return 0

    detection = detect_targets()
    if args.dry_run:
        print(f"Canonical skill package: {skill_root}")
        for surface in SURFACES:
            print(render_detection_line(surface, detection[surface], selected=surface in selected_surfaces))
        return 0

    run_checked([sys.executable, str(REPO_ROOT / "scripts" / "sync_knowledge_runtime.py")])

    migration_result = migrate_legacy_install(repo_root=REPO_ROOT)
    install_cli_from_skill(skill_root)

    results = {}
    existing_manifest = load_existing_manifest(REPO_ROOT)
    codex_skill = existing_manifest.codex_managed_skill_path if existing_manifest else None
    hermes_paths = existing_manifest.hermes_skill_paths if existing_manifest else ()
    openclaw_paths = existing_manifest.openclaw_skill_paths if existing_manifest else ()

    for surface in selected_surfaces:
        if surface == "codex":
            codex_skill = install_codex(REPO_ROOT)
            results[surface] = f"installed {codex_skill}"
            continue
        if surface == "hermes":
            target_paths = detection["hermes"]["skill_paths"]
            if not target_paths:
                results[surface] = "not detected"
                continue
            disabled_homes = install_hermes(skill_root, target_paths, force=args.force)
            hermes_paths = tuple(target_paths)
            if disabled_homes:
                rendered = ", ".join(str(path) for path in disabled_homes)
                results[surface] = f"blocked by config in {rendered}"
            else:
                results[surface] = f"installed {len(target_paths)} Hermes skill dirs"
            continue
        if surface == "openclaw":
            target_paths = detection["openclaw"]["skill_paths"]
            if not target_paths:
                results[surface] = "not detected"
                continue
            install_openclaw(skill_root, target_paths, force=args.force)
            openclaw_paths = tuple(target_paths)
            results[surface] = f"installed {len(target_paths)} OpenClaw skill dirs"
            continue

    layout = resolve_knowledge_layout(repo_root=REPO_ROOT)
    manifest = build_install_manifest(
        layout,
        canonical_skill_path=skill_root,
        codex_managed_skill_path=codex_skill,
        hermes_skill_paths=hermes_paths,
        openclaw_skill_paths=openclaw_paths,
        legacy_repo_root=REPO_ROOT,
    )
    write_install_manifest(manifest)
    repo = KnowledgeRepository(layout)
    repo.initialize_layout()

    if migration_result is not None:
        print(
            f"migrated legacy Fleki root to {layout.config_root}"
        )
    print(f"knowledge cli ready")
    print(f"knowledge data root: {layout.data_root}")
    print("installing or refreshing the CLI does not clear an existing graph")
    print(f"install manifest: {layout.install_manifest_path}")
    for surface in selected_surfaces:
        print(f"{surface}: {results[surface]}")
    return 0


def auto_detected_surfaces() -> tuple[str, ...]:
    detected = detect_targets()
    surfaces = []
    if detected["codex"]["detected"]:
        surfaces.append("codex")
    if detected["hermes"]["detected"]:
        surfaces.append("hermes")
    if detected["openclaw"]["detected"]:
        surfaces.append("openclaw")
    return tuple(surfaces)


def detect_targets() -> dict[str, dict[str, object]]:
    hermes_homes = discover_hermes_homes()
    openclaw_roots = discover_openclaw_roots()
    return {
        "codex": {
            "detected": shutil.which("codex") is not None and shutil.which("npx") is not None,
            "skill_paths": (codex_managed_skill_path(),),
        },
        "hermes": {
            "detected": bool(hermes_homes),
            "homes": hermes_homes,
            "skill_paths": hermes_skill_paths(),
        },
        "openclaw": {
            "detected": bool(openclaw_roots),
            "roots": openclaw_roots,
            "skill_paths": openclaw_skill_paths(),
        },
    }


def render_detection_line(surface: str, payload: dict[str, object], *, selected: bool) -> str:
    state = "selected" if selected else "not selected"
    if not payload["detected"]:
        return f"{surface}: not detected ({state})"
    targets = ", ".join(str(path) for path in payload["skill_paths"])
    return f"{surface}: detected ({state}) -> {targets}"


def install_cli_from_skill(skill_root: Path) -> None:
    if shutil.which("uv") is None:
        raise SystemExit("uv is required to install the bundled knowledge CLI.")
    runtime_dir = skill_root / "runtime"
    if not (runtime_dir / "src" / "knowledge_graph").is_dir():
        raise SystemExit(f"missing bundled runtime at {runtime_dir}")
    run_checked(["uv", "tool", "install", "--force", "--python", "3.12", str(runtime_dir)])


def install_codex(repo_root: Path) -> Path:
    if shutil.which("npx") is None:
        raise SystemExit("npx is required for the Codex install flow.")
    run_checked(
        [
            "npx",
            "skills",
            "add",
            str(repo_root),
            "-g",
            "-a",
            "codex",
            "--skill",
            KNOWLEDGE_SKILL_NAME,
            "-y",
        ]
    )
    return codex_managed_skill_path()


def install_hermes(skill_root: Path, target_paths: Sequence[Path], *, force: bool) -> tuple[Path, ...]:
    disabled = []
    for target in target_paths:
        replace = force or target.is_symlink() or (target.exists() and not target.is_dir())
        materialize_skill_copy(skill_root, target, replace=replace)
        if hermes_skill_disabled(target.parents[1]):
            disabled.append(target.parents[1])
    return tuple(disabled)


def install_openclaw(skill_root: Path, target_paths: Sequence[Path], *, force: bool) -> None:
    for target in target_paths:
        replace = force or target.is_symlink() or (target.exists() and not target.is_dir())
        materialize_skill_copy(skill_root, target, replace=replace)


def load_existing_manifest(repo_root: Path):
    layout = resolve_knowledge_layout(repo_root=repo_root)
    if not layout.install_manifest_path.exists():
        return None
    return load_install_manifest(layout.install_manifest_path)


def run_checked(command: Sequence[str]) -> None:
    subprocess.run(command, check=True)


if __name__ == "__main__":
    raise SystemExit(main())

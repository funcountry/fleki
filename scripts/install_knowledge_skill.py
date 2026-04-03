#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence


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
from knowledge_graph.layout import port_graph_frontmatter  # noqa: E402
from knowledge_graph.review_wiki.layout import (  # noqa: E402
    QUARTZ_NPM_MIN_VERSION,
    QUARTZ_PACKAGE_REFERENCE,
    QUARTZ_REQUIRED_NODE_MAJOR,
    QUARTZ_VERSION,
    resolve_review_wiki_layout,
)
from knowledge_graph.review_wiki.service import (  # noqa: E402
    REVIEW_WIKI_LAUNCHD_LABEL,
    REVIEW_WIKI_SYSTEMD_UNIT_NAME,
    launch_agent_path,
    render_launchd_plist,
    render_systemd_unit,
    systemd_user_unit_path,
)


SURFACES = ("codex", "hermes", "openclaw")
REVIEW_WIKI_TEMPLATE_FILES = (
    "README.md",
    "package.json",
    "quartz.config.ts",
    "quartz.layout.ts",
    "tsconfig.json",
)


def build_parser() -> argparse.ArgumentParser:
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
    review_group = parser.add_mutually_exclusive_group()
    review_group.add_argument(
        "--review-wiki",
        action="store_true",
        help="Also install the local review wiki daemon and service on this machine.",
    )
    review_group.add_argument(
        "--remove-review-wiki",
        action="store_true",
        help="Remove the local review wiki service and derived state from this machine.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    skill_root = REPO_ROOT / "skills" / KNOWLEDGE_SKILL_NAME
    if not skill_root.exists():
        raise SystemExit(f"missing canonical skill package: {skill_root}")

    detection = detect_targets()
    selected_surfaces = tuple(args.surface) if args.surface else auto_detected_surfaces()
    layout = resolve_knowledge_layout(repo_root=REPO_ROOT)
    review_layout = resolve_review_wiki_layout(layout)

    if args.dry_run:
        print(f"Canonical skill package: {skill_root}")
        for surface in SURFACES:
            print(render_detection_line(surface, detection[surface], selected=surface in selected_surfaces))
        if args.review_wiki:
            print(f"review-wiki: selected -> {review_layout.root}")
        elif args.remove_review_wiki:
            print(f"review-wiki: remove -> {review_layout.root}")
        elif not selected_surfaces:
            print("No supported runtime was detected on this machine.")
        return 0

    if args.remove_review_wiki:
        remove_review_wiki_install(layout)
        print(f"review-wiki removed from {review_layout.root}")
        return 0

    if not selected_surfaces and not args.review_wiki:
        print("No supported runtime was detected on this machine.")
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
    ported_files = port_existing_graph_frontmatter(layout)
    repo = KnowledgeRepository(layout)
    repo.initialize_layout()

    review_wiki_result = None
    if args.review_wiki:
        review_wiki_result = install_review_wiki(layout)

    if migration_result is not None:
        print(f"migrated legacy Fleki root to {layout.config_root}")
    if ported_files:
        print(f"ported {ported_files} graph markdown files to YAML frontmatter")
    print("knowledge cli ready")
    print(f"knowledge data root: {layout.data_root}")
    print("installing or refreshing the CLI does not clear an existing graph")
    print(f"install manifest: {layout.install_manifest_path}")
    for surface in selected_surfaces:
        print(f"{surface}: {results[surface]}")
    if review_wiki_result is not None:
        print(f"review-wiki: {review_wiki_result}")
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


def port_existing_graph_frontmatter(layout) -> int:
    return port_graph_frontmatter(layout.data_root)


def install_review_wiki(layout) -> str:
    tooling = ensure_review_wiki_tooling()
    review_layout = resolve_review_wiki_layout(layout)
    template_root = REPO_ROOT / "templates" / "review-wiki"
    materialize_review_wiki_overlay(template_root, review_layout.quartz_root)
    review_layout.content_root.mkdir(parents=True, exist_ok=True)
    review_layout.public_root.mkdir(parents=True, exist_ok=True)
    run_checked(["npm", "install"], cwd=review_layout.quartz_root)
    materialize_quartz_runtime_scaffold(review_layout.quartz_root)

    path_env = os.environ.get("PATH", "")
    if sys.platform == "darwin":
        service_path = launch_agent_path()
        service_path.parent.mkdir(parents=True, exist_ok=True)
        service_path.write_text(
            render_launchd_plist(
                repo_root=REPO_ROOT,
                uv_path=tooling["uv_path"],
                path_env=path_env,
            )
        )
        run_optional(["launchctl", "bootout", f"gui/{os.getuid()}", str(service_path)])
        run_checked(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(service_path)])
        run_checked(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{REVIEW_WIKI_LAUNCHD_LABEL}"])
    elif sys.platform.startswith("linux"):
        service_path = systemd_user_unit_path()
        service_path.parent.mkdir(parents=True, exist_ok=True)
        service_path.write_text(
            render_systemd_unit(
                repo_root=REPO_ROOT,
                uv_path=tooling["uv_path"],
                path_env=path_env,
            )
        )
        run_checked(["systemctl", "--user", "daemon-reload"])
        run_checked(["systemctl", "--user", "enable", "--now", REVIEW_WIKI_SYSTEMD_UNIT_NAME])
    else:
        raise SystemExit("review-wiki install only supports macOS and Linux")

    return f"installed -> http://127.0.0.1:4151 using Quartz {QUARTZ_PACKAGE_REFERENCE}"


def remove_review_wiki_install(layout) -> None:
    review_layout = resolve_review_wiki_layout(layout)
    if sys.platform == "darwin":
        service_path = launch_agent_path()
        if service_path.exists():
            run_optional(["launchctl", "bootout", f"gui/{os.getuid()}", str(service_path)])
            service_path.unlink()
    elif sys.platform.startswith("linux"):
        service_path = systemd_user_unit_path()
        if service_path.exists():
            run_optional(["systemctl", "--user", "disable", "--now", REVIEW_WIKI_SYSTEMD_UNIT_NAME])
            service_path.unlink()
            run_optional(["systemctl", "--user", "daemon-reload"])
    else:
        raise SystemExit("review-wiki removal only supports macOS and Linux")

    if review_layout.root.exists():
        shutil.rmtree(review_layout.root)


def ensure_review_wiki_tooling(
    *,
    runner: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Path]:
    active_runner = runner or run_checked_output
    uv_path = shutil.which("uv")
    if uv_path is None:
        raise SystemExit("uv is required to install the review wiki.")
    if shutil.which("npx") is None:
        raise SystemExit("npx is required to build the review wiki.")

    node_version = _parse_version(active_runner(["node", "--version"]), label="node")
    npm_version = _parse_version(active_runner(["npm", "--version"]), label="npm")
    required_npm = _parse_version(QUARTZ_NPM_MIN_VERSION, label="npm")

    if node_version[0] < QUARTZ_REQUIRED_NODE_MAJOR:
        raise SystemExit(
            f"review wiki requires Node >= {QUARTZ_REQUIRED_NODE_MAJOR}; found {node_version[0]}"
        )
    if npm_version < required_npm:
        raise SystemExit(
            f"review wiki requires npm >= {QUARTZ_NPM_MIN_VERSION}; found {'.'.join(str(part) for part in npm_version)}"
        )

    return {"uv_path": Path(uv_path)}


def materialize_review_wiki_overlay(template_root: Path, quartz_root: Path) -> None:
    quartz_root.mkdir(parents=True, exist_ok=True)
    for relative_name in REVIEW_WIKI_TEMPLATE_FILES:
        source = template_root / relative_name
        target = quartz_root / relative_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def materialize_quartz_runtime_scaffold(quartz_root: Path) -> None:
    source = quartz_root / "node_modules" / "@jackyzha0" / "quartz" / "quartz"
    if not source.is_dir():
        raise SystemExit(f"missing installed Quartz scaffold: {source}")
    target = quartz_root / "quartz"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _parse_version(raw: str, *, label: str) -> tuple[int, ...]:
    value = raw.strip()
    if value.startswith("v"):
        value = value[1:]
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError as exc:
        raise SystemExit(f"unable to parse {label} version from: {raw!r}") from exc


def run_checked(command: Sequence[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def run_optional(command: Sequence[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=False)


def run_checked_output(command: Sequence[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip() or result.stderr.strip()


if __name__ == "__main__":
    raise SystemExit(main())

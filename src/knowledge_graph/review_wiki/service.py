from __future__ import annotations

from pathlib import Path
from typing import Optional

from .layout import REVIEW_WIKI_HOST, REVIEW_WIKI_PORT


REVIEW_WIKI_LAUNCHD_LABEL = "dev.fleki.review-wiki"
REVIEW_WIKI_SYSTEMD_UNIT_NAME = "fleki-review-wiki.service"


def launch_agent_path(*, home: Path | str | None = None) -> Path:
    base_home = Path(home).expanduser().resolve() if home is not None else Path.home()
    return base_home / "Library" / "LaunchAgents" / f"{REVIEW_WIKI_LAUNCHD_LABEL}.plist"


def systemd_user_unit_path(*, home: Path | str | None = None) -> Path:
    base_home = Path(home).expanduser().resolve() if home is not None else Path.home()
    return base_home / ".config" / "systemd" / "user" / REVIEW_WIKI_SYSTEMD_UNIT_NAME


def render_launchd_plist(
    *,
    repo_root: Path,
    uv_path: Path,
    path_env: Optional[str] = None,
) -> str:
    env_block = ""
    if path_env:
        env_block = (
            "  <key>EnvironmentVariables</key>\n"
            "  <dict>\n"
            "    <key>PATH</key>\n"
            f"    <string>{path_env}</string>\n"
            "  </dict>\n"
        )
    arguments = [
        str(uv_path),
        "run",
        "--project",
        str(repo_root),
        "python",
        "-m",
        "knowledge_graph.review_wiki.daemon",
        "--repo-root",
        str(repo_root),
    ]
    argument_lines = "\n".join(f"      <string>{arg}</string>" for arg in arguments)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
        "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
        "<plist version=\"1.0\">\n"
        "<dict>\n"
        "  <key>Label</key>\n"
        f"  <string>{REVIEW_WIKI_LAUNCHD_LABEL}</string>\n"
        "  <key>ProgramArguments</key>\n"
        "  <array>\n"
        f"{argument_lines}\n"
        "  </array>\n"
        "  <key>RunAtLoad</key>\n"
        "  <true/>\n"
        "  <key>KeepAlive</key>\n"
        "  <true/>\n"
        "  <key>WorkingDirectory</key>\n"
        f"  <string>{repo_root}</string>\n"
        f"{env_block}"
        "</dict>\n"
        "</plist>\n"
    )


def render_systemd_unit(
    *,
    repo_root: Path,
    uv_path: Path,
    path_env: Optional[str] = None,
) -> str:
    environment_line = ""
    if path_env:
        environment_line = f'Environment="PATH={path_env}"\n'
    exec_start = (
        f"{uv_path} run --project {repo_root} python -m "
        "knowledge_graph.review_wiki.daemon "
        f"--repo-root {repo_root}"
    )
    return (
        "[Unit]\n"
        "Description=Fleki knowledge review wiki daemon\n"
        "After=network.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"WorkingDirectory={repo_root}\n"
        f"{environment_line}"
        f"ExecStart={exec_start}\n"
        "Restart=on-failure\n"
        f"Environment=FLEKI_REVIEW_WIKI_BIND={REVIEW_WIKI_HOST}:{REVIEW_WIKI_PORT}\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )

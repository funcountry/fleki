from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def _skill_dir(repo_root: Path | str) -> Path:
    return Path(repo_root) / "skills_or_tools" / "knowledge"


def _codex_workspace_skill_dir(repo_root: Path | str) -> Path:
    return Path(repo_root) / ".agents" / "skills" / "knowledge"


def _hermes_repo_shared_skill_dir() -> Path:
    return Path("/Users/agents/workspace/agents/agents/_shared/skills/knowledge")


def _hermes_trusted_skill_dir() -> Path:
    return Path("/Users/agents/.hermes/skills/knowledge")


def _paperclip_repo_skill_dir() -> Path:
    return Path("/Users/agents/workspace/paperclip_agents/skills/knowledge")


def codex_runtime_manifest(repo_root: Path | str) -> Dict[str, object]:
    skill_dir = _skill_dir(repo_root)
    return {
        "runtime": "codex",
        "skill_name": "knowledge",
        "skill_path": str(skill_dir),
        "workspace_publication_path": str(_codex_workspace_skill_dir(repo_root)),
        "install_hint": "publish into workspace .agents/skills for direct local Codex discovery",
        "contract_verbs": ["save", "search", "trace", "rebuild", "status"],
    }


def hermes_runtime_manifest(repo_root: Path | str) -> Dict[str, object]:
    skill_dir = _skill_dir(repo_root)
    return {
        "runtime": "hermes",
        "skill_name": "knowledge",
        "skill_path": str(skill_dir),
        "repo_shared_publication_path": str(_hermes_repo_shared_skill_dir()),
        "trusted_runtime_publication_path": str(_hermes_trusted_skill_dir()),
        "skills_external_dirs": ["/Users/agents/workspace/agents/agents/_shared/skills"],
        "wrapping": "shared skill publication plus optional slash/tool wrapping only",
        "contract_verbs": ["save", "search", "trace", "rebuild", "status"],
    }


def paperclip_runtime_manifest(repo_root: Path | str) -> Dict[str, object]:
    skill_dir = _skill_dir(repo_root)
    return {
        "runtime": "paperclip_codex_local",
        "skill_name": "knowledge",
        "skill_path": str(skill_dir),
        "repo_owned_publication_path": str(_paperclip_repo_skill_dir()),
        "workspace_publication_path": str(_codex_workspace_skill_dir(repo_root)),
        "desired_skills": ["knowledge"],
        "distribution_model": "reuse the Codex lane without a Paperclip-only backend",
        "contract_verbs": ["save", "search", "trace", "rebuild", "status"],
    }

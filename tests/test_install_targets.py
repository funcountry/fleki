from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from knowledge_graph.install_targets import (
    codex_managed_install_root,
    codex_managed_skill_path,
    discover_hermes_homes,
    discover_openclaw_roots,
    hermes_skill_disabled,
    hermes_skill_paths,
    materialize_skill_copy,
    openclaw_skill_paths,
)


class InstallTargetsTest(unittest.TestCase):
    def test_codex_managed_paths_use_standard_root(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = (Path(temp_dir.name) / "home").resolve()

        self.assertEqual(codex_managed_install_root(home=home), home / ".agents" / "skills")
        self.assertEqual(
            codex_managed_skill_path(home=home),
            home / ".agents" / "skills" / "knowledge",
        )

    def test_hermes_discovery_uses_env_default_and_profiles(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = (Path(temp_dir.name) / "home").resolve()
        default_home = home / ".hermes"
        env_home = default_home / "profiles" / "agent_special"
        other_home = default_home / "profiles" / "agent_writer"
        for path in [default_home, env_home, other_home]:
            (path / "skills").mkdir(parents=True, exist_ok=True)

        with patch.dict("os.environ", {"HERMES_HOME": str(env_home)}, clear=False), patch(
            "knowledge_graph.install_targets._hermes_profile_homes_from_cli",
            return_value=(env_home, other_home),
        ):
            homes = discover_hermes_homes(home=home)
            with patch(
                "knowledge_graph.install_targets.discover_hermes_homes",
                return_value=homes,
            ):
                skill_paths = hermes_skill_paths(home=home)

        self.assertEqual(homes, (env_home, default_home, other_home))
        self.assertEqual(
            skill_paths,
            (
                env_home / "skills" / "knowledge",
                default_home / "skills" / "knowledge",
                other_home / "skills" / "knowledge",
            ),
        )

    def test_hermes_disabled_detection_reads_config_yaml(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        hermes_home = Path(temp_dir.name) / ".hermes" / "profiles" / "agent_special"
        hermes_home.mkdir(parents=True, exist_ok=True)
        (hermes_home / "config.yaml").write_text(
            "skills:\n"
            "  disabled:\n"
            "    - github-auth\n"
            "    - knowledge\n"
        )

        self.assertTrue(hermes_skill_disabled(hermes_home))

    def test_openclaw_discovery_uses_live_root_and_profile_roots(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = (Path(temp_dir.name) / "home").resolve()
        default_root = home / ".openclaw"
        dev_root = home / ".openclaw-dev"
        extra_root = home / ".openclaw-work"
        for path in [default_root, dev_root, extra_root]:
            (path / "skills").mkdir(parents=True, exist_ok=True)

        with patch(
            "knowledge_graph.install_targets._openclaw_root_from_live_skills",
            return_value=default_root,
        ):
            roots = discover_openclaw_roots(home=home)
            with patch(
                "knowledge_graph.install_targets.discover_openclaw_roots",
                return_value=roots,
            ):
                skill_paths = openclaw_skill_paths(home=home)

        self.assertEqual(roots, (default_root, dev_root, extra_root))
        self.assertEqual(
            skill_paths,
            (
                default_root / "skills" / "knowledge",
                dev_root / "skills" / "knowledge",
                extra_root / "skills" / "knowledge",
            ),
        )

    def test_materialize_skill_copy_replaces_symlink_with_real_tree(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        source_skill = root / "source" / "knowledge"
        target_skill = root / "target" / "skills" / "knowledge"
        source_skill.mkdir(parents=True, exist_ok=True)
        (source_skill / "SKILL.md").write_text("# knowledge\n")
        (source_skill / "references").mkdir()
        (source_skill / "references" / "save-ingestion.md").write_text("save\n")

        target_skill.parent.mkdir(parents=True, exist_ok=True)
        target_skill.symlink_to(source_skill, target_is_directory=True)

        materialize_skill_copy(source_skill, target_skill)

        self.assertTrue(target_skill.is_dir())
        self.assertFalse(target_skill.is_symlink())
        self.assertEqual((target_skill / "SKILL.md").read_text(), "# knowledge\n")
        self.assertEqual(
            (target_skill / "references" / "save-ingestion.md").read_text(),
            "save\n",
        )


if __name__ == "__main__":
    unittest.main()

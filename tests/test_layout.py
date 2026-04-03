from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from common import ROOT
from knowledge_graph import (
    KnowledgeRepository,
    ValidationError,
    build_install_manifest,
    default_config_root,
    default_data_root,
    default_install_manifest_path,
    default_root,
    default_state_root,
    load_install_manifest,
    migrate_legacy_install,
    migrate_legacy_repo_graph,
    resolve_knowledge_layout,
    write_install_manifest,
)
from knowledge_graph.frontmatter import dump_frontmatter


class LayoutContractTest(unittest.TestCase):
    def test_default_layout_uses_dot_fleki_root(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = (Path(temp_dir.name) / "home").resolve()
        home.mkdir(parents=True, exist_ok=True)

        layout = resolve_knowledge_layout(home=home)

        self.assertEqual(default_root(home=home), home / ".fleki")
        self.assertEqual(default_config_root(home=home), home / ".fleki")
        self.assertEqual(default_data_root(home=home), home / ".fleki" / "knowledge")
        self.assertEqual(default_state_root(home=home), home / ".fleki" / "state")
        self.assertEqual(default_install_manifest_path(home=home), home / ".fleki" / "install.json")
        self.assertEqual(layout.config_root, home / ".fleki")
        self.assertEqual(layout.data_root, home / ".fleki" / "knowledge")
        self.assertEqual(layout.state_root, home / ".fleki" / "state")
        self.assertEqual(layout.install_manifest_path, home / ".fleki" / "install.json")

    def test_install_manifest_round_trip_and_resolution_precedence(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        shared_skill_target = root / "shared-install" / "knowledge"
        shared_skill_target.mkdir(parents=True, exist_ok=True)
        codex_link = root / "codex-home" / "skills" / "knowledge"
        codex_link.parent.mkdir(parents=True, exist_ok=True)
        codex_link.symlink_to(shared_skill_target, target_is_directory=True)
        layout = resolve_knowledge_layout(
            data_root=root / "data-root",
            config_root=root / "config-root",
            state_root=root / "state-root",
            install_manifest_path=root / "config-root" / "install.json",
            repo_root=root,
        )
        manifest = build_install_manifest(
            layout,
            canonical_skill_path=ROOT / "skills" / "knowledge",
            codex_managed_skill_path=Path.home() / ".agents" / "skills" / "knowledge",
            hermes_skill_paths=(root / "external-runtime-skills" / "knowledge",),
            openclaw_skill_paths=(root / "openclaw-runtime" / "skills" / "knowledge",),
            legacy_repo_root=root,
        )
        manifest_path = write_install_manifest(manifest)

        reloaded_manifest = load_install_manifest(manifest_path)
        resolved = resolve_knowledge_layout(
            install_manifest_path=manifest_path,
            repo_root=root,
        )
        self.assertEqual(reloaded_manifest.data_root, layout.data_root)
        self.assertEqual(resolved.data_root, layout.data_root)
        self.assertEqual(resolved.install_manifest_path, manifest_path)
        self.assertEqual(
            reloaded_manifest.codex_managed_skill_path,
            Path.home() / ".agents" / "skills" / "knowledge",
        )
        self.assertEqual(
            reloaded_manifest.hermes_skill_paths,
            (root / "external-runtime-skills" / "knowledge",),
        )
        self.assertEqual(
            reloaded_manifest.openclaw_skill_paths,
            (root / "openclaw-runtime" / "skills" / "knowledge",),
        )

        with self.assertRaises(ValidationError):
            resolve_knowledge_layout(
                data_root=root / "different-data-root",
                install_manifest_path=manifest_path,
                repo_root=root,
            )

    def test_migrate_legacy_repo_graph_copies_into_explicit_data_root(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        legacy_topic = root / "knowledge" / "topics" / "doctrine" / "shared-agent-learnings.md"
        legacy_topic.parent.mkdir(parents=True, exist_ok=True)
        legacy_topic.write_text(
            dump_frontmatter(
                {"current_path": "doctrine/shared-agent-learnings"},
                "# Legacy Topic\n\n## Provenance Notes\n- `knowledge/provenance/other/prov_legacy.md`\n",
            )
        )
        (root / "knowledge" / "README.md").write_text("# Legacy Graph\n")
        legacy_provenance = root / "knowledge" / "provenance" / "other" / "prov_legacy.md"
        legacy_provenance.parent.mkdir(parents=True, exist_ok=True)
        legacy_provenance.write_text(
            dump_frontmatter(
                {
                    "provenance_id": "prov_legacy",
                    "source_record_paths": [
                        "knowledge/sources/other/legacy.record.json",
                    ],
                },
                "# Legacy Provenance\n",
            )
        )
        legacy_source_record = root / "knowledge" / "sources" / "other" / "legacy.record.json"
        legacy_source_record.parent.mkdir(parents=True, exist_ok=True)
        legacy_source_record.write_text(
            '{\n  "relative_path": "knowledge/sources/other/legacy.md"\n}\n'
        )

        layout = resolve_knowledge_layout(
            data_root=root / "data-root",
            config_root=root / "config-root",
            state_root=root / "state-root",
            install_manifest_path=root / "config-root" / "install.json",
            repo_root=root,
        )

        result = migrate_legacy_repo_graph(repo_root=root, layout=layout)
        self.assertTrue(result["verified"])
        self.assertTrue(result["switched"])
        self.assertGreaterEqual(result["rewritten_files"], 3)
        migrated_topic = layout.data_root / "topics" / "doctrine" / "shared-agent-learnings.md"
        self.assertTrue(migrated_topic.exists())
        topic_text = migrated_topic.read_text()
        self.assertIn("`provenance/other/prov_legacy.md`", topic_text)
        self.assertNotIn("`knowledge/provenance/other/prov_legacy.md`", topic_text)
        provenance_text = (layout.data_root / "provenance" / "other" / "prov_legacy.md").read_text()
        self.assertIn('"source_record_paths": [\n    "sources/other/legacy.record.json"\n  ]', provenance_text)
        source_record_text = (layout.data_root / "sources" / "other" / "legacy.record.json").read_text()
        self.assertIn('"relative_path": "sources/other/legacy.md"', source_record_text)

    def test_migrate_legacy_install_moves_old_root_into_dot_fleki_and_deletes_source(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = (Path(temp_dir.name) / "home").resolve()
        home.mkdir(parents=True, exist_ok=True)
        repo_root = Path(temp_dir.name) / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)

        old_config_root = home / "Library" / "Application Support" / "Fleki"
        old_layout = resolve_knowledge_layout(
            data_root=old_config_root / "knowledge",
            config_root=old_config_root,
            state_root=old_config_root / "state",
            install_manifest_path=old_config_root / "install.json",
            repo_root=repo_root,
        )
        old_manifest = build_install_manifest(
            old_layout,
            canonical_skill_path=ROOT / "skills" / "knowledge",
            codex_managed_skill_path=Path.home() / ".agents" / "skills" / "knowledge",
            hermes_skill_paths=(home / ".hermes" / "profiles" / "agent_growth_analyst" / "skills" / "knowledge",),
            openclaw_skill_paths=(home / ".openclaw" / "skills" / "knowledge",),
            legacy_repo_root=repo_root,
        )
        write_install_manifest(old_manifest)
        old_repo = resolve_knowledge_layout(
            install_manifest_path=old_layout.install_manifest_path,
            repo_root=repo_root,
        )
        legacy_repo = KnowledgeRepository(old_repo)
        legacy_repo.initialize_layout()
        topic_path = legacy_repo.data_root / "topics" / "product" / "legacy.md"
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        topic_path.write_text(
            dump_frontmatter(
                {"knowledge_id": "kg_legacy", "current_path": "product/legacy", "page_kind": "topic"},
                "# Legacy\n",
            )
        )

        result = migrate_legacy_install(repo_root=repo_root, home=home)

        self.assertIsNotNone(result)
        self.assertEqual(result["kind"], "legacy_install")
        new_layout = resolve_knowledge_layout(home=home, repo_root=repo_root)
        self.assertEqual(new_layout.config_root, home / ".fleki")
        self.assertTrue((new_layout.config_root / "install.json").exists())
        self.assertTrue((new_layout.data_root / "topics" / "product" / "legacy.md").exists())
        self.assertFalse(old_config_root.exists())

    def test_migrate_legacy_xdg_install_moves_old_root_into_dot_fleki(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = (Path(temp_dir.name) / "home").resolve()
        home.mkdir(parents=True, exist_ok=True)
        repo_root = Path(temp_dir.name) / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)

        old_layout = resolve_knowledge_layout(
            data_root=home / ".local" / "share" / "fleki" / "knowledge",
            config_root=home / ".config" / "fleki",
            state_root=home / ".local" / "state" / "fleki",
            install_manifest_path=home / ".config" / "fleki" / "install.json",
            repo_root=repo_root,
        )
        old_manifest = build_install_manifest(
            old_layout,
            canonical_skill_path=ROOT / "skills" / "knowledge",
            codex_managed_skill_path=Path.home() / ".agents" / "skills" / "knowledge",
            hermes_skill_paths=(),
            openclaw_skill_paths=(),
            legacy_repo_root=repo_root,
        )
        write_install_manifest(old_manifest)
        (old_layout.data_root / "topics" / "indexes").mkdir(parents=True, exist_ok=True)
        (old_layout.data_root / "topics" / "indexes" / "README.md").write_text("# Indexes\n")
        (old_layout.state_root / "receipts").mkdir(parents=True, exist_ok=True)
        (old_layout.state_root / "receipts" / "migration.txt").write_text("ok\n")

        result = migrate_legacy_install(repo_root=repo_root, home=home)

        self.assertIsNotNone(result)
        self.assertEqual(result["kind"], "legacy_install")
        new_layout = resolve_knowledge_layout(home=home, repo_root=repo_root)
        self.assertTrue((new_layout.data_root / "topics" / "indexes" / "README.md").exists())
        self.assertTrue((new_layout.state_root / "receipts" / "migration.txt").exists())
        self.assertFalse((home / ".config" / "fleki").exists())
        self.assertFalse((home / ".local" / "state" / "fleki").exists())
        self.assertFalse((home / ".local" / "share" / "fleki" / "knowledge").exists())


if __name__ == "__main__":
    unittest.main()

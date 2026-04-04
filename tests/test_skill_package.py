from __future__ import annotations

import unittest
from pathlib import Path


class SkillPackageTest(unittest.TestCase):
    def test_knowledge_skill_package_exists_in_one_canonical_repo_path(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_root = root / "skills" / "knowledge"
        runtime_root = skill_root / "runtime"
        repo_readme = root / "README.md"
        repo_install_script = root / "install.sh"
        runtime_sync_script = root / "scripts" / "sync_knowledge_runtime.py"
        repo_installer_script = root / "scripts" / "install_knowledge_skill.py"
        backfill_script = root / "scripts" / "backfill_pdf_render_contract.py"
        source_family_repair_script = root / "scripts" / "backfill_source_family.py"

        self.assertTrue(skill_root.exists(), msg=str(skill_root))
        self.assertTrue((skill_root / "SKILL.md").exists())
        self.assertFalse((root / "skills_or_tools" / "knowledge").exists())
        self.assertFalse((root / ".agents" / "skills" / "knowledge").exists())

        skill_text = (skill_root / "SKILL.md").read_text()
        self.assertIn("key: fleki/knowledge", skill_text)
        self.assertIn("knowledge save", skill_text)
        self.assertIn("knowledge search", skill_text)
        self.assertIn("knowledge trace", skill_text)
        self.assertIn("knowledge rebuild", skill_text)
        self.assertIn("knowledge status", skill_text)

        references = [
            skill_root / "references" / "save-ingestion.md",
            skill_root / "references" / "search-and-trace.md",
            skill_root / "references" / "storage-and-authority.md",
            skill_root / "references" / "examples-and-validation.md",
            skill_root / "references" / "examples" / "minimal-save-bindings.json",
            skill_root / "references" / "examples" / "minimal-save-decision.json",
            skill_root / "install" / "README.md",
            skill_root / "install" / "bootstrap.sh",
        ]
        for reference in references:
            self.assertTrue(reference.exists(), msg=str(reference))

        self.assertTrue(repo_readme.exists(), msg=str(repo_readme))
        self.assertTrue(repo_install_script.exists(), msg=str(repo_install_script))
        self.assertTrue(runtime_sync_script.exists(), msg=str(runtime_sync_script))
        self.assertTrue(repo_installer_script.exists(), msg=str(repo_installer_script))
        self.assertTrue(backfill_script.exists(), msg=str(backfill_script))
        self.assertTrue(source_family_repair_script.exists(), msg=str(source_family_repair_script))

        readme_text = repo_readme.read_text()
        self.assertIn("./install.sh", readme_text)
        self.assertIn("--dry-run", readme_text)
        self.assertIn("$HOME/.fleki/knowledge", readme_text)
        self.assertIn("--review-wiki", readme_text)
        self.assertIn("--remove-review-wiki", readme_text)
        self.assertIn("127.0.0.1:4151", readme_text)
        self.assertIn("Hermes", readme_text)
        self.assertIn("OpenClaw", readme_text)
        self.assertIn("knowledge save", readme_text)
        self.assertNotIn("knowledge preview", readme_text)

        install_script_text = repo_install_script.read_text()
        self.assertIn("scripts/install_knowledge_skill.py", install_script_text)
        self.assertNotIn("export_knowledge_skill_bundle.py", install_script_text)
        self.assertNotIn("--external-root", install_script_text)

        generated_runtime_files = [
            "runtime/README.md",
            "runtime/pyproject.toml",
            "runtime/src/knowledge_graph/__init__.py",
            "runtime/src/knowledge_graph/cli.py",
            "runtime/src/knowledge_graph/pdf_render.py",
            "runtime/src/knowledge_graph/repository.py",
            "runtime/src/knowledge_graph/install_targets.py",
        ]
        for relative_name in generated_runtime_files:
            self.assertTrue((skill_root / relative_name).exists(), msg=relative_name)
        self.assertFalse((runtime_root / "src" / "knowledge_graph" / "review_wiki").exists())
        self.assertFalse((runtime_root / "templates" / "review-wiki").exists())

        runtime_pyproject = (runtime_root / "pyproject.toml").read_text()
        self.assertIn('knowledge = "knowledge_graph.cli:main"', runtime_pyproject)
        self.assertIn('"docling>=2.69,<3"', runtime_pyproject)
        self.assertIn('"PyYAML>=6,<7"', runtime_pyproject)

        runtime_repository = (runtime_root / "src" / "knowledge_graph" / "repository.py").read_text()
        self.assertIn('"artifacts_by_source"', runtime_repository)
        self.assertIn("def _artifact_summary_from_manifest(", runtime_repository)
        self.assertFalse((runtime_root / "src" / "knowledge_graph" / "review_wiki").exists())

        runtime_readme = (runtime_root / "README.md").read_text()
        self.assertIn("Minimal valid save example", runtime_readme)
        self.assertIn("Create `bindings.json`", runtime_readme)
        self.assertIn("Create `decision.json`", runtime_readme)
        self.assertIn("bindings must include `source_family`", runtime_readme)
        self.assertIn("bindings must include `timestamp`", runtime_readme)
        self.assertIn("`knowledge trace` accepts exact refs only", runtime_readme)
        self.assertIn("page-level trace returns `supported_sections`", runtime_readme)
        self.assertIn("`knowledge search` stays literal", runtime_readme)
        self.assertIn("`ingests_with_confidence_caveats`", runtime_readme)
        self.assertIn("`ingest_summary.authority_tier`", runtime_readme)
        self.assertIn("`knowledge_units[].authority_posture`", runtime_readme)
        self.assertIn('`knowledge_units[].kind`: `fact`', runtime_readme)
        self.assertIn('"kind": "fact"', runtime_readme)
        self.assertNotIn("knowledge preview", runtime_readme)
        self.assertIn("knowledge save --bindings bindings.json --decision decision.json", runtime_readme)

        bootstrap_text = (skill_root / "install" / "bootstrap.sh").read_text()
        self.assertIn("uv tool install --force --python 3.12", bootstrap_text)
        self.assertIn("migrate_legacy_install", bootstrap_text)
        self.assertIn("build_install_manifest", bootstrap_text)
        self.assertNotIn("npx skills add", bootstrap_text)


if __name__ == "__main__":
    unittest.main()

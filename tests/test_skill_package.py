from __future__ import annotations

import unittest
from pathlib import Path


class SkillPackageTest(unittest.TestCase):
    def test_knowledge_skill_package_exists(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_path = root / "skills_or_tools" / "knowledge" / "SKILL.md"
        self.assertTrue(skill_path.exists())
        text = skill_path.read_text()
        self.assertIn("knowledge save", text)
        self.assertIn("knowledge search", text)
        self.assertIn("knowledge trace", text)
        self.assertIn("knowledge rebuild", text)
        self.assertIn("knowledge status", text)

        references = [
            root / "skills_or_tools" / "knowledge" / "references" / "save-ingestion.md",
            root / "skills_or_tools" / "knowledge" / "references" / "search-and-trace.md",
            root / "skills_or_tools" / "knowledge" / "references" / "storage-and-authority.md",
            root / "skills_or_tools" / "knowledge" / "references" / "examples-and-validation.md",
        ]
        for reference in references:
            self.assertTrue(reference.exists(), msg=str(reference))

        workspace_publication = root / ".agents" / "skills" / "knowledge"
        self.assertTrue(workspace_publication.exists(), msg=str(workspace_publication))
        self.assertTrue((workspace_publication / "SKILL.md").exists())
        for reference_name in [
            "save-ingestion.md",
            "search-and-trace.md",
            "storage-and-authority.md",
            "examples-and-validation.md",
        ]:
            self.assertTrue(
                (workspace_publication / "references" / reference_name).exists(),
                msg=reference_name,
            )


if __name__ == "__main__":
    unittest.main()

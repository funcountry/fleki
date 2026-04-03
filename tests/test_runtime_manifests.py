from __future__ import annotations

import unittest
from pathlib import Path

from common import ROOT
from knowledge_graph import (
    codex_runtime_manifest,
    hermes_runtime_manifest,
    paperclip_runtime_manifest,
)


class RuntimeManifestTest(unittest.TestCase):
    def test_runtime_manifests_point_at_shared_skill(self) -> None:
        codex = codex_runtime_manifest(ROOT)
        hermes = hermes_runtime_manifest(ROOT)
        paperclip = paperclip_runtime_manifest(ROOT)

        expected_skill_path = str(ROOT / "skills_or_tools" / "knowledge")
        expected_codex_publication = str(ROOT / ".agents" / "skills" / "knowledge")

        self.assertEqual(codex["skill_path"], expected_skill_path)
        self.assertEqual(hermes["skill_path"], expected_skill_path)
        self.assertEqual(paperclip["skill_path"], expected_skill_path)
        self.assertEqual(codex["workspace_publication_path"], expected_codex_publication)
        self.assertEqual(paperclip["workspace_publication_path"], expected_codex_publication)
        self.assertIn("knowledge", paperclip["desired_skills"])
        self.assertEqual(
            hermes["skills_external_dirs"],
            ["/Users/agents/workspace/agents/agents/_shared/skills"],
        )
        self.assertEqual(
            hermes["repo_shared_publication_path"],
            "/Users/agents/workspace/agents/agents/_shared/skills/knowledge",
        )
        self.assertEqual(
            hermes["trusted_runtime_publication_path"],
            "/Users/agents/.hermes/skills/knowledge",
        )
        self.assertEqual(
            paperclip["repo_owned_publication_path"],
            "/Users/agents/workspace/paperclip_agents/skills/knowledge",
        )


if __name__ == "__main__":
    unittest.main()

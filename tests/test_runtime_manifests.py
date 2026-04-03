from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from common import ROOT
from knowledge_graph import (
    codex_runtime_manifest,
    hermes_runtime_manifest,
    openclaw_runtime_manifest,
    resolve_knowledge_layout,
)


class RuntimeManifestTest(unittest.TestCase):
    def test_runtime_manifests_use_native_runtime_targets(self) -> None:
        layout = resolve_knowledge_layout(
            data_root=Path("/tmp/fleki-test-data-root"),
            config_root=Path("/tmp/fleki-test-config-root"),
            state_root=Path("/tmp/fleki-test-state-root"),
            install_manifest_path=Path("/tmp/fleki-test-config-root/install.json"),
            repo_root=ROOT,
        )
        env = {
            "HOME": "/tmp/fleki-test-home",
            "HERMES_HOME": "/tmp/fleki-test-home/.hermes/profiles/agent_special",
        }
        with patch.dict("os.environ", env, clear=False), patch(
            "knowledge_graph.runtime_manifests.discover_hermes_homes",
            return_value=(
                Path("/tmp/fleki-test-home/.hermes/profiles/agent_special"),
                Path("/tmp/fleki-test-home/.hermes/profiles/agent_writer"),
            ),
        ), patch(
            "knowledge_graph.runtime_manifests.hermes_skill_paths",
            return_value=(
                Path("/tmp/fleki-test-home/.hermes/profiles/agent_special/skills/knowledge"),
                Path("/tmp/fleki-test-home/.hermes/profiles/agent_writer/skills/knowledge"),
            ),
        ), patch(
            "knowledge_graph.runtime_manifests.discover_openclaw_roots",
            return_value=(
                Path("/tmp/fleki-test-home/.openclaw"),
                Path("/tmp/fleki-test-home/.openclaw-dev"),
            ),
        ), patch(
            "knowledge_graph.runtime_manifests.openclaw_skill_paths",
            return_value=(
                Path("/tmp/fleki-test-home/.openclaw/skills/knowledge"),
                Path("/tmp/fleki-test-home/.openclaw-dev/skills/knowledge"),
            ),
        ):
            codex = codex_runtime_manifest(ROOT, layout=layout)
            hermes = hermes_runtime_manifest(ROOT, layout=layout)
            openclaw = openclaw_runtime_manifest(ROOT, layout=layout)

        expected_skill_package_path = str(ROOT / "skills" / "knowledge")
        expected_codex_skill_path = "/tmp/fleki-test-home/.agents/skills/knowledge"

        self.assertEqual(codex["skill_package_path"], expected_skill_package_path)
        self.assertEqual(hermes["skill_package_path"], expected_skill_package_path)
        self.assertEqual(openclaw["skill_package_path"], expected_skill_package_path)
        self.assertEqual(codex["data_root"], str(layout.data_root))
        self.assertEqual(codex["install_manifest_path"], str(layout.install_manifest_path))
        self.assertEqual(codex["adapter_mode"], "upstream_global_manager")
        self.assertEqual(hermes["adapter_mode"], "per_home_native_copy")
        self.assertEqual(
            openclaw["adapter_mode"],
            "per_root_native_copy",
        )
        self.assertEqual(codex["target_skill_paths"], [expected_codex_skill_path])
        self.assertEqual(
            hermes["target_skill_paths"],
            [
                "/tmp/fleki-test-home/.hermes/profiles/agent_special/skills/knowledge",
                "/tmp/fleki-test-home/.hermes/profiles/agent_writer/skills/knowledge",
            ],
        )
        self.assertEqual(
            openclaw["target_skill_paths"],
            [
                "/tmp/fleki-test-home/.openclaw/skills/knowledge",
                "/tmp/fleki-test-home/.openclaw-dev/skills/knowledge",
            ],
        )
        self.assertEqual(openclaw["canonical_skill_key"], "fleki/knowledge")
        self.assertIn("Hermes profiles", " ".join(hermes["notes"]))
        self.assertIn("OpenClaw", " ".join(openclaw["notes"]))


if __name__ == "__main__":
    unittest.main()

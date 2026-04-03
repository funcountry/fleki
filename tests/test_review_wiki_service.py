from __future__ import annotations

import unittest
from pathlib import Path

from knowledge_graph.review_wiki.service import (
    REVIEW_WIKI_LAUNCHD_LABEL,
    REVIEW_WIKI_SYSTEMD_UNIT_NAME,
    launch_agent_path,
    render_launchd_plist,
    render_systemd_unit,
    systemd_user_unit_path,
)


class ReviewWikiServiceTest(unittest.TestCase):
    def test_launchd_plist_renders_expected_command_and_label(self) -> None:
        repo_root = Path("/tmp/fleki-review-wiki")
        uv_path = Path("/usr/local/bin/uv")

        rendered = render_launchd_plist(repo_root=repo_root, uv_path=uv_path, path_env="/usr/bin:/bin")

        self.assertIn(REVIEW_WIKI_LAUNCHD_LABEL, rendered)
        self.assertIn("<string>/usr/local/bin/uv</string>", rendered)
        self.assertIn("<string>knowledge_graph.review_wiki.daemon</string>", rendered)
        self.assertIn("<string>--repo-root</string>", rendered)
        self.assertIn("<string>/tmp/fleki-review-wiki</string>", rendered)
        self.assertIn("<key>EnvironmentVariables</key>", rendered)

    def test_systemd_unit_renders_expected_command_and_unit_name(self) -> None:
        repo_root = Path("/tmp/fleki-review-wiki")
        uv_path = Path("/usr/local/bin/uv")

        rendered = render_systemd_unit(repo_root=repo_root, uv_path=uv_path, path_env="/usr/bin:/bin")

        self.assertIn("Description=Fleki knowledge review wiki daemon", rendered)
        self.assertIn("ExecStart=/usr/local/bin/uv run --project /tmp/fleki-review-wiki python -m knowledge_graph.review_wiki.daemon --repo-root /tmp/fleki-review-wiki", rendered)
        self.assertIn('Environment="PATH=/usr/bin:/bin"', rendered)
        self.assertIn("WantedBy=default.target", rendered)
        self.assertEqual(REVIEW_WIKI_SYSTEMD_UNIT_NAME, "fleki-review-wiki.service")

    def test_service_paths_match_platform_conventions(self) -> None:
        home = Path("/tmp/home")

        self.assertEqual(
            launch_agent_path(home=home),
            home.resolve() / "Library" / "LaunchAgents" / f"{REVIEW_WIKI_LAUNCHD_LABEL}.plist",
        )
        self.assertEqual(
            systemd_user_unit_path(home=home),
            home.resolve() / ".config" / "systemd" / "user" / REVIEW_WIKI_SYSTEMD_UNIT_NAME,
        )


if __name__ == "__main__":
    unittest.main()

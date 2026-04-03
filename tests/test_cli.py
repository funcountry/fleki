from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph.cli import main


class CliContractTest(unittest.TestCase):
    def test_save_help_mentions_temporal_contract_and_bundled_readme(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as exit_info:
                main(["save", "--help"])

        self.assertEqual(exit_info.exception.code, 0)
        rendered = stdout.getvalue()
        self.assertIn('Bindings may include "timestamp"', rendered)
        self.assertIn("knowledge_units[].temporal_scope", rendered)
        self.assertIn("topic_actions[].lifecycle_state", rendered)
        self.assertIn("bundled runtime README.md", rendered)

    def test_status_command_reports_resolved_root_as_json(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "status",
                    "--json",
                    "--no-receipt",
                    "--install-manifest-path",
                    str(repo.install_manifest_path),
                    "--repo-root",
                    str(root),
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["resolved_data_root"], str(repo.data_root))
        self.assertEqual(payload["install_manifest_path"], str(repo.install_manifest_path))

    def test_save_command_renders_pdf_bundle(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        pdf_path = copy_fixture_pdf(root, "cli-fixture.pdf")
        bindings_path = root / "bindings.json"
        decision_path = root / "decision.json"

        bindings_payload = [
            {
                "source_id": "pdf.cli.fixture",
                "local_path": str(pdf_path),
                "source_kind": "pdf_research",
                "authority_tier": "historical_support",
                "sensitivity": "internal",
                "preserve_mode": "copy",
            }
        ]
        decision_payload = sample_save_decision(
            source_ids=["pdf.cli.fixture"],
            topic_path="product/cli/pdf-runtime",
            candidate_title="CLI PDF Runtime",
        )
        decision_payload["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"

        bindings_path.write_text(json.dumps(bindings_payload))
        decision_path.write_text(json.dumps(decision_payload))

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "save",
                    "--json",
                    "--bindings",
                    str(bindings_path),
                    "--decision",
                    str(decision_path),
                    "--install-manifest-path",
                    str(repo.install_manifest_path),
                    "--repo-root",
                    str(root),
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["result"], "applied")

        render_markdowns = sorted((repo.data_root / "sources" / "pdf").glob("*.render.md"))
        render_manifests = sorted((repo.data_root / "sources" / "pdf").glob("*.render.manifest.json"))
        self.assertEqual(len(render_markdowns), 1)
        self.assertEqual(len(render_manifests), 1)
        self.assertIn("Semantic knowledge graph smoke PDF", render_markdowns[0].read_text())

    def test_rebuild_plan_parses_lifecycle_and_delete_fields(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "slack-first.md"
        source_path.write_text("Slack-first authoring guidance.\n")

        from knowledge_graph import SourceBinding

        binding = SourceBinding(
            source_id="codex.session.slack-first",
            local_path=source_path,
            source_kind="codex_session",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="product/lessons/slack-first-authoring",
            candidate_title="Slack-First Authoring",
            recommended_scope=["product/lessons"],
        )
        save_result = repo.apply_save(source_bindings=[binding], decision=decision)
        knowledge_ref = save_result["touched_page_sections"][0].split("#", 1)[0]

        plan_path = root / "rebuild.json"
        plan_path.write_text(
            json.dumps(
                {
                    "scope": ["product/lessons"],
                    "page_updates": [
                        {
                            "knowledge_id": knowledge_ref,
                            "lifecycle_state": "historical",
                            "delete_page": False,
                        }
                    ],
                }
            )
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "rebuild",
                    "--json",
                    "--plan",
                    str(plan_path),
                    "--install-manifest-path",
                    str(repo.install_manifest_path),
                    "--repo-root",
                    str(root),
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["changes"][0]["knowledge_id"], knowledge_ref)


if __name__ == "__main__":
    unittest.main()

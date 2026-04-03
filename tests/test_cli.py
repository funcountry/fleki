from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph.frontmatter import dump_frontmatter, split_frontmatter
from knowledge_graph.cli import main


class CliContractTest(unittest.TestCase):
    def test_search_help_describes_candidate_discovery(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as exit_info:
                main(["search", "--help"])

        self.assertEqual(exit_info.exception.code, 0)
        rendered = stdout.getvalue()
        self.assertIn("Exact ref or literal query for candidate discovery.", rendered)

    def test_trace_help_describes_exact_refs(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as exit_info:
                main(["trace", "--help"])

        self.assertEqual(exit_info.exception.code, 0)
        rendered = stdout.getvalue()
        self.assertIn("Exact ref: knowledge_id", rendered)
        self.assertIn("current_path#section_alias", rendered)

    def test_save_help_mentions_temporal_contract_and_bundled_readme(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as exit_info:
                main(["save", "--help"])

        self.assertEqual(exit_info.exception.code, 0)
        rendered = stdout.getvalue()
        self.assertIn('Bindings must include "source_family"', rendered)
        self.assertIn('Bindings may include "timestamp"', rendered)
        self.assertIn("ingest_summary.authority_tier", rendered)
        self.assertIn("knowledge_units[].authority_posture", rendered)
        self.assertIn("knowledge_units[].kind", rendered)
        self.assertIn("knowledge_units[].temporal_scope", rendered)
        self.assertIn("topic_actions[].lifecycle_state", rendered)
        self.assertIn("bundled runtime README.md", rendered)

    def test_top_level_help_does_not_list_preview(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as exit_info:
                main(["--help"])

        self.assertEqual(exit_info.exception.code, 0)
        rendered = stdout.getvalue()
        self.assertIn("save", rendered)
        self.assertNotIn("preview", rendered)

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
        self.assertIn("missing_lifecycle_state_count", payload)
        self.assertNotIn("runtime_agreement_state", payload)
        self.assertNotIn("runtime_agreement", payload)

    def test_status_json_reports_missing_lifecycle_state_count(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "known.md"
        source_path.write_text("Leaderboard liquidity and reopen loop guidance.\n")

        from knowledge_graph import SourceBinding

        binding = SourceBinding(
            source_id="note.known",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="leaderboard/liquidity-and-reopen-loop",
            candidate_title="Liquidity And Reopen Loop",
            recommended_scope=["leaderboard"],
        )
        repo.apply_save(source_bindings=[binding], decision=decision)

        page_path = repo.data_root / "topics" / "leaderboard" / "liquidity-and-reopen-loop.md"
        metadata, body = split_frontmatter(page_path.read_text())
        metadata.pop("lifecycle_state", None)
        page_path.write_text(dump_frontmatter(metadata, body))

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
        self.assertEqual(payload["missing_lifecycle_state_count"], 1)

    def test_pdf_save_json_stdout_stays_parseable_in_subprocess(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        pdf_path = copy_fixture_pdf(root, "subprocess-fixture.pdf")
        bindings_path = root / "bindings.json"
        decision_path = root / "decision.json"

        bindings_payload = [
            {
                "source_id": "pdf.cli.subprocess",
                "local_path": str(pdf_path),
                "source_kind": "pdf_research",
                "source_family": "pdf",
                "authority_tier": "historical_support",
                "sensitivity": "internal",
                "preserve_mode": "copy",
            }
        ]
        decision_payload = sample_save_decision(
            source_ids=["pdf.cli.subprocess"],
            topic_path="product/cli/pdf-subprocess-runtime",
            candidate_title="CLI PDF Subprocess Runtime",
        )
        decision_payload["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"

        bindings_path.write_text(json.dumps(bindings_payload))
        decision_path.write_text(json.dumps(decision_payload))

        repo_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{repo_root / 'src'}:{repo_root / 'tests'}"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "knowledge_graph.cli",
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
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=repo_root,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "applied")

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
                "source_family": "pdf",
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

    def test_search_human_output_includes_match_kind_and_trace_ref_without_score(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "search.txt"
        source_path.write_text("AIM is auth-only.\n")

        from knowledge_graph import SourceBinding

        binding = SourceBinding(
            source_id="note.cli.search",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/cli-search-contract",
            candidate_title="CLI Search Contract",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"][0]["kind"] = "fact"
        decision["topic_actions"][0]["knowledge_units"][0]["statement"] = "AIM is auth-only."
        repo.apply_save(source_bindings=[binding], decision=decision)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "search",
                    "AIM is auth-only",
                    "--no-receipt",
                    "--install-manifest-path",
                    str(repo.install_manifest_path),
                    "--repo-root",
                    str(root),
                ]
            )

        self.assertEqual(exit_code, 0)
        rendered = stdout.getvalue()
        self.assertIn("match_kind=", rendered)
        self.assertIn("trace_ref=", rendered)
        self.assertNotIn("score=", rendered)

    def test_search_json_includes_match_kind_and_omits_score(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "search-json.txt"
        source_path.write_text("AIM is auth-only.\n")

        from knowledge_graph import SourceBinding

        binding = SourceBinding(
            source_id="note.cli.search.json",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/cli-search-json-contract",
            candidate_title="CLI Search JSON Contract",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"][0]["kind"] = "fact"
        decision["topic_actions"][0]["knowledge_units"][0]["statement"] = "AIM is auth-only."
        repo.apply_save(source_bindings=[binding], decision=decision)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "search",
                    "AIM is auth-only",
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
        self.assertIn("match_kind", payload["results"][0])
        self.assertNotIn("score", payload["results"][0])

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
            source_family="codex",
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

    def test_validation_error_is_reported_without_traceback(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "invalid.md"
        source_path.write_text("Invalid authority posture.\n")
        bindings_path = root / "bindings.json"
        decision_path = root / "decision.json"

        bindings_payload = [
            {
                "source_id": "note.invalid",
                "local_path": str(source_path),
                "source_kind": "markdown_doc",
                "source_family": "other",
            }
        ]
        decision_payload = sample_save_decision(
            source_ids=["note.invalid"],
            topic_path="knowledge-system/invalid-authority-posture",
            candidate_title="Invalid Authority Posture",
        )
        decision_payload["topic_actions"][0]["knowledge_units"][0]["authority_posture"] = (
            "historical_support"
        )

        bindings_path.write_text(json.dumps(bindings_payload))
        decision_path.write_text(json.dumps(decision_payload))

        stderr = io.StringIO()
        with redirect_stderr(stderr):
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

        rendered = stderr.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("error:", rendered)
        self.assertIn("knowledge_unit.authority_posture is invalid", rendered)
        self.assertNotIn("Traceback", rendered)

    def test_missing_source_family_is_reported_without_traceback(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "missing-family.md"
        source_path.write_text("Missing source family.\n")
        bindings_path = root / "bindings.json"
        decision_path = root / "decision.json"

        bindings_payload = [
            {
                "source_id": "note.missing.family",
                "local_path": str(source_path),
                "source_kind": "markdown_doc",
            }
        ]
        decision_payload = sample_save_decision(
            source_ids=["note.missing.family"],
            topic_path="knowledge-system/missing-source-family",
            candidate_title="Missing Source Family",
        )

        bindings_path.write_text(json.dumps(bindings_payload))
        decision_path.write_text(json.dumps(decision_payload))

        stderr = io.StringIO()
        with redirect_stderr(stderr):
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

        rendered = stderr.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("error:", rendered)
        self.assertIn("source binding missing required keys: source_family", rendered)
        self.assertNotIn("Traceback", rendered)

    def test_trace_not_found_is_reported_without_traceback(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(
                [
                    "trace",
                    "knowledge-system/does-not-exist",
                    "--json",
                    "--no-receipt",
                    "--install-manifest-path",
                    str(repo.install_manifest_path),
                    "--repo-root",
                    str(root),
                ]
            )

        rendered = stderr.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("error: unable to trace ref: knowledge-system/does-not-exist", rendered)
        self.assertNotIn("Traceback", rendered)


if __name__ == "__main__":
    unittest.main()

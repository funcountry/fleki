from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from common import make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding
from knowledge_graph.review_wiki.daemon import _resolve_public_path, _run_quartz_build, sync_review_wiki
from knowledge_graph.review_wiki.layout import resolve_review_wiki_layout


class ReviewWikiDaemonTest(unittest.TestCase):
    def test_resolve_public_path_handles_index_and_nested_routes(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        public_root = Path(temp_dir.name) / "public"
        (public_root / "index.html").parent.mkdir(parents=True, exist_ok=True)
        (public_root / "index.html").write_text("home\n")
        nested = public_root / "topics" / "example" / "index.html"
        nested.parent.mkdir(parents=True, exist_ok=True)
        nested.write_text("topic\n")
        asset = public_root / "index.css"
        asset.write_text("body{}\n")

        self.assertEqual(_resolve_public_path(public_root, "/"), (public_root / "index.html").resolve())
        self.assertEqual(_resolve_public_path(public_root, "/topics/example"), nested.resolve())
        self.assertEqual(_resolve_public_path(public_root, "/index.css"), asset.resolve())

    def test_resolve_public_path_rejects_path_traversal(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        public_root = Path(temp_dir.name) / "public"
        public_root.mkdir(parents=True, exist_ok=True)

        self.assertIsNone(_resolve_public_path(public_root, "/../secret.txt"))

    def test_quartz_build_uses_workspace_local_bootstrap(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        quartz_root = Path(temp_dir.name) / "quartz"
        quartz_root.mkdir(parents=True, exist_ok=True)
        build_log_path = Path(temp_dir.name) / "build.log"

        with mock.patch("knowledge_graph.review_wiki.daemon.subprocess.run") as run_mock:
            run_mock.return_value = mock.Mock(returncode=0, stdout="ok\n", stderr="")
            _run_quartz_build(quartz_root, quartz_root / ".public.next", build_log_path)

        run_mock.assert_called_once()
        command = run_mock.call_args.args[0]
        self.assertEqual(command[:2], ["node", "./quartz/bootstrap-cli.mjs"])
        self.assertEqual(command[2:], ["build", "-d", "content", "-o", ".public.next"])
        self.assertEqual(build_log_path.read_text(), "ok\n")

    def test_sync_rebuilds_once_and_skips_receipt_only_changes(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "daemon.md"
        source_path.write_text("Daemon review wiki source.\n")
        binding = SourceBinding(
            source_id="note.review.daemon",
            local_path=source_path,
            source_kind="markdown_doc",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="product/review/daemon",
            candidate_title="Daemon",
            recommended_scope=["product/review"],
        )
        repo.apply_save(source_bindings=[binding], decision=decision)

        review_layout = resolve_review_wiki_layout(repo.layout)
        review_layout.quartz_root.mkdir(parents=True, exist_ok=True)
        (review_layout.quartz_root / "package.json").write_text("{}\n")

        builds: list[Path] = []

        def fake_build(quartz_root: Path, output_root: Path, build_log_path: Path) -> None:
            builds.append(output_root)
            output_root.mkdir(parents=True, exist_ok=True)
            (output_root / "index.html").write_text("ok\n")
            build_log_path.parent.mkdir(parents=True, exist_ok=True)
            build_log_path.write_text("build ok\n")

        first = sync_review_wiki(repo, build_runner=fake_build)
        self.assertTrue(first.rebuilt)
        self.assertEqual(len(builds), 1)
        self.assertTrue((review_layout.public_root / "index.html").exists())

        repo.search("Daemon", write_receipt=True)
        second = sync_review_wiki(repo, build_runner=fake_build)
        self.assertFalse(second.rebuilt)
        self.assertEqual(len(builds), 1)


if __name__ == "__main__":
    unittest.main()

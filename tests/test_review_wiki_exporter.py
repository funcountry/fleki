from __future__ import annotations

import unittest

from common import make_temp_repo, sample_save_decision
from knowledge_graph import RebuildPlan, SourceBinding
from knowledge_graph.review_wiki.exporter import build_export_snapshot, materialize_export_snapshot


class ReviewWikiExporterTest(unittest.TestCase):
    def test_export_snapshot_includes_only_review_pages_and_rewrites_links(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "review-exporter.md"
        source_path.write_text("Review exporter evidence.\n")
        binding = SourceBinding(
            source_id="note.review.exporter",
            local_path=source_path,
            source_kind="markdown_doc",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="product/review/exporter-shape",
            candidate_title="Exporter Shape",
            recommended_scope=["product/review"],
        )

        repo.apply_save(source_bindings=[binding], decision=decision)
        repo.apply_rebuild(RebuildPlan(scope=("product/review",)))

        snapshot = build_export_snapshot(repo)
        paths = {item.relative_path for item in snapshot.files}

        self.assertIn("index.md", paths)
        self.assertIn("topics/index.md", paths)
        self.assertIn("indexes/index.md", paths)
        self.assertIn("provenance/index.md", paths)
        self.assertIn("topics/product/review/exporter-shape.md", paths)
        self.assertIn("indexes/by-topic.md", paths)
        self.assertTrue(any(path.startswith("provenance/") for path in paths))
        self.assertFalse(any(path.startswith("receipts/") for path in paths))
        self.assertFalse(any(path.startswith("sources/") for path in paths))

        topic_page = next(
            item.text
            for item in snapshot.files
            if item.relative_path == "topics/product/review/exporter-shape.md"
        )
        self.assertIn("[Provenance for note.review.exporter]", topic_page)

        provenance_page = next(
            item.text
            for item in snapshot.files
            if item.relative_path.startswith("provenance/")
            and item.relative_path.endswith(".md")
            and item.relative_path != "provenance/index.md"
        )
        self.assertIn("## Connected Topics", provenance_page)
        self.assertIn("[Exporter Shape]", provenance_page)

        by_topic_page = next(
            item.text for item in snapshot.files if item.relative_path == "indexes/by-topic.md"
        )
        self.assertIn("[Exporter Shape]", by_topic_page)

    def test_materialize_export_snapshot_replaces_stale_files(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "stale-export.md"
        source_path.write_text("Initial knowledge.\n")
        binding = SourceBinding(
            source_id="note.review.materialize",
            local_path=source_path,
            source_kind="markdown_doc",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="product/review/materialize",
            candidate_title="Materialize",
            recommended_scope=["product/review"],
        )
        repo.apply_save(source_bindings=[binding], decision=decision)

        snapshot = build_export_snapshot(repo)
        content_root = root / "state-root" / "review-wiki" / "quartz" / "content"
        materialize_export_snapshot(snapshot, content_root)
        stale_file = content_root / "stale.md"
        stale_file.write_text("obsolete\n")

        refreshed = build_export_snapshot(repo)
        materialize_export_snapshot(refreshed, content_root)

        self.assertFalse(stale_file.exists())
        self.assertTrue((content_root / "topics" / "product" / "review" / "materialize.md").exists())


if __name__ == "__main__":
    unittest.main()

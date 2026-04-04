from __future__ import annotations

import unittest

from common import make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding
from knowledge_graph.review_wiki.digest import (
    calculate_export_digest,
    load_saved_export_digest,
    write_saved_export_digest,
)
from knowledge_graph.review_wiki.exporter import build_export_snapshot


class ReviewWikiDigestTest(unittest.TestCase):
    def test_digest_is_stable_and_ignores_receipt_only_changes(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "digest.md"
        source_path.write_text("Digest test.\n")
        binding = SourceBinding(
            source_id="note.review.digest",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="product/review/digest",
            candidate_title="Digest",
            recommended_scope=["product/review"],
        )
        repo.apply_save(source_bindings=[binding], decision=decision)

        initial_snapshot = build_export_snapshot(repo)
        initial_digest = calculate_export_digest(initial_snapshot)

        repo.search("Digest", write_receipt=True)
        repo.status(write_receipt=True)

        refreshed_snapshot = build_export_snapshot(repo)
        refreshed_digest = calculate_export_digest(refreshed_snapshot)

        self.assertEqual(refreshed_digest, initial_digest)

    def test_saved_digest_round_trip(self) -> None:
        temp_dir, root, _repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        digest_path = root / "state-root" / "review-wiki" / "export-digest.json"
        self.assertIsNone(load_saved_export_digest(digest_path))

        write_saved_export_digest(digest_path, "abc123")

        self.assertEqual(load_saved_export_digest(digest_path), "abc123")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from common import make_temp_repo, sample_save_decision
from knowledge_graph import RebuildPageUpdate, RebuildPlan, SourceBinding


class RebuildTest(unittest.TestCase):
    def test_rebuild_rehomes_page_and_refreshes_indexes(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "slack-first.md"
        source_path.write_text("Slack-first authoring guidance.\n")
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

        rebuild = repo.apply_rebuild(
            RebuildPlan(
                scope=("product/lessons",),
                page_updates=(
                    RebuildPageUpdate(
                        knowledge_id=knowledge_ref,
                        new_current_path="product/lessons/slack-first-lesson-authoring",
                        note="Renamed for clarity.",
                    ),
                ),
                open_questions=("Need to watch for lesson-length contradictions.",),
            )
        )
        self.assertIn("product/lessons", rebuild["cleared_scopes"])

        new_page = root / "knowledge" / "topics" / "product" / "lessons" / "slack-first-lesson-authoring.md"
        old_page = root / "knowledge" / "topics" / "product" / "lessons" / "slack-first-authoring.md"
        self.assertTrue(new_page.exists())
        self.assertFalse(old_page.exists())

        search = repo.search("slack first authoring")
        self.assertEqual(
            search["results"][0]["current_path"],
            "product/lessons/slack-first-lesson-authoring",
        )

        by_topic = root / "knowledge" / "topics" / "indexes" / "by-topic.md"
        unresolved = root / "knowledge" / "topics" / "indexes" / "unresolved-questions.md"
        self.assertTrue(by_topic.exists())
        self.assertTrue(unresolved.exists())


if __name__ == "__main__":
    unittest.main()

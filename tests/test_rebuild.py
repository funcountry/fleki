from __future__ import annotations

import unittest

from common import make_temp_repo, sample_save_decision
from knowledge_graph.frontmatter import split_frontmatter
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

        new_page = repo.data_root / "topics" / "product" / "lessons" / "slack-first-lesson-authoring.md"
        old_page = repo.data_root / "topics" / "product" / "lessons" / "slack-first-authoring.md"
        self.assertTrue(new_page.exists())
        self.assertFalse(old_page.exists())

        search = repo.search("slack first authoring")
        self.assertEqual(
            search["results"][0]["current_path"],
            "product/lessons/slack-first-lesson-authoring",
        )

        by_topic = repo.data_root / "topics" / "indexes" / "by-topic.md"
        unresolved = repo.data_root / "topics" / "indexes" / "unresolved-questions.md"
        self.assertTrue(by_topic.exists())
        self.assertTrue(unresolved.exists())

    def test_rebuild_can_mark_page_stale_then_delete_it(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "stale-note.md"
        source_path.write_text("Old ephemeral note.\n")
        binding = SourceBinding(
            source_id="codex.session.stale-note",
            local_path=source_path,
            source_kind="codex_session",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="product/lessons/stale-note",
            candidate_title="Stale Note",
            recommended_scope=["product/lessons"],
        )
        save_result = repo.apply_save(source_bindings=[binding], decision=decision)
        knowledge_ref = save_result["touched_page_sections"][0].split("#", 1)[0]
        page_path = repo.data_root / "topics" / "product" / "lessons" / "stale-note.md"

        repo.apply_rebuild(
            RebuildPlan(
                scope=("product/lessons",),
                page_updates=(
                    RebuildPageUpdate(
                        knowledge_id=knowledge_ref,
                        lifecycle_state="stale",
                        note="This note is no longer current.",
                    ),
                ),
            )
        )

        metadata, _ = split_frontmatter(page_path.read_text())
        self.assertEqual(metadata["lifecycle_state"], "stale")
        search = repo.search("stale note")
        self.assertEqual(search["results"][0]["effective_lifecycle_state"], "stale")

        repo.apply_rebuild(
            RebuildPlan(
                scope=("product/lessons",),
                page_updates=(
                    RebuildPageUpdate(
                        knowledge_id=knowledge_ref,
                        delete_page=True,
                        note="Delete after explicit stale retirement.",
                    ),
                ),
            )
        )

        self.assertFalse(page_path.exists())
        self.assertEqual(repo.search("stale note")["results"], [])


if __name__ == "__main__":
    unittest.main()

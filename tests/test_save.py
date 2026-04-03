from __future__ import annotations

import unittest

from common import make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding


class SaveWorkflowTest(unittest.TestCase):
    def test_apply_save_persists_sources_provenance_topics_and_receipt(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        note_path = root / "lesson-note.md"
        note_path.write_text("# Note\n\nShared learnings matter.\n")
        session_path = root / "rollout.jsonl"
        session_path.write_text('{"event":"session"}\n')

        bindings = [
            SourceBinding(
                source_id="note.internal.lesson",
                local_path=note_path,
                source_kind="markdown_doc",
                authority_tier="live_doctrine",
            ),
            SourceBinding(
                source_id="codex.session.2026-04-02.demo",
                local_path=session_path,
                source_kind="codex_session",
                authority_tier="historical_support",
            ),
        ]
        decision = sample_save_decision(
            source_ids=[binding.source_id for binding in bindings],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )

        result = repo.apply_save(source_bindings=bindings, decision=decision)

        self.assertEqual(result["result"], "applied")
        self.assertEqual(len(result["saved_sources"]), 2)
        self.assertEqual(len(result["provenance_notes"]), 2)
        self.assertTrue(result["touched_page_sections"])
        self.assertIn("doctrine", result["rebuild_pending_scopes"])

        topic_path = root / "knowledge" / "topics" / "doctrine" / "shared-agent-learnings.md"
        self.assertTrue(topic_path.exists())
        topic_text = topic_path.read_text()
        self.assertIn("Shared Agent Learnings", topic_text)
        self.assertIn("Current Understanding", topic_text)

        receipt_path = root / result["receipt_path"]
        self.assertTrue(receipt_path.exists())
        self.assertIn("Save Receipt", receipt_path.read_text())


if __name__ == "__main__":
    unittest.main()

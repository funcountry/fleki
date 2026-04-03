from __future__ import annotations

import unittest

from common import make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding


class SearchTraceStatusTest(unittest.TestCase):
    def test_search_trace_and_status_are_authority_aware(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        doctrine_source = root / "doctrine.md"
        doctrine_source.write_text("This is live doctrine.\n")
        session_source = root / "session.jsonl"
        session_source.write_text('{"event":"session"}\n')

        doctrine_binding = SourceBinding(
            source_id="doctrine.current.shared",
            local_path=doctrine_source,
            source_kind="markdown_doc",
            authority_tier="live_doctrine",
        )
        session_binding = SourceBinding(
            source_id="codex.session.shared.draft",
            local_path=session_source,
            source_kind="codex_session",
            authority_tier="historical_support",
        )

        doctrine_decision = sample_save_decision(
            source_ids=[doctrine_binding.source_id],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
            authority_tier="live_doctrine",
            recommended_scope=["doctrine"],
        )
        doctrine_decision["topic_actions"][0]["knowledge_units"][0]["authority_posture"] = "live_doctrine"

        session_decision = sample_save_decision(
            source_ids=[session_binding.source_id],
            topic_path="doctrine/shared-agent-learnings-draft",
            candidate_title="Shared Agent Learnings Draft",
            authority_tier="historical_support",
            recommended_scope=["doctrine"],
        )

        repo.apply_save(source_bindings=[doctrine_binding], decision=doctrine_decision)
        repo.apply_save(source_bindings=[session_binding], decision=session_decision)

        search = repo.search("shared agent learnings")
        self.assertGreaterEqual(len(search["results"]), 2)
        self.assertEqual(
            search["results"][0]["current_path"],
            "doctrine/shared-agent-learnings",
        )
        self.assertEqual(search["results"][0]["authority_posture"], "live_doctrine")

        trace = repo.trace(search["results"][0]["trace_ref"])
        self.assertEqual(trace["current_path"], "doctrine/shared-agent-learnings")
        self.assertTrue(trace["provenance"])
        self.assertTrue(trace["source_records"])

        status = repo.status()
        self.assertIn("doctrine", status["rebuild_pending"])
        self.assertEqual(status["unresolved_contradictions"], 0)
        self.assertIn("doctrine/shared-agent-learnings", status["hot_topics"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding
from knowledge_graph.frontmatter import split_frontmatter


class SaveWorkflowTest(unittest.TestCase):
    def test_apply_save_persists_sources_provenance_topics_and_receipt(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        note_path = root / "lesson-note.md"
        note_path.write_text("# Note\n\nShared learnings matter.\n")
        pdf_path = copy_fixture_pdf(root, "lesson-note.pdf")

        bindings = [
            SourceBinding(
                source_id="note.internal.lesson",
                local_path=note_path,
                source_kind="markdown_doc",
                authority_tier="live_doctrine",
                timestamp="2026-03-31T10:00:00+00:00",
            ),
            SourceBinding(
                source_id="pdf.internal.lesson",
                local_path=pdf_path,
                source_kind="pdf_research",
                authority_tier="historical_support",
                timestamp="2026-04-01T09:00:00+00:00",
            ),
        ]
        decision = sample_save_decision(
            source_ids=[binding.source_id for binding in bindings],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )
        decision["source_reading_reports"][1]["reading_mode"] = "direct_local_pdf"

        result = repo.apply_save(source_bindings=bindings, decision=decision)

        self.assertEqual(result["result"], "applied")
        self.assertEqual(len(result["saved_sources"]), 2)
        self.assertEqual(len(result["provenance_notes"]), 2)
        self.assertTrue(result["touched_page_sections"])
        self.assertIn("doctrine", result["rebuild_pending_scopes"])
        self.assertEqual(len(result["saved_render_manifests"]), 1)
        self.assertEqual(len(result["saved_renders"]), 1)
        self.assertEqual(result["render_omitted_sources"], [])

        topic_path = repo.data_root / "topics" / "doctrine" / "shared-agent-learnings.md"
        self.assertTrue(topic_path.exists())
        topic_metadata, topic_text = split_frontmatter(topic_path.read_text())
        self.assertIn("Shared Agent Learnings", topic_text)
        self.assertIn("Current Understanding", topic_text)
        self.assertEqual(topic_metadata["lifecycle_state"], "current")
        self.assertEqual(topic_metadata["temporal_scope"], "evergreen")
        self.assertEqual(topic_metadata["last_supported_at"], "2026-04-01T09:00:00+00:00")
        section_temporal = topic_metadata["section_temporal"]
        self.assertEqual(len(section_temporal), 1)
        self.assertEqual(
            next(iter(section_temporal.values()))["last_supported_at"],
            "2026-04-01T09:00:00+00:00",
        )

        receipt_path = repo.data_root / result["receipt_path"]
        self.assertTrue(receipt_path.exists())
        receipt_metadata, receipt_body = split_frontmatter(receipt_path.read_text())
        self.assertIn("Save Receipt", receipt_body)
        self.assertEqual(receipt_metadata["saved_render_manifests"], result["saved_render_manifests"])
        self.assertEqual(receipt_metadata["saved_renders"], result["saved_renders"])

        render_manifest_path = repo.data_root / result["saved_render_manifests"][0]
        render_manifest = json.loads(render_manifest_path.read_text())
        self.assertEqual(render_manifest["engine_id"], "docling")
        self.assertEqual(render_manifest["source_id"], "pdf.internal.lesson")

        source_manifest_path = repo.data_root / "sources" / "pdf" / "pdf.internal.lesson__lesson-note.pdf.record.json"
        source_manifest = json.loads(source_manifest_path.read_text())
        self.assertTrue(source_manifest["render_eligibility"])
        self.assertEqual(source_manifest["source_observed_at"], "2026-04-01T09:00:00+00:00")
        self.assertEqual(
            source_manifest["render_manifest_relative_path"],
            result["saved_render_manifests"][0],
        )

        provenance_metadata = []
        for relative_path in result["provenance_notes"]:
            metadata, _ = split_frontmatter((repo.data_root / relative_path).read_text())
            provenance_metadata.append(metadata)
        pdf_provenance = next(
            metadata
            for metadata in provenance_metadata
            if metadata["source_ids"] == ["pdf.internal.lesson"]
        )
        self.assertEqual(
            pdf_provenance["source_observed_at_by_source"]["pdf.internal.lesson"],
            "2026-04-01T09:00:00+00:00",
        )
        self.assertEqual(
            pdf_provenance["latest_source_observed_at"],
            "2026-04-01T09:00:00+00:00",
        )
        self.assertEqual(
            pdf_provenance["render_manifest_paths"]["pdf.internal.lesson"],
            result["saved_render_manifests"][0],
        )
        self.assertEqual(
            pdf_provenance["render_fidelity_by_source"]["pdf.internal.lesson"],
            "high_fidelity",
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding
from knowledge_graph.ids import safe_filename
from knowledge_graph.review_wiki import export_review_wiki


class ReviewWikiExporterTest(unittest.TestCase):
    def test_export_review_wiki_appends_artifacts_and_exports_only_linked_files(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        note_path = root / "artifact-note.md"
        note_path.write_text("Semantic evidence for the review wiki.\n")
        copied_pdf_path = copy_fixture_pdf(root, "copied-evidence.pdf")
        secret_pdf_path = copy_fixture_pdf(root, "secret-evidence.pdf")

        bindings = [
            SourceBinding(
                source_id="note.review.article",
                local_path=note_path,
                source_kind="markdown_doc",
                source_family="other",
                timestamp="2026-04-03T12:00:00+00:00",
            ),
            SourceBinding(
                source_id="note.review.pdf.copy",
                local_path=copied_pdf_path,
                source_kind="pdf_document",
                source_family="pdf",
                timestamp="2026-04-03T12:30:00+00:00",
            ),
            SourceBinding(
                source_id="note.review.pdf.secret",
                local_path=secret_pdf_path,
                source_kind="pdf_document",
                source_family="pdf",
                sensitivity="secret_pointer_only",
                timestamp="2026-04-03T13:00:00+00:00",
            ),
        ]
        decision = sample_save_decision(
            source_ids=[binding.source_id for binding in bindings],
            topic_path="knowledge-system/review-wiki-artifacts",
            candidate_title="Review Wiki Artifacts",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"][0]["statement"] = (
            "The review wiki should show artifacts directly under the knowledge."
        )

        repo.apply_save(source_bindings=bindings, decision=decision)
        exported = export_review_wiki(repo)

        content_root = Path(exported["content_root"])
        topic_page = content_root / "topics" / "knowledge-system" / "review-wiki-artifacts.md"
        self.assertTrue(topic_page.exists(), msg=str(topic_page))
        topic_text = topic_page.read_text()
        self.assertTrue(topic_text.startswith("---\n"))
        self.assertIn('knowledge_id: "', topic_text)
        self.assertIn("## Artifacts", topic_text)
        self.assertIn("## Provenance Notes", topic_text)
        self.assertLess(topic_text.index("## Artifacts"), topic_text.index("## Provenance Notes"))

        note_artifact_page = f"artifacts/{safe_filename('note.review.article')}.md"
        copied_pdf_artifact_page = f"artifacts/{safe_filename('note.review.pdf.copy')}.md"
        secret_pdf_artifact_page = f"artifacts/{safe_filename('note.review.pdf.secret')}.md"
        self.assertEqual(
            exported["artifact_pages_by_source"]["note.review.article"],
            note_artifact_page,
        )
        self.assertIn(f"[note.review.article](../../{note_artifact_page})", topic_text)
        self.assertIn(f"[note.review.pdf.copy](../../{copied_pdf_artifact_page})", topic_text)
        self.assertIn(f"[note.review.pdf.secret](../../{secret_pdf_artifact_page})", topic_text)

        provenance_pages = [content_root / relative_path for relative_path in exported["provenance_pages"]]
        self.assertEqual(len(provenance_pages), 3)
        self.assertTrue(
            any(
                "## Artifacts" in provenance_page.read_text()
                and "[note.review.article]" in provenance_page.read_text()
                for provenance_page in provenance_pages
            )
        )

        note_artifact_text = (content_root / note_artifact_page).read_text()
        self.assertIn("## Primary Artifact", note_artifact_text)
        self.assertIn(
            "[Open preserved artifact](../files/sources/other/note.review.article__artifact-note.md)",
            note_artifact_text,
        )
        self.assertNotIn("## PDF Render", note_artifact_text)

        copied_pdf_artifact_text = (content_root / copied_pdf_artifact_page).read_text()
        self.assertIn("## PDF Render", copied_pdf_artifact_text)
        self.assertIn("[Render markdown](", copied_pdf_artifact_text)
        self.assertIn("[Render manifest](", copied_pdf_artifact_text)

        secret_pdf_artifact_text = (content_root / secret_pdf_artifact_page).read_text()
        self.assertIn("## Primary Artifact", secret_pdf_artifact_text)
        self.assertIn(
            "[Open preserved artifact](../files/sources/pdf/note.review.pdf.secret__secret-evidence.pdf.pointer.json)",
            secret_pdf_artifact_text,
        )
        self.assertIn("Raw copied content is not stored for `secret_pointer_only`.", secret_pdf_artifact_text)
        self.assertIn("Render omitted: `disallowed_by_sensitivity`", secret_pdf_artifact_text)
        self.assertNotIn("[Render markdown](", secret_pdf_artifact_text)

        expected_exported_files = {
            "files/sources/other/note.review.article__artifact-note.md",
            "files/sources/pdf/note.review.pdf.copy__copied-evidence.pdf",
            "files/sources/pdf/note.review.pdf.secret__secret-evidence.pdf.pointer.json",
        }
        self.assertTrue(expected_exported_files.issubset(set(exported["exported_files"])))
        self.assertFalse(list(content_root.rglob("*.record.json")))


if __name__ == "__main__":
    unittest.main()

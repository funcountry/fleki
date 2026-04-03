from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from shutil import copy2

from common import create_structured_pdf, make_temp_repo, repo_fixture_pdf_path
from knowledge_graph.pdf_render import render_pdf_bundle


class PdfRenderingTest(unittest.TestCase):
    def test_render_pdf_bundle_writes_markdown_and_manifest(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        raw_dir = repo.data_root / "sources" / "pdf"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_pdf_path = raw_dir / "fixture.pdf"
        copy2(repo_fixture_pdf_path(), raw_pdf_path)

        bundle = render_pdf_bundle(
            root=repo.data_root,
            raw_pdf_path=raw_pdf_path,
            source_id="pdf.fixture",
            source_sha256=repo._sha256(raw_pdf_path),
            timestamp="2026-04-03T00:00:00+00:00",
        )

        self.assertTrue(bundle.render_eligible)
        self.assertEqual(bundle.engine_id, "docling")
        self.assertEqual(bundle.fidelity_mode, "high_fidelity")
        self.assertIsNotNone(bundle.render_relative_path)
        self.assertIsNotNone(bundle.render_manifest_relative_path)

        render_markdown_path = repo.data_root / bundle.render_relative_path
        render_manifest_path = repo.data_root / bundle.render_manifest_relative_path
        self.assertTrue(render_markdown_path.exists())
        self.assertTrue(render_manifest_path.exists())

        render_markdown = render_markdown_path.read_text()
        self.assertIn("Semantic knowledge graph smoke PDF", render_markdown)
        self.assertTrue(bundle.anchor_hints)

        render_manifest = json.loads(render_manifest_path.read_text())
        self.assertEqual(render_manifest["render_relative_path"], bundle.render_relative_path)
        self.assertEqual(render_manifest["fidelity_mode"], "high_fidelity")
        self.assertEqual(render_manifest["asset_relative_paths"], [])

    def test_render_pdf_bundle_restores_lists_and_literal_placeholders(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        raw_dir = repo.data_root / "sources" / "pdf"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_pdf_path = create_structured_pdf(raw_dir)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            bundle = render_pdf_bundle(
                root=repo.data_root,
                raw_pdf_path=raw_pdf_path,
                source_id="pdf.structured",
                source_sha256=repo._sha256(raw_pdf_path),
                timestamp="2026-04-03T00:00:00+00:00",
            )

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

        render_markdown_path = repo.data_root / bundle.render_relative_path
        render_markdown = render_markdown_path.read_text()
        self.assertIn("## Heading: Tone Guide", render_markdown)
        self.assertIn("1. Acknowledge the issue\n2. Offer the next step", render_markdown)
        self.assertIn("- Keep the tone calm\n- Mention <X> and <specific issue>", render_markdown)
        self.assertIn("Section: Examples", render_markdown)
        self.assertIn("Use concise bullets.", render_markdown)


if __name__ == "__main__":
    unittest.main()

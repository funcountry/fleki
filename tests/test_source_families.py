from __future__ import annotations

import json
import unittest

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding


class SourceFamiliesTest(unittest.TestCase):
    def test_pdf_image_and_runtime_origin_sources_are_preserved(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        pdf_path = copy_fixture_pdf(root, "lesson-onboarding.pdf")
        image_path = root / "diagram.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\nmock")
        hermes_path = root / "hermes-event.json"
        hermes_path.write_text('{"runtime":"hermes"}\n')

        bindings = [
            SourceBinding(
                source_id="research.pdf.lesson-onboarding",
                local_path=pdf_path,
                source_kind="pdf_research",
                timestamp="2026-04-01T09:00:00+00:00",
            ),
            SourceBinding(
                source_id="image.lesson.diagram",
                local_path=image_path,
                source_kind="image_asset",
                timestamp="2026-04-02T08:00:00+00:00",
            ),
            SourceBinding(
                source_id="hermes.runtime.event",
                local_path=hermes_path,
                source_kind="hermes_runtime_artifact",
                authority_tier="raw_runtime",
                timestamp="2026-04-03T07:00:00+00:00",
            ),
        ]
        decision = sample_save_decision(
            source_ids=[binding.source_id for binding in bindings],
            topic_path="product/learning-experience/placement-and-onboarding",
            candidate_title="Placement And Onboarding",
            authority_tier="mixed",
            recommended_scope=["product/learning-experience"],
        )
        decision["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"
        decision["source_reading_reports"][1]["reading_mode"] = "direct_local_image"
        decision["source_reading_reports"][2]["reading_mode"] = "direct_local_text"

        result = repo.apply_save(source_bindings=bindings, decision=decision)

        saved_sources = result["saved_sources"]
        self.assertTrue(any("/pdf/" in path for path in saved_sources))
        self.assertTrue(any("/images/" in path for path in saved_sources))
        self.assertTrue(any("/hermes/" in path for path in saved_sources))
        self.assertEqual(len(result["saved_render_manifests"]), 1)

        render_manifest_path = repo.data_root / result["saved_render_manifests"][0]
        self.assertTrue(render_manifest_path.exists())
        render_manifest = json.loads(render_manifest_path.read_text())
        self.assertEqual(render_manifest["engine_id"], "docling")
        self.assertEqual(render_manifest["fidelity_mode"], "high_fidelity")

        render_markdown_path = repo.data_root / result["saved_renders"][0]
        self.assertTrue(render_markdown_path.exists())
        self.assertIn("Semantic knowledge graph smoke PDF", render_markdown_path.read_text())
        self.assertFalse(any(repo.assets_root.iterdir()))

        pdf_manifest = json.loads(
            (
                repo.data_root
                / "sources"
                / "pdf"
                / "research.pdf.lesson-onboarding__lesson-onboarding.pdf.record.json"
            ).read_text()
        )
        self.assertEqual(pdf_manifest["source_observed_at"], "2026-04-01T09:00:00+00:00")

    def test_secret_pointer_only_sources_are_not_copied_raw(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        secret_path = copy_fixture_pdf(root, "secret-config.pdf")

        binding = SourceBinding(
            source_id="runtime.secret.pointer",
            local_path=secret_path,
            source_kind="pdf_secret",
            sensitivity="secret_pointer_only",
            preserve_mode="pointer",
            timestamp="2026-04-03T06:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="doctrine/authority-and-precedence",
            candidate_title="Authority And Precedence",
            authority_tier="historical_support",
            recommended_scope=["doctrine"],
        )
        result = repo.apply_save(source_bindings=[binding], decision=decision)

        saved_source = result["saved_sources"][0]
        self.assertTrue(saved_source.endswith(".pointer.json"))
        self.assertEqual(result["saved_render_manifests"], [])
        self.assertEqual(
            result["render_omitted_sources"],
            [
                {
                    "source_id": binding.source_id,
                    "omission_reason": "disallowed_by_sensitivity",
                }
            ],
        )

        source_manifest_path = repo.data_root / "sources" / "pdf" / "runtime.secret.pointer__secret-config.pdf.record.json"
        manifest = json.loads(source_manifest_path.read_text())
        self.assertFalse(manifest["render_eligibility"])
        self.assertEqual(manifest["render_omission_reason"], "disallowed_by_sensitivity")
        self.assertEqual(manifest["source_observed_at"], "2026-04-03T06:00:00+00:00")


if __name__ == "__main__":
    unittest.main()

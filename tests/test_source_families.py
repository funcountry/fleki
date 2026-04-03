from __future__ import annotations

import unittest

from common import make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding


class SourceFamiliesTest(unittest.TestCase):
    def test_pdf_image_and_runtime_origin_sources_are_preserved(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        pdf_path = root / "lesson-onboarding.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 mock pdf")
        image_path = root / "diagram.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\nmock")
        hermes_path = root / "hermes-event.json"
        hermes_path.write_text('{"runtime":"hermes"}\n')

        bindings = [
            SourceBinding(
                source_id="research.pdf.lesson-onboarding",
                local_path=pdf_path,
                source_kind="pdf_research",
            ),
            SourceBinding(
                source_id="image.lesson.diagram",
                local_path=image_path,
                source_kind="image_asset",
            ),
            SourceBinding(
                source_id="hermes.runtime.event",
                local_path=hermes_path,
                source_kind="hermes_runtime_artifact",
                authority_tier="raw_runtime",
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

    def test_secret_pointer_only_sources_are_not_copied_raw(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        secret_path = root / "secret-config.txt"
        secret_path.write_text("top-secret\n")

        binding = SourceBinding(
            source_id="runtime.secret.pointer",
            local_path=secret_path,
            source_kind="runtime_secret",
            sensitivity="secret_pointer_only",
            preserve_mode="pointer",
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


if __name__ == "__main__":
    unittest.main()

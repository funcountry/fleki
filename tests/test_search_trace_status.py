from __future__ import annotations

import json
import shutil
import unittest

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph import (
    RebuildPageUpdate,
    RebuildPlan,
    SourceBinding,
)


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
            timestamp="2026-03-01T10:00:00+00:00",
        )
        session_binding = SourceBinding(
            source_id="codex.session.shared.draft",
            local_path=session_source,
            source_kind="codex_session",
            authority_tier="historical_support",
            timestamp="2026-04-03T10:00:00+00:00",
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
        session_decision["topic_actions"][0]["lifecycle_state"] = "historical"

        repo.apply_save(source_bindings=[doctrine_binding], decision=doctrine_decision)
        repo.apply_save(source_bindings=[session_binding], decision=session_decision)

        search = repo.search("shared agent learnings")
        self.assertGreaterEqual(len(search["results"]), 2)
        self.assertEqual(
            search["results"][0]["current_path"],
            "doctrine/shared-agent-learnings",
        )
        self.assertEqual(search["results"][0]["authority_posture"], "live_doctrine")
        self.assertEqual(search["results"][0]["lifecycle_state"], "current")
        self.assertEqual(search["results"][0]["effective_lifecycle_state"], "current")
        self.assertEqual(search["results"][0]["last_supported_at"], "2026-03-01T10:00:00+00:00")

        trace = repo.trace(search["results"][0]["trace_ref"])
        self.assertEqual(trace["current_path"], "doctrine/shared-agent-learnings")
        self.assertEqual(trace["lifecycle_state"], "current")
        self.assertEqual(trace["effective_lifecycle_state"], "current")
        self.assertEqual(
            trace["source_observed_at_by_source"]["doctrine.current.shared"],
            "2026-03-01T10:00:00+00:00",
        )
        self.assertTrue(trace["provenance"])
        self.assertTrue(trace["source_records"])

        status = repo.status()
        self.assertIn("doctrine", status["rebuild_pending"])
        self.assertEqual(status["unresolved_contradictions"], 0)
        self.assertIn("doctrine/shared-agent-learnings", status["hot_topics"])
        self.assertIn("doctrine/shared-agent-learnings-draft", status["recent_topics"])
        self.assertTrue(
            any(path.endswith("codex.session.shared.draft__session.jsonl.record.json") for path in status["recent_source_ingests"])
        )
        self.assertEqual(status["historical_topic_count"], 1)
        self.assertEqual(status["stale_topic_count"], 0)
        self.assertEqual(status["superseded_topic_count"], 0)
        self.assertEqual(status["resolved_data_root"], str(repo.data_root))
        self.assertEqual(status["install_manifest_path"], str(repo.install_manifest_path))
        self.assertTrue(status["install_manifest_present"])
        self.assertFalse(status["legacy_repo_graph_detected"])
        self.assertNotIn("runtime_agreement", status)
        self.assertNotIn("runtime_agreement_state", status)

    def test_search_prefers_topical_match_over_path_noise(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        actual_source = root / "customer-io.md"
        actual_source.write_text("Customer.io current setup guidance.\n")
        noise_source = root / "noise.md"
        noise_source.write_text("Knowledge system internals.\n")

        actual_binding = SourceBinding(
            source_id="note.customerio.actual",
            local_path=actual_source,
            source_kind="markdown_doc",
            timestamp="2026-04-03T11:00:00+00:00",
        )
        noise_binding = SourceBinding(
            source_id="note.customerio.noise",
            local_path=noise_source,
            source_kind="markdown_doc",
            timestamp="2026-04-03T09:00:00+00:00",
        )

        actual_decision = sample_save_decision(
            source_ids=[actual_binding.source_id],
            topic_path="product/customer-io/current-setup",
            candidate_title="Customer.io Current Setup",
            recommended_scope=["product/customer-io"],
        )
        noise_decision = sample_save_decision(
            source_ids=[noise_binding.source_id],
            topic_path="knowledge-system/customer-io-index",
            candidate_title="Knowledge System Index",
            recommended_scope=["knowledge-system"],
        )
        noise_decision["topic_actions"][0]["knowledge_units"][0]["statement"] = (
            "This page tracks knowledge graph routing."
        )

        repo.apply_save(source_bindings=[actual_binding], decision=actual_decision)
        repo.apply_save(source_bindings=[noise_binding], decision=noise_decision)

        search = repo.search("Customer.io")
        self.assertEqual(
            search["results"][0]["current_path"],
            "product/customer-io/current-setup",
        )

    def test_trace_and_status_surface_pdf_render_and_omission_state(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        copied_pdf_path = copy_fixture_pdf(root, "copied.pdf")
        secret_pdf_path = copy_fixture_pdf(root, "secret.pdf")

        copied_binding = SourceBinding(
            source_id="pdf.copied.lesson",
            local_path=copied_pdf_path,
            source_kind="pdf_research",
        )
        secret_binding = SourceBinding(
            source_id="pdf.secret.lesson",
            local_path=secret_pdf_path,
            source_kind="pdf_secret",
            sensitivity="secret_pointer_only",
            preserve_mode="pointer",
        )

        copied_decision = sample_save_decision(
            source_ids=[copied_binding.source_id],
            topic_path="product/learning-experience/copied-pdf",
            candidate_title="Copied PDF",
            recommended_scope=["product/learning-experience"],
        )
        copied_decision["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"

        secret_decision = sample_save_decision(
            source_ids=[secret_binding.source_id],
            topic_path="product/learning-experience/secret-pdf",
            candidate_title="Secret PDF",
            recommended_scope=["product/learning-experience"],
        )
        secret_decision["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"
        secret_decision["ingest_summary"]["sensitivity"] = "secret_pointer_only"
        secret_decision["provenance_notes"][0]["sensitivity_notes"] = "secret_pointer_only"

        repo.apply_save(source_bindings=[copied_binding], decision=copied_decision)
        repo.apply_save(source_bindings=[secret_binding], decision=secret_decision)

        copied_trace = repo.trace("product/learning-experience/copied-pdf")
        self.assertEqual(len(copied_trace["render_manifests"]), 1)
        self.assertEqual(len(copied_trace["render_artifacts"]), 1)
        self.assertEqual(copied_trace["render_omissions"], [])

        secret_trace = repo.trace("product/learning-experience/secret-pdf")
        self.assertEqual(secret_trace["render_manifests"], [])
        self.assertEqual(secret_trace["render_artifacts"], [])
        self.assertEqual(
            secret_trace["render_omissions"],
            [
                {
                    "source_id": "pdf.secret.lesson",
                    "source_record": "sources/pdf/pdf.secret.lesson__secret.pdf.record.json",
                    "omission_reason": "disallowed_by_sensitivity",
                }
            ],
        )

        status = repo.status()
        self.assertEqual(status["pdf_rendered_sources"], 1)
        self.assertEqual(status["pdf_limited_fidelity_sources"], 0)
        self.assertEqual(status["pdf_render_omitted_sources"], 1)
        self.assertTrue(status["recent_topics"])
        self.assertTrue(status["recent_source_ingests"])

    def test_superseded_pages_stay_traceable_and_rank_lower(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        legacy_source = root / "legacy.md"
        legacy_source.write_text("Legacy setup.\n")
        current_source = root / "current.md"
        current_source.write_text("Current setup.\n")

        legacy_binding = SourceBinding(
            source_id="note.customerio.legacy",
            local_path=legacy_source,
            source_kind="markdown_doc",
            timestamp="2026-03-01T10:00:00+00:00",
        )
        current_binding = SourceBinding(
            source_id="note.customerio.current",
            local_path=current_source,
            source_kind="markdown_doc",
            timestamp="2026-04-03T10:00:00+00:00",
        )

        legacy_decision = sample_save_decision(
            source_ids=[legacy_binding.source_id],
            topic_path="product/customer-io/legacy-setup",
            candidate_title="Customer.io Legacy Setup",
            recommended_scope=["product/customer-io"],
        )
        current_decision = sample_save_decision(
            source_ids=[current_binding.source_id],
            topic_path="product/customer-io/current-setup",
            candidate_title="Customer.io Current Setup",
            recommended_scope=["product/customer-io"],
        )

        legacy_result = repo.apply_save(source_bindings=[legacy_binding], decision=legacy_decision)
        current_result = repo.apply_save(source_bindings=[current_binding], decision=current_decision)
        current_knowledge_id = current_result["touched_page_sections"][0].split("#", 1)[0]

        repo.apply_rebuild(
            RebuildPlan(
                scope=("product/customer-io",),
                page_updates=(
                    RebuildPageUpdate(
                        knowledge_id=current_knowledge_id,
                        add_supersedes=("product/customer-io/legacy-setup",),
                        note="Current setup replaces the legacy page.",
                    ),
                ),
            )
        )

        search = repo.search("Customer.io setup")
        self.assertEqual(search["results"][0]["current_path"], "product/customer-io/current-setup")
        legacy_result = next(
            item for item in search["results"] if item["current_path"] == "product/customer-io/legacy-setup"
        )
        self.assertEqual(legacy_result["effective_lifecycle_state"], "superseded")

        trace = repo.trace("product/customer-io/legacy-setup")
        self.assertEqual(trace["effective_lifecycle_state"], "superseded")
        self.assertEqual(trace["replacement_paths"], ["product/customer-io/current-setup"])

    def test_trace_and_status_surface_legacy_pdf_render_contract_gap(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        pdf_path = copy_fixture_pdf(root, "legacy-gap.pdf")
        binding = SourceBinding(
            source_id="pdf.legacy.gap",
            local_path=pdf_path,
            source_kind="pdf_research",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/multimodal-runtime-validation",
            candidate_title="Multimodal Runtime Validation",
            recommended_scope=["knowledge-system"],
        )
        decision["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"

        repo.apply_save(source_bindings=[binding], decision=decision)

        manifest_path = next((repo.data_root / "sources" / "pdf").glob("*.record.json"))
        manifest = json.loads(manifest_path.read_text())
        manifest.pop("source_family", None)
        render_manifest_path = manifest.pop("render_manifest_relative_path")
        render_markdown_path = manifest.pop("render_relative_path")
        manifest.pop("render_eligibility", None)
        manifest.pop("render_omission_reason", None)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        (repo.data_root / render_manifest_path).unlink()
        (repo.data_root / render_markdown_path).unlink()
        assets_dir = (repo.data_root / render_markdown_path).with_suffix(".assets")
        if assets_dir.exists():
            shutil.rmtree(assets_dir)

        trace = repo.trace("knowledge-system/multimodal-runtime-validation")
        self.assertEqual(trace["render_manifests"], [])
        self.assertEqual(trace["render_artifacts"], [])
        self.assertEqual(trace["render_omissions"], [])
        self.assertEqual(
            trace["render_contract_gaps"],
            [
                {
                    "source_id": "pdf.legacy.gap",
                    "source_record": manifest_path.relative_to(repo.data_root).as_posix(),
                    "gap_reason": "legacy_missing_render_contract",
                }
            ],
        )

        status = repo.status()
        self.assertEqual(status["pdf_rendered_sources"], 0)
        self.assertEqual(status["pdf_render_omitted_sources"], 0)
        self.assertEqual(status["pdf_render_contract_gap_count"], 1)


if __name__ == "__main__":
    unittest.main()

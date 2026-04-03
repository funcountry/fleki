from __future__ import annotations

import json
import shutil
import unittest

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph.frontmatter import dump_frontmatter, split_frontmatter
from knowledge_graph import (
    RebuildPageUpdate,
    RebuildPlan,
    SourceBinding,
    ValidationError,
)


class SearchTraceStatusTest(unittest.TestCase):
    def test_trace_resolves_normalized_section_aliases_and_rejects_unknown_fragment(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "alias-trace.md"
        source_path.write_text("Current understanding for exact trace behavior.\n")
        binding = SourceBinding(
            source_id="note.alias.trace",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/multimodal-runtime-validation",
            candidate_title="Multimodal Runtime Validation",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"][0]["kind"] = "fact"
        decision["topic_actions"][0]["knowledge_units"][0]["statement"] = (
            "Exact trace should resolve section aliases from stored metadata."
        )
        decision["topic_actions"][0]["knowledge_units"][0]["evidence"] = [
            {
                "source_id": binding.source_id,
                "locator": "line 1",
                "notes": "",
            }
        ]

        repo.apply_save(source_bindings=[binding], decision=decision)

        trace = repo.trace("knowledge-system/multimodal-runtime-validation#current_understanding")
        hyphen_trace = repo.trace("knowledge-system/multimodal-runtime-validation#current-understanding")
        heading_trace = repo.trace("knowledge-system/multimodal-runtime-validation#Current Understanding")
        self.assertIsNotNone(trace["section_id"])
        self.assertEqual(trace["section_id"], hyphen_trace["section_id"])
        self.assertEqual(trace["section_id"], heading_trace["section_id"])
        self.assertEqual(trace["matched_heading"], "Current Understanding")
        self.assertEqual(
            trace["matched_snippet"],
            "- Exact trace should resolve section aliases from stored metadata.",
        )
        self.assertEqual(trace["matched_evidence_locators"], ["line 1"])
        self.assertEqual(len(trace["provenance"]), 1)
        self.assertEqual(
            trace["supported_sections"],
            [
                {
                    "section_id": trace["section_id"],
                    "heading": "Current Understanding",
                    "trace_ref": f"{trace['knowledge_id']}#{trace['section_id']}",
                    "snippet": "- Exact trace should resolve section aliases from stored metadata.",
                    "matched_evidence_locators": ["line 1"],
                    "provenance": trace["provenance"],
                }
            ],
        )
        with self.assertRaises(ValidationError):
            repo.trace("knowledge-system/multimodal-runtime-validation#does_not_exist")

    def test_page_trace_returns_supported_sections_without_guessing(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "page-trace.md"
        source_path.write_text("Two sections should remain explicit.\n")
        binding = SourceBinding(
            source_id="note.page.trace",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/page-trace-contract",
            candidate_title="Page Trace Contract",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"] = [
            {
                "kind": "fact",
                "temporal_scope": "evergreen",
                "target_section": {
                    "section_id": None,
                    "heading": "Current Understanding",
                },
                "statement": "The page trace should list supported sections.",
                "rationale": "Operators need a deterministic section summary.",
                "authority_posture": "supported_by_internal_session",
                "confidence": "high",
                "evidence": [
                    {
                        "source_id": binding.source_id,
                        "locator": "line 1",
                        "notes": "",
                    }
                ],
            },
            {
                "kind": "fact",
                "temporal_scope": "evergreen",
                "target_section": {
                    "section_id": None,
                    "heading": "Operational Notes",
                },
                "statement": "The page trace should not guess a best section.",
                "rationale": "Section summaries are better than fake ranking.",
                "authority_posture": "supported_by_internal_session",
                "confidence": "high",
                "evidence": [
                    {
                        "source_id": binding.source_id,
                        "locator": "line 1",
                        "notes": "",
                    }
                ],
            },
        ]

        repo.apply_save(source_bindings=[binding], decision=decision)

        trace = repo.trace("knowledge-system/page-trace-contract")
        self.assertIsNone(trace["section_id"])
        self.assertIsNone(trace["matched_heading"])
        self.assertIsNone(trace["matched_snippet"])
        self.assertEqual(len(trace["supported_sections"]), 2)
        self.assertEqual(
            [item["heading"] for item in trace["supported_sections"]],
            ["Current Understanding", "Operational Notes"],
        )
        self.assertTrue(
            all(item["trace_ref"].startswith(f"{trace['knowledge_id']}#") for item in trace["supported_sections"])
        )

    def test_trace_dedupes_provenance_paths(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "dedupe-trace.md"
        source_path.write_text("Repeated evidence should not duplicate provenance.\n")
        binding = SourceBinding(
            source_id="note.trace.dedupe",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/trace-dedupe-contract",
            candidate_title="Trace Dedupe Contract",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"] = [
            {
                "kind": "fact",
                "temporal_scope": "evergreen",
                "target_section": {
                    "section_id": None,
                    "heading": "Current Understanding",
                },
                "statement": "Trace should dedupe provenance paths.",
                "rationale": "Multiple locators can still point to one provenance note.",
                "authority_posture": "supported_by_internal_session",
                "confidence": "high",
                "evidence": [
                    {
                        "source_id": binding.source_id,
                        "locator": "line 1",
                        "notes": "",
                    },
                    {
                        "source_id": binding.source_id,
                        "locator": "line 1 (repeat)",
                        "notes": "",
                    },
                ],
            }
        ]

        repo.apply_save(source_bindings=[binding], decision=decision)

        trace = repo.trace("knowledge-system/trace-dedupe-contract#current_understanding")
        self.assertEqual(len(trace["provenance"]), 1)
        self.assertEqual(len(trace["supported_sections"][0]["provenance"]), 1)
        self.assertEqual(
            trace["supported_sections"][0]["matched_evidence_locators"],
            ["line 1", "line 1 (repeat)"],
        )

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
            source_family="other",
            authority_tier="live_doctrine",
            timestamp="2026-03-01T10:00:00+00:00",
        )
        session_binding = SourceBinding(
            source_id="codex.session.shared.draft",
            local_path=session_source,
            source_kind="codex_session",
            source_family="codex",
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
        self.assertEqual(status["missing_lifecycle_state_count"], 0)
        self.assertEqual(status["resolved_data_root"], str(repo.data_root))
        self.assertEqual(status["install_manifest_path"], str(repo.install_manifest_path))
        self.assertTrue(status["install_manifest_present"])
        self.assertFalse(status["legacy_repo_graph_detected"])
        self.assertNotIn("runtime_agreement", status)
        self.assertNotIn("runtime_agreement_state", status)

    def test_status_splits_reading_limits_from_confidence_caveats(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        confidence_source = root / "confidence.md"
        confidence_source.write_text("Confidence caveat only.\n")
        gap_source = root / "gap.md"
        gap_source.write_text("Reading gap example.\n")

        confidence_binding = SourceBinding(
            source_id="note.confidence.only",
            local_path=confidence_source,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        gap_binding = SourceBinding(
            source_id="note.reading.gap",
            local_path=gap_source,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T13:00:00+00:00",
        )

        confidence_decision = sample_save_decision(
            source_ids=[confidence_binding.source_id],
            topic_path="knowledge-system/confidence-caveat-contract",
            candidate_title="Confidence Caveat Contract",
            recommended_scope=["knowledge-system"],
        )
        confidence_decision["source_reading_reports"][0]["confidence_notes"] = [
            "This is a dated internal note, not live doctrine."
        ]

        gap_decision = sample_save_decision(
            source_ids=[gap_binding.source_id],
            topic_path="knowledge-system/reading-gap-contract",
            candidate_title="Reading Gap Contract",
            recommended_scope=["knowledge-system"],
        )
        gap_decision["source_reading_reports"][0]["gaps"] = ["Appendix was not readable."]

        repo.apply_save(source_bindings=[confidence_binding], decision=confidence_decision)
        repo.apply_save(source_bindings=[gap_binding], decision=gap_decision)

        status = repo.status()
        self.assertEqual(status["ingests_with_confidence_caveats"], 1)
        self.assertEqual(status["ingests_with_reading_limits"], 1)

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
            source_family="other",
            timestamp="2026-04-03T11:00:00+00:00",
        )
        noise_binding = SourceBinding(
            source_id="note.customerio.noise",
            local_path=noise_source,
            source_kind="markdown_doc",
            source_family="other",
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

    def test_search_uses_best_matching_line_for_snippet(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "repo-readme.md"
        source_path.write_text("# Repo\n\nAIM is auth-only.\n")

        binding = SourceBinding(
            source_id="repo.readme",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/smoke-repo-readme",
            candidate_title="Smoke Repo README",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"] = [
            {
                "kind": "fact",
                "temporal_scope": "evergreen",
                "target_section": {
                    "section_id": None,
                    "heading": "Current Understanding",
                },
                "statement": "The Poker Skill agents repo describes a multi-agent Slack fleet running on the Mac host.",
                "rationale": "Background context from the README.",
                "authority_posture": "supported_by_internal_session",
                "confidence": "high",
                "evidence": [
                    {
                        "source_id": binding.source_id,
                        "locator": "line 1",
                        "notes": "",
                    }
                ],
            },
            {
                "kind": "fact",
                "temporal_scope": "evergreen",
                "target_section": {
                    "section_id": None,
                    "heading": "Current Understanding",
                },
                "statement": "AIM is auth-only.",
                "rationale": "The README names AIM as the auth-only lane.",
                "authority_posture": "supported_by_internal_session",
                "confidence": "high",
                "evidence": [
                    {
                        "source_id": binding.source_id,
                        "locator": "line 3",
                        "notes": "",
                    }
                ],
            },
        ]

        repo.apply_save(source_bindings=[binding], decision=decision)

        search = repo.search("AIM is auth-only")
        self.assertEqual(search["results"][0]["current_path"], "knowledge-system/smoke-repo-readme")
        self.assertEqual(search["results"][0]["snippet"], "- AIM is auth-only.")

    def test_search_returns_exact_current_path_section_alias_candidate(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "exact-search.md"
        source_path.write_text("Exact current path section alias search.\n")

        binding = SourceBinding(
            source_id="note.exact.search",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/exact-search-contract",
            candidate_title="Exact Search Contract",
            recommended_scope=["knowledge-system"],
        )
        decision["topic_actions"][0]["knowledge_units"][0]["kind"] = "fact"
        decision["topic_actions"][0]["knowledge_units"][0]["statement"] = (
            "Exact search should return a section trace ref for current path section aliases."
        )

        save_result = repo.apply_save(source_bindings=[binding], decision=decision)
        expected_trace_ref = save_result["touched_page_sections"][0]

        search = repo.search("knowledge-system/exact-search-contract#current_understanding")
        self.assertEqual(len(search["results"]), 1)
        self.assertEqual(search["results"][0]["match_kind"], "exact_current_path_section")
        self.assertEqual(search["results"][0]["trace_ref"], expected_trace_ref)

        normalized_search = repo.search("knowledge-system/exact-search-contract#current-understanding")
        self.assertEqual(len(normalized_search["results"]), 1)
        self.assertEqual(normalized_search["results"][0]["trace_ref"], expected_trace_ref)

    def test_search_returns_no_results_for_confident_miss(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "known.md"
        source_path.write_text(
            "This page mentions a claim moment and says some flows exist already, "
            "but it does not contain the bogus phrase.\n"
        )

        binding = SourceBinding(
            source_id="note.known",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="leaderboard/liquidity-and-reopen-loop",
            candidate_title="Liquidity And Reopen Loop",
            recommended_scope=["leaderboard"],
        )
        repo.apply_save(source_bindings=[binding], decision=decision)

        search = repo.search("this claim definitely does not exist 12345")
        self.assertEqual(search["results"], [])

    def test_trace_rejects_bogus_path_and_claim_text(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "known.md"
        source_path.write_text(
            "This page mentions a claim moment and says some flows exist already, "
            "but it does not contain the bogus phrase.\n"
        )

        binding = SourceBinding(
            source_id="note.known",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="leaderboard/liquidity-and-reopen-loop",
            candidate_title="Liquidity And Reopen Loop",
            recommended_scope=["leaderboard"],
        )
        repo.apply_save(source_bindings=[binding], decision=decision)

        with self.assertRaises(ValidationError):
            repo.trace("knowledge-system/does-not-exist")
        with self.assertRaises(ValidationError):
            repo.trace("this claim definitely does not exist 12345")

    def test_status_reports_missing_lifecycle_state_count(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        source_path = root / "known.md"
        source_path.write_text("Leaderboard liquidity and reopen loop guidance.\n")

        binding = SourceBinding(
            source_id="note.known",
            local_path=source_path,
            source_kind="markdown_doc",
            source_family="other",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="leaderboard/liquidity-and-reopen-loop",
            candidate_title="Liquidity And Reopen Loop",
            recommended_scope=["leaderboard"],
        )
        repo.apply_save(source_bindings=[binding], decision=decision)

        page_path = repo.data_root / "topics" / "leaderboard" / "liquidity-and-reopen-loop.md"
        metadata, body = split_frontmatter(page_path.read_text())
        metadata.pop("lifecycle_state", None)
        page_path.write_text(dump_frontmatter(metadata, body))

        status = repo.status()
        self.assertEqual(status["missing_lifecycle_state_count"], 1)

    def test_trace_and_status_surface_pdf_render_and_omission_state(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        copied_pdf_path = copy_fixture_pdf(root, "copied.pdf")
        secret_pdf_path = copy_fixture_pdf(root, "secret.pdf")

        copied_binding = SourceBinding(
            source_id="pdf.copied.lesson",
            local_path=copied_pdf_path,
            source_kind="pdf_research",
            source_family="pdf",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        secret_binding = SourceBinding(
            source_id="pdf.secret.lesson",
            local_path=secret_pdf_path,
            source_kind="pdf_secret",
            source_family="pdf",
            sensitivity="secret_pointer_only",
            preserve_mode="pointer",
            timestamp="2026-04-03T12:00:00+00:00",
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
            source_family="other",
            timestamp="2026-03-01T10:00:00+00:00",
        )
        current_binding = SourceBinding(
            source_id="note.customerio.current",
            local_path=current_source,
            source_kind="markdown_doc",
            source_family="other",
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

        search = repo.search("Customer.io")
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
            source_family="pdf",
            timestamp="2026-04-03T12:00:00+00:00",
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

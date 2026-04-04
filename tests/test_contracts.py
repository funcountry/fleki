from __future__ import annotations

import json
import unittest
from pathlib import Path

from common import make_temp_repo, sample_save_decision
from knowledge_graph.ids import make_opaque_id
from knowledge_graph.validation import ValidationError, validate_save_decision


class ContractsTest(unittest.TestCase):
    def test_canonical_minimal_example_validates_against_live_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        bindings_path = root / "skills" / "knowledge" / "references" / "examples" / "minimal-save-bindings.json"
        decision_path = root / "skills" / "knowledge" / "references" / "examples" / "minimal-save-decision.json"

        bindings_payload = json.loads(bindings_path.read_text())
        decision_payload = json.loads(decision_path.read_text())
        self.assertTrue(bindings_payload)
        self.assertTrue(all("source_family" in item for item in bindings_payload))
        source_bindings = {
            item["source_id"]: object()
            for item in bindings_payload
        }

        validate_save_decision(
            decision_payload,
            source_bindings=source_bindings,
            fallback_policy="forbidden",
        )

    def test_make_opaque_id_preserves_prefix(self) -> None:
        generated = make_opaque_id("kg")
        self.assertTrue(generated.startswith("kg_"))
        self.assertGreater(len(generated), 10)

    def test_fallback_helper_requires_approved_policy(self) -> None:
        temp_dir, root, _ = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)
        source_path = root / "note.md"
        source_path.write_text("hello")
        decision = {
            "ingest_summary": {
                "source_ids": ["note.1"],
                "primary_domains": ["doctrine"],
                "authority_tier": "historical_support",
                "sensitivity": "internal",
                "semantic_summary": "test",
            },
            "source_reading_reports": [
                {
                    "source_id": "note.1",
                    "reading_mode": "direct_local_text",
                    "approved_helpers_used": [
                        {
                            "helper_id": "helper.pdf",
                            "decision_log_ref": "Decision Log 1",
                            "purpose": "test",
                            "allowed_scope": ["pdf only"],
                            "expires_at": "2026-04-03T00:00:00Z",
                            "fallback_exception": True,
                        }
                    ],
                    "readable_units": ["all"],
                    "gaps": [],
                    "confidence_notes": [],
                }
            ],
            "topic_actions": [
                {
                    "topic_path": "doctrine/shared-agent-learnings",
                    "page_kind": "topic",
                    "action": "create",
                    "candidate_title": "Shared Agent Learnings",
                    "why": "semantic home",
                    "knowledge_units": [
                        {
                            "kind": "principle",
                            "target_section": {"section_id": None, "heading": "Current Understanding"},
                            "statement": "hello",
                            "rationale": "test",
                            "authority_posture": "supported_by_internal_session",
                            "confidence": "high",
                            "evidence": [
                                {"source_id": "note.1", "locator": "line 1", "notes": ""}
                            ],
                        }
                    ],
                }
            ],
            "provenance_notes": [
                {
                    "source_ids": ["note.1"],
                    "bundle_rationale": None,
                    "title": "Note 1",
                    "summary": "test",
                    "source_reading_summary": "direct",
                    "what_this_source_contributes": ["test"],
                    "knowledge_sections_touched": [
                        {"topic_path": "doctrine/shared-agent-learnings", "section_heading": "Current Understanding"}
                    ],
                    "sensitivity_notes": "internal",
                }
            ],
            "conflicts_or_questions": [],
            "asset_actions": [],
            "recommended_next_step": {
                "action": "apply_now",
                "scope": ["doctrine"],
                "why": "none",
            },
        }
        with self.assertRaises(ValidationError):
            validate_save_decision(
                decision,
                source_bindings={"note.1": object()},
                fallback_policy="forbidden",
            )

    def test_caller_owned_render_metadata_is_rejected(self) -> None:
        temp_dir, root, _ = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)
        source_path = root / "note.md"
        source_path.write_text("hello")

        decision = sample_save_decision(
            source_ids=["note.1"],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )
        decision["provenance_notes"][0]["render_manifest_paths"] = {
            "note.1": "sources/pdf/note.render.manifest.json"
        }

        with self.assertRaises(ValidationError):
            validate_save_decision(
                decision,
                source_bindings={"note.1": object()},
                fallback_policy="forbidden",
            )

    def test_source_family_topic_path_is_rejected(self) -> None:
        decision = {
            "ingest_summary": {
                "source_ids": ["note.1"],
                "primary_domains": ["codex"],
                "authority_tier": "historical_support",
                "sensitivity": "internal",
                "semantic_summary": "test",
            },
            "source_reading_reports": [
                {
                    "source_id": "note.1",
                    "reading_mode": "direct_local_text",
                    "approved_helpers_used": [],
                    "readable_units": ["all"],
                    "gaps": [],
                    "confidence_notes": [],
                }
            ],
            "topic_actions": [
                {
                    "topic_path": "codex/2026-02-27-runbook",
                    "page_kind": "topic",
                    "action": "create",
                    "candidate_title": "Bad Path",
                    "why": "bad",
                    "knowledge_units": [
                        {
                            "kind": "principle",
                            "target_section": {"section_id": None, "heading": "Current Understanding"},
                            "statement": "hello",
                            "rationale": "test",
                            "authority_posture": "supported_by_internal_session",
                            "confidence": "high",
                            "evidence": [
                                {"source_id": "note.1", "locator": "line 1", "notes": ""}
                            ],
                        }
                    ],
                }
            ],
            "provenance_notes": [
                {
                    "source_ids": ["note.1"],
                    "bundle_rationale": None,
                    "title": "Note 1",
                    "summary": "test",
                    "source_reading_summary": "direct",
                    "what_this_source_contributes": ["test"],
                    "knowledge_sections_touched": [
                        {"topic_path": "codex/2026-02-27-runbook", "section_heading": "Current Understanding"}
                    ],
                    "sensitivity_notes": "internal",
                }
            ],
            "conflicts_or_questions": [],
            "asset_actions": [],
            "recommended_next_step": {
                "action": "apply_now",
                "scope": ["codex"],
                "why": "none",
            },
        }
        with self.assertRaises(ValidationError):
            validate_save_decision(
                decision,
                source_bindings={"note.1": object()},
                fallback_policy="forbidden",
            )

    def test_invalid_temporal_scope_is_rejected(self) -> None:
        decision = sample_save_decision(
            source_ids=["note.1"],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )
        decision["topic_actions"][0]["knowledge_units"][0]["temporal_scope"] = "fresh"

        with self.assertRaises(ValidationError):
            validate_save_decision(
                decision,
                source_bindings={"note.1": object()},
                fallback_policy="forbidden",
            )

    def test_fact_kind_is_accepted(self) -> None:
        decision = sample_save_decision(
            source_ids=["note.1"],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )
        decision["topic_actions"][0]["knowledge_units"][0]["kind"] = "fact"

        validate_save_decision(
            decision,
            source_bindings={"note.1": object()},
            fallback_policy="forbidden",
        )

    def test_authority_posture_error_lists_allowed_values_and_tier_hint(self) -> None:
        decision = sample_save_decision(
            source_ids=["note.1"],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )
        decision["topic_actions"][0]["knowledge_units"][0]["authority_posture"] = "historical_support"

        with self.assertRaises(ValidationError) as error_info:
            validate_save_decision(
                decision,
                source_bindings={"note.1": object()},
                fallback_policy="forbidden",
            )

        message = str(error_info.exception)
        self.assertIn("knowledge_unit.authority_posture is invalid", message)
        self.assertIn("supported_by_internal_session", message)
        self.assertIn("supported_by_runtime", message)
        self.assertIn("'historical_support' belongs to ingest_summary.authority_tier", message)

    def test_authority_tier_error_lists_allowed_values_and_posture_hint(self) -> None:
        decision = sample_save_decision(
            source_ids=["note.1"],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )
        decision["ingest_summary"]["authority_tier"] = "supported_by_runtime"

        with self.assertRaises(ValidationError) as error_info:
            validate_save_decision(
                decision,
                source_bindings={"note.1": object()},
                fallback_policy="forbidden",
            )

        message = str(error_info.exception)
        self.assertIn("ingest_summary.authority_tier is invalid", message)
        self.assertIn("historical_support", message)
        self.assertIn("raw_runtime", message)
        self.assertIn(
            "'supported_by_runtime' belongs to knowledge_units[].authority_posture",
            message,
        )

    def test_save_rejects_stale_lifecycle_state(self) -> None:
        decision = sample_save_decision(
            source_ids=["note.1"],
            topic_path="doctrine/shared-agent-learnings",
            candidate_title="Shared Agent Learnings",
        )
        decision["topic_actions"][0]["lifecycle_state"] = "stale"

        with self.assertRaises(ValidationError):
            validate_save_decision(
                decision,
                source_bindings={"note.1": object()},
                fallback_policy="forbidden",
            )


if __name__ == "__main__":
    unittest.main()

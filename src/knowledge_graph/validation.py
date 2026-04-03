from __future__ import annotations

from typing import Any, Dict, Mapping

from .authority import (
    ASSET_ACTIONS,
    AUTHORITY_POSTURES,
    AUTHORITY_TIERS,
    CONFLICT_HANDLINGS,
    CONFLICT_TYPES,
    KNOWLEDGE_UNIT_KINDS,
    NEXT_STEP_ACTIONS,
    PAGE_KINDS,
    READING_MODES,
    SENSITIVITY_VALUES,
    TOPIC_ACTIONS,
)

FORBIDDEN_TOPIC_ROOTS = {
    "codex",
    "paperclip",
    "hermes",
    "pdf",
    "pdfs",
    "image",
    "images",
    "sessions",
}


class ValidationError(ValueError):
    pass


def _require_keys(data: Mapping[str, Any], keys: list[str], context: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValidationError(f"{context} missing keys: {', '.join(missing)}")


def _validate_helper(helper: Mapping[str, Any], fallback_policy: str) -> None:
    _require_keys(
        helper,
        [
            "helper_id",
            "decision_log_ref",
            "purpose",
            "allowed_scope",
            "expires_at",
            "fallback_exception",
        ],
        "approved helper",
    )
    if not helper["helper_id"] or not helper["decision_log_ref"]:
        raise ValidationError("approved helper must have helper_id and decision_log_ref")
    if not helper["allowed_scope"]:
        raise ValidationError("approved helper must have non-empty allowed_scope")
    if helper["fallback_exception"] and fallback_policy != "approved":
        raise ValidationError(
            "fallback_exception helper is invalid unless fallback_policy is approved"
        )


def _validate_topic_path(topic_path: str) -> None:
    if not topic_path or topic_path.startswith("/") or topic_path.endswith("/"):
        raise ValidationError("topic_path must be a relative semantic path")
    root = topic_path.split("/", 1)[0].strip().lower()
    if root in FORBIDDEN_TOPIC_ROOTS:
        raise ValidationError(
            f"topic_path root '{root}' is source-family-first and forbidden"
        )


def validate_save_decision(
    decision: Mapping[str, Any],
    source_bindings: Mapping[str, Any],
    fallback_policy: str = "forbidden",
) -> None:
    _require_keys(
        decision,
        [
            "ingest_summary",
            "source_reading_reports",
            "topic_actions",
            "provenance_notes",
            "conflicts_or_questions",
            "asset_actions",
            "recommended_next_step",
        ],
        "save decision",
    )

    ingest_summary = decision["ingest_summary"]
    _require_keys(
        ingest_summary,
        ["source_ids", "primary_domains", "authority_tier", "sensitivity", "semantic_summary"],
        "ingest_summary",
    )
    source_ids = ingest_summary["source_ids"]
    if not source_ids:
        raise ValidationError("ingest_summary.source_ids must not be empty")
    if set(source_ids) != set(source_bindings.keys()):
        raise ValidationError("source_bindings must exactly match ingest_summary.source_ids")
    if ingest_summary["authority_tier"] not in AUTHORITY_TIERS:
        raise ValidationError("ingest_summary.authority_tier is invalid")
    if ingest_summary["sensitivity"] not in SENSITIVITY_VALUES:
        raise ValidationError("ingest_summary.sensitivity is invalid")

    reading_reports = decision["source_reading_reports"]
    if {report["source_id"] for report in reading_reports} != set(source_ids):
        raise ValidationError("source_reading_reports must cover each source_id exactly once")
    for report in reading_reports:
        _require_keys(
            report,
            ["source_id", "reading_mode", "approved_helpers_used", "readable_units", "gaps", "confidence_notes"],
            "source_reading_report",
        )
        if report["reading_mode"] not in READING_MODES:
            raise ValidationError("invalid source_reading_report.reading_mode")
        for helper in report["approved_helpers_used"]:
            _validate_helper(helper, fallback_policy)

    note_coverage = set()
    for note in decision["provenance_notes"]:
        _require_keys(
            note,
            [
                "source_ids",
                "bundle_rationale",
                "title",
                "summary",
                "source_reading_summary",
                "what_this_source_contributes",
                "knowledge_sections_touched",
                "sensitivity_notes",
            ],
            "provenance_note",
        )
        if not note["source_ids"]:
            raise ValidationError("provenance_note.source_ids must not be empty")
        if len(note["source_ids"]) > 1 and not note["bundle_rationale"]:
            raise ValidationError(
                "provenance note with multiple source_ids requires bundle_rationale"
            )
        note_coverage.update(note["source_ids"])
    if not set(source_ids).issubset(note_coverage):
        raise ValidationError("every source_id must appear in provenance_notes")

    for action in decision["topic_actions"]:
        _require_keys(
            action,
            ["topic_path", "page_kind", "action", "candidate_title", "why", "knowledge_units"],
            "topic_action",
        )
        _validate_topic_path(action["topic_path"])
        if action["page_kind"] not in PAGE_KINDS:
            raise ValidationError("invalid topic_action.page_kind")
        if action["action"] not in TOPIC_ACTIONS:
            raise ValidationError("invalid topic_action.action")
        for unit in action["knowledge_units"]:
            _require_keys(
                unit,
                [
                    "kind",
                    "target_section",
                    "statement",
                    "rationale",
                    "authority_posture",
                    "confidence",
                    "evidence",
                ],
                "knowledge_unit",
            )
            if unit["kind"] not in KNOWLEDGE_UNIT_KINDS:
                raise ValidationError("invalid knowledge_unit.kind")
            if unit["authority_posture"] not in AUTHORITY_POSTURES:
                raise ValidationError("invalid knowledge_unit.authority_posture")
            if unit["confidence"] not in {"high", "medium", "low"}:
                raise ValidationError("invalid knowledge_unit.confidence")
            if not unit["evidence"]:
                raise ValidationError("knowledge_unit.evidence must not be empty")
            for evidence in unit["evidence"]:
                _require_keys(evidence, ["source_id", "locator", "notes"], "knowledge_unit.evidence")
                if evidence["source_id"] not in source_bindings:
                    raise ValidationError("knowledge_unit.evidence source_id is unknown")
                if not evidence["locator"]:
                    raise ValidationError("knowledge_unit.evidence locator must not be empty")

    for item in decision["conflicts_or_questions"]:
        _require_keys(item, ["type", "topic_path", "description", "suggested_handling"], "conflict_or_question")
        if item["type"] not in CONFLICT_TYPES:
            raise ValidationError("invalid conflict_or_question.type")
        if item["suggested_handling"] not in CONFLICT_HANDLINGS:
            raise ValidationError("invalid conflict_or_question.suggested_handling")
        _validate_topic_path(item["topic_path"])

    for item in decision["asset_actions"]:
        _require_keys(item, ["asset_ref", "action", "target_topic_path", "why"], "asset_action")
        if item["action"] not in ASSET_ACTIONS:
            raise ValidationError("invalid asset_action.action")
        if item["target_topic_path"]:
            _validate_topic_path(item["target_topic_path"])

    next_step = decision["recommended_next_step"]
    _require_keys(next_step, ["action", "scope", "why"], "recommended_next_step")
    if next_step["action"] not in NEXT_STEP_ACTIONS:
        raise ValidationError("invalid recommended_next_step.action")

from __future__ import annotations

AUTHORITY_TIERS = {
    "live_doctrine",
    "raw_runtime",
    "historical_support",
    "generated_mirror",
    "mixed",
}

AUTHORITY_POSTURES = {
    "live_doctrine",
    "supported_by_runtime",
    "supported_by_internal_session",
    "tentative",
    "mixed",
}

PAGE_KINDS = {
    "topic",
    "playbook",
    "decision",
    "glossary",
}

SENSITIVITY_VALUES = {
    "public",
    "internal",
    "restricted_prompt_bearing",
    "secret_pointer_only",
    "mixed",
}

READING_MODES = {
    "direct_local_text",
    "direct_local_pdf",
    "direct_local_image",
    "direct_local_multimodal",
    "mixed",
}

PDF_RENDER_FIDELITY_MODES = {
    "high_fidelity",
    "limited_fidelity",
}

PDF_RENDER_OMISSION_REASONS = {
    "disallowed_by_sensitivity",
    "disallowed_by_storage_mode",
}

TOPIC_ACTIONS = {
    "create",
    "update",
    "append_evidence",
    "split_suggest",
    "merge_suggest",
    "rehome_suggest",
    "no_change",
}

KNOWLEDGE_UNIT_KINDS = {
    "principle",
    "playbook",
    "decision",
    "pattern",
    "regression",
    "glossary",
    "question",
}

CONFLICT_TYPES = {
    "conflict",
    "missing_context",
    "authority_collision",
    "taxonomy_question",
    "weak_signal",
    "helper_needed",
}

CONFLICT_HANDLINGS = {
    "apply_now",
    "queue_rebuild",
    "human_review",
}

ASSET_ACTIONS = {
    "preserve_only",
    "attach_to_topic",
    "caption_and_attach",
    "redact",
}

NEXT_STEP_ACTIONS = {
    "apply_now",
    "queue_rebuild_topic",
    "human_review_required",
}

TEMPORAL_SCOPES = {
    "evergreen",
    "time_bound",
    "ephemeral",
}

SAVE_LIFECYCLE_STATES = {
    "current",
    "historical",
}

LIFECYCLE_STATES = SAVE_LIFECYCLE_STATES | {"stale"}

_AUTHORITY_RANKS = {
    "live_doctrine": 100,
    "supported_by_runtime": 80,
    "supported_by_internal_session": 60,
    "mixed": 50,
    "tentative": 25,
}


def authority_rank(posture: str) -> int:
    return _AUTHORITY_RANKS.get(posture, 0)


def merge_authority_postures(values: list[str]) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return "tentative"
    unique = set(cleaned)
    if len(unique) == 1:
        return cleaned[0]
    if "live_doctrine" in unique and len(unique) > 1:
        return "mixed"
    return max(unique, key=authority_rank)

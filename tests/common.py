from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from knowledge_graph import KnowledgeRepository, SourceBinding  # noqa: E402


def make_temp_repo() -> Tuple[TemporaryDirectory, Path, KnowledgeRepository]:
    tmp = TemporaryDirectory()
    root = Path(tmp.name)
    repo = KnowledgeRepository(root)
    repo.initialize_layout()
    return tmp, root, repo


def sample_save_decision(*, source_ids, topic_path, candidate_title, authority_tier="mixed", recommended_scope=None):
    if recommended_scope is None:
        recommended_scope = [topic_path.split("/", 1)[0]]
    return {
        "ingest_summary": {
            "source_ids": list(source_ids),
            "primary_domains": [topic_path.split("/", 1)[0]],
            "authority_tier": authority_tier,
            "sensitivity": "internal",
            "semantic_summary": f"Knowledge contribution for {topic_path}",
        },
        "source_reading_reports": [
            {
                "source_id": source_id,
                "reading_mode": "direct_local_text",
                "approved_helpers_used": [],
                "readable_units": ["full text"],
                "gaps": [],
                "confidence_notes": [],
            }
            for source_id in source_ids
        ],
        "topic_actions": [
            {
                "topic_path": topic_path,
                "page_kind": "topic",
                "action": "create",
                "candidate_title": candidate_title,
                "why": "Durable knowledge belongs here.",
                "knowledge_units": [
                    {
                        "kind": "principle",
                        "target_section": {
                            "section_id": None,
                            "heading": "Current Understanding",
                        },
                        "statement": f"{candidate_title} is now part of the shared graph.",
                        "rationale": "The topic captures the semantic meaning of the source material.",
                        "authority_posture": "supported_by_internal_session",
                        "confidence": "high",
                        "evidence": [
                            {
                                "source_id": source_id,
                                "locator": "top-level source review",
                                "notes": "",
                            }
                            for source_id in source_ids
                        ],
                    }
                ],
            }
        ],
        "provenance_notes": [
            {
                "source_ids": [source_id],
                "bundle_rationale": None,
                "title": f"Provenance for {source_id}",
                "summary": f"Source {source_id} contributed to {topic_path}.",
                "source_reading_summary": "Read directly from the local filesystem.",
                "what_this_source_contributes": [f"Evidence for {topic_path}."],
                "knowledge_sections_touched": [
                    {
                        "topic_path": topic_path,
                        "section_heading": "Current Understanding",
                    }
                ],
                "sensitivity_notes": "internal",
            }
            for source_id in source_ids
        ],
        "conflicts_or_questions": [],
        "asset_actions": [],
        "recommended_next_step": {
            "action": "queue_rebuild_topic",
            "scope": list(recommended_scope),
            "why": "Rebuild later to refresh semantic neighbors and indexes.",
        },
    }

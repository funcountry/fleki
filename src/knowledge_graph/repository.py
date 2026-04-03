from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter, OrderedDict, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .authority import authority_rank, merge_authority_postures
from .frontmatter import dump_frontmatter, split_frontmatter
from .ids import make_opaque_id, safe_filename, section_key, slugify
from .models import RebuildPlan, RebuildPageUpdate, SourceBinding
from .text import parse_sections, render_page, tokenize
from .validation import ValidationError, validate_save_decision


class KnowledgeRepository:
    def __init__(self, root: Path | str, fallback_policy: str = "forbidden") -> None:
        self.root = Path(root)
        self.fallback_policy = fallback_policy
        self.knowledge_root = self.root / "knowledge"
        self.topics_root = self.knowledge_root / "topics"
        self.provenance_root = self.knowledge_root / "provenance"
        self.sources_root = self.knowledge_root / "sources"
        self.assets_root = self.knowledge_root / "assets"
        self.receipts_root = self.knowledge_root / "receipts"
        self.search_root = self.knowledge_root / "search"

    def initialize_layout(self) -> None:
        for path in [
            self.topics_root / "indexes",
            self.provenance_root,
            self.sources_root,
            self.assets_root,
            self.receipts_root / "save",
            self.receipts_root / "search",
            self.receipts_root / "trace",
            self.receipts_root / "rebuild",
            self.receipts_root / "status",
            self.search_root,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        knowledge_readme = self.knowledge_root / "README.md"
        if not knowledge_readme.exists():
            knowledge_readme.write_text(
                "# Knowledge Tree\n\n"
                "This directory is the canonical on-disk knowledge graph for Fleki.\n"
                "Semantic pages live under `topics/`, provenance under `provenance/`, raw sources under `sources/`, and command receipts under `receipts/`.\n"
            )

        search_readme = self.search_root / "README.md"
        if not search_readme.exists():
            search_readme.write_text(
                "# Optional Search Support State\n\n"
                "This directory is reserved for approval-gated support state only.\n"
                "The default architecture must remain truthful and useful without anything new appearing here.\n"
            )

    def apply_save(
        self,
        *,
        source_bindings: Sequence[SourceBinding],
        decision: Mapping[str, Any],
    ) -> Dict[str, Any]:
        self.initialize_layout()
        bindings_by_id = {binding.source_id: binding for binding in source_bindings}
        validate_save_decision(decision, bindings_by_id, fallback_policy=self.fallback_policy)
        timestamp = self._timestamp()

        source_records = self._persist_source_records(bindings_by_id, timestamp)
        provenance_records = self._persist_provenance_notes(
            decision=decision,
            source_records=source_records,
            timestamp=timestamp,
        )
        topic_records = self._apply_topic_actions(
            decision=decision,
            provenance_records=provenance_records,
            timestamp=timestamp,
        )
        receipt = self._write_save_receipt(
            decision=decision,
            source_records=source_records,
            provenance_records=provenance_records,
            topic_records=topic_records,
            timestamp=timestamp,
        )
        return receipt

    def search(self, query: str, limit: int = 5, write_receipt: bool = True) -> Dict[str, Any]:
        self.initialize_layout()
        query_tokens = tokenize(query)
        pages = self._load_topics()
        provenance_map = self._load_provenance_map()
        results = []
        for page in pages:
            score, match_heading, match_section_id, snippet = self._score_page(
                page=page, query=query, query_tokens=query_tokens
            )
            if score <= 0:
                continue
            provenance_refs = self._supporting_provenance_for_section(
                page_metadata=page["metadata"],
                section_id=match_section_id,
            )
            results.append(
                {
                    "knowledge_id": page["metadata"]["knowledge_id"],
                    "path": self._relative(page["path"]),
                    "current_path": page["metadata"]["current_path"],
                    "page_kind": page["metadata"]["page_kind"],
                    "authority_posture": page["metadata"].get("authority_posture", "tentative"),
                    "match_heading": match_heading,
                    "match_section_id": match_section_id,
                    "snippet": snippet,
                    "provenance_paths": [
                        provenance_map[prov_id]["relative_path"]
                        for prov_id in provenance_refs
                        if prov_id in provenance_map
                    ],
                    "trace_ref": (
                        f"{page['metadata']['knowledge_id']}#{match_section_id}"
                        if match_section_id
                        else page["metadata"]["knowledge_id"]
                    ),
                    "score": score,
                }
            )

        results.sort(
            key=lambda item: (
                item["score"],
                authority_rank(item["authority_posture"]),
                item["current_path"],
            ),
            reverse=True,
        )
        payload = {
            "query": query,
            "approved_helpers_used": [],
            "results": results[:limit],
        }
        if write_receipt:
            self._write_receipt("search", payload, timestamp=self._timestamp())
        return payload

    def trace(self, ref: str, write_receipt: bool = True) -> Dict[str, Any]:
        self.initialize_layout()
        page, section_id = self._resolve_trace_target(ref)
        provenance_map = self._load_provenance_map()
        relevant_provenance = self._supporting_provenance_for_section(
            page_metadata=page["metadata"], section_id=section_id
        )
        provenance_entries = [provenance_map[prov_id] for prov_id in relevant_provenance if prov_id in provenance_map]
        source_paths = []
        for entry in provenance_entries:
            source_paths.extend(entry["metadata"].get("source_record_paths", []))

        payload = {
            "ref": ref,
            "knowledge_id": page["metadata"]["knowledge_id"],
            "path": self._relative(page["path"]),
            "current_path": page["metadata"]["current_path"],
            "section_id": section_id,
            "authority_posture": page["metadata"].get("authority_posture", "tentative"),
            "provenance": [entry["relative_path"] for entry in provenance_entries],
            "source_records": source_paths,
        }
        if write_receipt:
            self._write_receipt("trace", payload, timestamp=self._timestamp())
        return payload

    def status(self, write_receipt: bool = True) -> Dict[str, Any]:
        self.initialize_layout()
        save_receipts = self._load_receipts("save")
        rebuild_receipts = self._load_receipts("rebuild")
        cleared_scopes = {
            scope
            for receipt in rebuild_receipts
            for scope in receipt["metadata"].get("cleared_scopes", [])
        }
        pending_scopes = []
        reading_limit_count = 0
        conflict_count = 0
        topic_counter: Counter[str] = Counter()
        approved_helpers: set[str] = set()

        for receipt in save_receipts:
            metadata = receipt["metadata"]
            for scope in metadata.get("rebuild_pending_scopes", []):
                if scope not in cleared_scopes:
                    pending_scopes.append(scope)
            if metadata.get("reading_limitations"):
                reading_limit_count += 1
            for conflict in metadata.get("conflicts_or_questions", []):
                if conflict["type"] in {"conflict", "authority_collision"}:
                    conflict_count += 1
            for touched in metadata.get("touched_topics", []):
                topic_counter[touched] += 1
            for helper in metadata.get("approved_helpers_used", []):
                approved_helpers.add(helper["helper_id"])

        pages = self._load_topics()
        last_rebuild = None
        if rebuild_receipts:
            last_rebuild = max(receipt["metadata"]["created_at"] for receipt in rebuild_receipts)

        payload = {
            "pending_source_ingests": 0,
            "stale_knowledge_pages": len(set(pending_scopes)),
            "ingests_with_reading_limits": reading_limit_count,
            "approved_helpers_in_use": sorted(approved_helpers),
            "rebuild_pending": sorted(set(pending_scopes)),
            "hot_topics": [topic for topic, _ in topic_counter.most_common(3)],
            "unresolved_contradictions": conflict_count,
            "last_rebuild": last_rebuild,
            "topic_count": len(pages),
        }
        if write_receipt:
            self._write_receipt("status", payload, timestamp=self._timestamp())
        return payload

    def apply_rebuild(self, plan: RebuildPlan) -> Dict[str, Any]:
        self.initialize_layout()
        timestamp = self._timestamp()
        changes = []
        for update in plan.page_updates:
            change = self._apply_page_update(update, timestamp=timestamp)
            if change is not None:
                changes.append(change)
        if plan.refresh_indexes:
            self._refresh_indexes(timestamp)
        payload = {
            "scope": list(plan.scope),
            "changes": changes,
            "open_questions": list(plan.open_questions),
            "cleared_scopes": list(plan.scope),
            "approved_helpers_used": [],
        }
        self._write_receipt("rebuild", payload, timestamp=timestamp)
        return payload

    def _persist_source_records(
        self,
        bindings_by_id: Mapping[str, SourceBinding],
        timestamp: str,
    ) -> Dict[str, Dict[str, Any]]:
        records: Dict[str, Dict[str, Any]] = {}
        for source_id, binding in bindings_by_id.items():
            if not binding.local_path.exists():
                raise FileNotFoundError(f"source path does not exist: {binding.local_path}")

            family = self._source_family(binding)
            destination_dir = self.sources_root / family
            destination_dir.mkdir(parents=True, exist_ok=True)

            safe_id = safe_filename(source_id)
            safe_name = safe_filename(binding.local_path.name)
            raw_destination = destination_dir / f"{safe_id}__{safe_name}"
            manifest_path = Path(f"{raw_destination}.record.json")

            if binding.preserve_mode == "pointer" or binding.sensitivity == "secret_pointer_only":
                storage_mode = "pointer"
                pointer_payload = {
                    "source_id": source_id,
                    "source_kind": binding.source_kind,
                    "authority_tier": binding.authority_tier,
                    "sensitivity": binding.sensitivity,
                    "original_path": str(binding.local_path),
                    "sha256": self._sha256(binding.local_path),
                    "captured_at": timestamp,
                }
                raw_destination = Path(f"{raw_destination}.pointer.json")
                raw_destination.write_text(json.dumps(pointer_payload, indent=2, sort_keys=True))
            else:
                storage_mode = "copy"
                shutil.copy2(binding.local_path, raw_destination)

            manifest_payload = {
                "source_id": source_id,
                "source_kind": binding.source_kind,
                "authority_tier": binding.authority_tier,
                "sensitivity": binding.sensitivity,
                "storage_mode": storage_mode,
                "relative_path": self._relative(raw_destination),
                "sha256": self._sha256(binding.local_path),
                "captured_at": timestamp,
                "original_path": str(binding.local_path),
            }
            manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True))
            records[source_id] = {
                "manifest_path": manifest_path,
                "raw_path": raw_destination,
                "relative_path": self._relative(raw_destination),
                "manifest_relative_path": self._relative(manifest_path),
                "binding": binding,
            }
        return records

    def _persist_provenance_notes(
        self,
        *,
        decision: Mapping[str, Any],
        source_records: Mapping[str, Dict[str, Any]],
        timestamp: str,
    ) -> Dict[str, Dict[str, Any]]:
        reports_by_source = {
            report["source_id"]: report for report in decision["source_reading_reports"]
        }
        note_records: Dict[str, Dict[str, Any]] = {}
        for note in decision["provenance_notes"]:
            provenance_id = make_opaque_id("prov")
            family = self._provenance_family(note["source_ids"], source_records)
            path = self.provenance_root / family / f"{provenance_id}.md"
            path.parent.mkdir(parents=True, exist_ok=True)

            approved_helpers = []
            reading_modes = {}
            reading_gaps = {}
            for source_id in note["source_ids"]:
                report = reports_by_source[source_id]
                reading_modes[source_id] = report["reading_mode"]
                reading_gaps[source_id] = report["gaps"]
                approved_helpers.extend(report["approved_helpers_used"])

            metadata = {
                "provenance_id": provenance_id,
                "source_ids": list(note["source_ids"]),
                "source_record_paths": [
                    source_records[source_id]["manifest_relative_path"]
                    for source_id in note["source_ids"]
                ],
                "bundle_rationale": note["bundle_rationale"],
                "source_reading_modes": reading_modes,
                "approved_helpers_used": approved_helpers,
                "reading_gaps": reading_gaps,
                "knowledge_sections_touched": list(note["knowledge_sections_touched"]),
                "created_at": timestamp,
            }
            body = self._render_provenance_body(note)
            path.write_text(dump_frontmatter(metadata, body))

            note_records[provenance_id] = {
                "provenance_id": provenance_id,
                "path": path,
                "relative_path": self._relative(path),
                "source_ids": list(note["source_ids"]),
            }
        return note_records

    def _apply_topic_actions(
        self,
        *,
        decision: Mapping[str, Any],
        provenance_records: Mapping[str, Dict[str, Any]],
        timestamp: str,
    ) -> Dict[str, Any]:
        source_to_provenance_ids: Dict[str, List[str]] = defaultdict(list)
        for provenance_id, record in provenance_records.items():
            for source_id in record["source_ids"]:
                source_to_provenance_ids[source_id].append(provenance_id)

        touched_sections = []
        touched_topics = []
        page_records = {}

        for action in decision["topic_actions"]:
            if action["action"] in {"split_suggest", "merge_suggest", "rehome_suggest", "no_change"}:
                continue

            page_path = self.topics_root / f"{action['topic_path']}.md"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            if page_path.exists():
                metadata, body = split_frontmatter(page_path.read_text())
                title, sections = parse_sections(body)
            else:
                metadata = {}
                title = action["candidate_title"]
                sections = OrderedDict()

            knowledge_id = metadata.get("knowledge_id", make_opaque_id("kg"))
            aliases = list(metadata.get("aliases", []))
            section_ids = dict(metadata.get("section_ids", {}))
            section_support = dict(metadata.get("section_support", {}))
            authority_values = []

            for unit in action["knowledge_units"]:
                heading = unit["target_section"]["heading"]
                key = section_key(heading)
                section_id = (
                    unit["target_section"].get("section_id")
                    or section_ids.get(key)
                    or make_opaque_id("sec")
                )
                section_ids[key] = section_id
                section_lines = sections.setdefault(heading, [])
                bullet = f"- {unit['statement']}"
                if bullet not in section_lines:
                    if section_lines and section_lines[-1] != "":
                        section_lines.append("")
                    section_lines.append(bullet)
                authority_values.append(unit["authority_posture"])

                support_entries = list(section_support.get(section_id, []))
                for evidence in unit["evidence"]:
                    for provenance_id in source_to_provenance_ids[evidence["source_id"]]:
                        support = {
                            "provenance_id": provenance_id,
                            "locator": evidence["locator"],
                            "notes": evidence["notes"],
                        }
                        if support not in support_entries:
                            support_entries.append(support)
                section_support[section_id] = support_entries
                touched_sections.append(f"{knowledge_id}#{section_id}")
                touched_topics.append(action["topic_path"])

            metadata.update(
                {
                    "knowledge_id": knowledge_id,
                    "current_path": action["topic_path"],
                    "aliases": aliases,
                    "page_kind": action["page_kind"],
                    "parent_topics": self._parent_topics(action["topic_path"]),
                    "section_ids": section_ids,
                    "section_support": section_support,
                    "authority_posture": merge_authority_postures(authority_values),
                    "last_updated_at": timestamp,
                    "last_reorganized_at": metadata.get("last_reorganized_at"),
                    "supersedes": metadata.get("supersedes", []),
                }
            )

            provenance_refs = []
            for entries in section_support.values():
                for entry in entries:
                    provenance_id = entry["provenance_id"]
                    if provenance_id in provenance_records:
                        provenance_refs.append(provenance_records[provenance_id]["relative_path"])

            page_path.write_text(dump_frontmatter(metadata, render_page(title, sections, provenance_refs)))
            page_records[action["topic_path"]] = {
                "knowledge_id": knowledge_id,
                "path": page_path,
                "relative_path": self._relative(page_path),
            }

        return {
            "touched_sections": touched_sections,
            "touched_topics": sorted(set(touched_topics)),
            "pages": page_records,
        }

    def _write_save_receipt(
        self,
        *,
        decision: Mapping[str, Any],
        source_records: Mapping[str, Dict[str, Any]],
        provenance_records: Mapping[str, Dict[str, Any]],
        topic_records: Mapping[str, Any],
        timestamp: str,
    ) -> Dict[str, Any]:
        receipt_id = make_opaque_id("receipt")
        path = self.receipts_root / "save" / f"{receipt_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)

        reading_limitations = []
        approved_helpers_used = []
        for report in decision["source_reading_reports"]:
            if report["gaps"] or report["confidence_notes"]:
                reading_limitations.append(
                    {
                        "source_id": report["source_id"],
                        "gaps": report["gaps"],
                        "confidence_notes": report["confidence_notes"],
                    }
                )
            approved_helpers_used.extend(report["approved_helpers_used"])

        metadata = {
            "receipt_id": receipt_id,
            "command": "save",
            "created_at": timestamp,
            "saved_source_records": [
                source_records[source_id]["manifest_relative_path"]
                for source_id in decision["ingest_summary"]["source_ids"]
            ],
            "saved_raw_sources": [
                source_records[source_id]["relative_path"]
                for source_id in decision["ingest_summary"]["source_ids"]
            ],
            "provenance_paths": [
                record["relative_path"] for record in provenance_records.values()
            ],
            "touched_page_sections": topic_records["touched_sections"],
            "touched_topics": topic_records["touched_topics"],
            "reading_limitations": reading_limitations,
            "approved_helpers_used": approved_helpers_used,
            "rebuild_pending_scopes": list(decision["recommended_next_step"]["scope"])
            if decision["recommended_next_step"]["action"] == "queue_rebuild_topic"
            else [],
            "conflicts_or_questions": list(decision["conflicts_or_questions"]),
        }
        body = (
            f"# Save Receipt\n\n"
            f"## Summary\n- {decision['ingest_summary']['semantic_summary']}\n\n"
            f"## Next Step\n- `{decision['recommended_next_step']['action']}`\n"
            f"- {decision['recommended_next_step']['why']}\n"
        )
        path.write_text(dump_frontmatter(metadata, body))
        return {
            "result": "applied",
            "receipt_path": self._relative(path),
            "saved_sources": metadata["saved_raw_sources"],
            "provenance_notes": metadata["provenance_paths"],
            "touched_page_sections": metadata["touched_page_sections"],
            "touched_topics": metadata["touched_topics"],
            "reading_limitations": metadata["reading_limitations"],
            "approved_helpers_used": metadata["approved_helpers_used"],
            "rebuild_pending_scopes": metadata["rebuild_pending_scopes"],
        }

    def _write_receipt(self, kind: str, payload: Mapping[str, Any], timestamp: str) -> None:
        receipt_id = make_opaque_id("receipt")
        path = self.receipts_root / kind / f"{receipt_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"receipt_id": receipt_id, "command": kind, "created_at": timestamp}
        metadata.update(payload)
        body = f"# {kind.title()} Receipt\n\nGenerated at `{timestamp}`.\n"
        path.write_text(dump_frontmatter(metadata, body))

    def _apply_page_update(
        self,
        update: RebuildPageUpdate,
        *,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        page = self._find_topic_page_by_knowledge_id(update.knowledge_id)
        if page is None:
            return None
        metadata = page["metadata"]
        body = page["body"]
        old_current_path = metadata["current_path"]
        target_path = page["path"]
        if update.new_current_path and update.new_current_path != old_current_path:
            target_path = self.topics_root / f"{update.new_current_path}.md"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            aliases = list(metadata.get("aliases", []))
            if old_current_path not in aliases:
                aliases.append(old_current_path)
            metadata["aliases"] = aliases
            metadata["current_path"] = update.new_current_path
            metadata["parent_topics"] = self._parent_topics(update.new_current_path)

        supersedes = list(metadata.get("supersedes", []))
        for item in update.add_supersedes:
            if item not in supersedes:
                supersedes.append(item)
        metadata["supersedes"] = supersedes
        metadata["last_reorganized_at"] = timestamp

        target_path.write_text(dump_frontmatter(metadata, body))
        if target_path != page["path"] and page["path"].exists():
            page["path"].unlink()

        return {
            "knowledge_id": update.knowledge_id,
            "old_current_path": old_current_path,
            "new_current_path": metadata["current_path"],
            "note": update.note,
        }

    def _refresh_indexes(self, timestamp: str) -> None:
        pages = sorted(self._load_topics(), key=lambda item: item["metadata"]["current_path"])
        by_topic_path = self.topics_root / "indexes" / "by-topic.md"
        recent_changes_path = self.topics_root / "indexes" / "recent-changes.md"
        unresolved_path = self.topics_root / "indexes" / "unresolved-questions.md"

        by_topic_body = "# By Topic\n\n"
        for page in pages:
            by_topic_body += (
                f"- `{page['metadata']['current_path']}`"
                f" ({page['metadata']['page_kind']}, {page['metadata'].get('authority_posture', 'tentative')})\n"
            )
        by_topic_path.write_text(dump_frontmatter({"generated_at": timestamp}, by_topic_body))

        recent_sorted = sorted(
            pages,
            key=lambda item: (
                item["metadata"].get("last_reorganized_at") or "",
                item["metadata"].get("last_updated_at") or "",
            ),
            reverse=True,
        )
        recent_body = "# Recent Changes\n\n"
        for page in recent_sorted[:20]:
            recent_body += (
                f"- `{page['metadata']['current_path']}`"
                f" updated=`{page['metadata'].get('last_updated_at')}`"
                f" reorganized=`{page['metadata'].get('last_reorganized_at')}`\n"
            )
        recent_changes_path.write_text(dump_frontmatter({"generated_at": timestamp}, recent_body))

        conflicts = []
        for receipt in self._load_receipts("save"):
            for item in receipt["metadata"].get("conflicts_or_questions", []):
                if item["type"] in {"conflict", "authority_collision", "taxonomy_question"}:
                    conflicts.append(item)
        unresolved_body = "# Unresolved Questions\n\n"
        if conflicts:
            for item in conflicts:
                unresolved_body += f"- `{item['topic_path']}`: {item['description']}\n"
        else:
            unresolved_body += "- none\n"
        unresolved_path.write_text(dump_frontmatter({"generated_at": timestamp}, unresolved_body))

    def _load_topics(self) -> List[Dict[str, Any]]:
        pages = []
        if not self.topics_root.exists():
            return pages
        for path in self.topics_root.rglob("*.md"):
            if path.name == "README.md":
                continue
            try:
                metadata, body = split_frontmatter(path.read_text())
            except Exception:
                continue
            if "knowledge_id" not in metadata:
                continue
            title, sections = parse_sections(body)
            pages.append(
                {
                    "path": path,
                    "relative_path": self._relative(path),
                    "metadata": metadata,
                    "body": body,
                    "title": title,
                    "sections": sections,
                }
            )
        return pages

    def _load_provenance_map(self) -> Dict[str, Dict[str, Any]]:
        items = {}
        if not self.provenance_root.exists():
            return items
        for path in self.provenance_root.rglob("*.md"):
            try:
                metadata, body = split_frontmatter(path.read_text())
            except Exception:
                continue
            provenance_id = metadata.get("provenance_id")
            if not provenance_id:
                continue
            items[provenance_id] = {
                "path": path,
                "relative_path": self._relative(path),
                "metadata": metadata,
                "body": body,
            }
        return items

    def _load_receipts(self, kind: str) -> List[Dict[str, Any]]:
        items = []
        receipt_dir = self.receipts_root / kind
        if not receipt_dir.exists():
            return items
        for path in receipt_dir.rglob("*.md"):
            try:
                metadata, body = split_frontmatter(path.read_text())
            except Exception:
                continue
            items.append({"path": path, "metadata": metadata, "body": body})
        return items

    def _resolve_trace_target(self, ref: str) -> Tuple[Dict[str, Any], Optional[str]]:
        pages = self._load_topics()
        page_lookup = {page["metadata"]["knowledge_id"]: page for page in pages}
        ref_value = ref.strip()
        section_id = None
        if "#" in ref_value:
            ref_value, section_id = ref_value.split("#", 1)

        if ref_value in page_lookup:
            return page_lookup[ref_value], section_id

        for page in pages:
            aliases = set(page["metadata"].get("aliases", []))
            aliases.add(page["metadata"]["current_path"])
            if ref_value in aliases:
                return page, section_id

        lowered = ref.lower()
        matches = []
        for page in pages:
            haystack = " ".join(
                [
                    page["title"],
                    page["metadata"]["current_path"],
                    " ".join(sum(page["sections"].values(), [])),
                ]
            ).lower()
            if lowered in haystack:
                matches.append(page)
        if not matches:
            raise ValidationError(f"unable to trace ref: {ref}")
        matches.sort(
            key=lambda page: (
                authority_rank(page["metadata"].get("authority_posture", "tentative")),
                page["metadata"]["current_path"],
            ),
            reverse=True,
        )
        return matches[0], section_id

    def _find_topic_page_by_knowledge_id(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        for page in self._load_topics():
            if page["metadata"]["knowledge_id"] == knowledge_id:
                return page
        return None

    def _score_page(
        self,
        *,
        page: Mapping[str, Any],
        query: str,
        query_tokens: List[str],
    ) -> Tuple[int, Optional[str], Optional[str], str]:
        current_path = page["metadata"]["current_path"]
        aliases = " ".join(page["metadata"].get("aliases", []))
        title = page["title"]
        body = page["body"]
        haystack = " ".join([current_path, aliases, title, body]).lower()
        if query.lower() not in haystack and not any(token in haystack for token in query_tokens):
            return 0, None, None, ""

        page_score = 0
        if query.lower() in haystack:
            page_score += 10
        page_score += sum(haystack.count(token) for token in query_tokens)
        page_score += authority_rank(page["metadata"].get("authority_posture", "tentative"))

        best_heading = None
        best_section_id = None
        best_snippet = title
        best_section_score = -1
        section_ids = page["metadata"].get("section_ids", {})
        for heading, section_lines in page["sections"].items():
            section_text = " ".join(section_lines).lower()
            score = sum(section_text.count(token) for token in query_tokens)
            if heading.lower().find(query.lower()) != -1:
                score += 5
            if score > best_section_score:
                best_section_score = score
                best_heading = heading
                best_snippet = next(
                    (line for line in section_lines if line.strip()),
                    heading,
                )
                best_section_id = section_ids.get(section_key(heading))

        return page_score + max(best_section_score, 0), best_heading, best_section_id, best_snippet

    def _supporting_provenance_for_section(
        self,
        *,
        page_metadata: Mapping[str, Any],
        section_id: Optional[str],
    ) -> List[str]:
        section_support = page_metadata.get("section_support", {})
        if section_id:
            entries = section_support.get(section_id, [])
        else:
            entries = [
                item
                for values in section_support.values()
                for item in values
            ]
        provenance_ids = []
        for entry in entries:
            provenance_id = entry["provenance_id"]
            if provenance_id not in provenance_ids:
                provenance_ids.append(provenance_id)
        return provenance_ids

    def _render_provenance_body(self, note: Mapping[str, Any]) -> str:
        lines = [
            f"# {note['title']}",
            "",
            "## Summary",
            f"- {note['summary']}",
            "",
            "## Source Reading Summary",
            f"- {note['source_reading_summary']}",
            "",
            "## What this source contributes",
        ]
        for item in note["what_this_source_contributes"]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Sensitivity Notes",
                f"- {note['sensitivity_notes']}",
                "",
            ]
        )
        return "\n".join(lines)

    def _source_family(self, binding: SourceBinding) -> str:
        kind = binding.source_kind.lower()
        suffix = binding.local_path.suffix.lower()
        if "codex" in kind:
            return "codex"
        if "paperclip" in kind:
            return "paperclip"
        if "hermes" in kind:
            return "hermes"
        if "pdf" in kind or suffix == ".pdf":
            return "pdf"
        if "image" in kind or suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            return "images"
        return "other"

    def _provenance_family(
        self,
        source_ids: Iterable[str],
        source_records: Mapping[str, Dict[str, Any]],
    ) -> str:
        families = {
            self._source_family(source_records[source_id]["binding"])
            for source_id in source_ids
        }
        if len(families) == 1:
            return next(iter(families))
        return "mixed"

    def _parent_topics(self, current_path: str) -> List[str]:
        parts = current_path.split("/")
        parents = []
        for index in range(1, len(parts)):
            parents.append("/".join(parts[:index]))
        return parents[:-1] if parents else []

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

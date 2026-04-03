from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .authority import authority_rank, merge_authority_postures
from .frontmatter import dump_frontmatter, split_frontmatter
from .ids import make_opaque_id, safe_filename, section_key, slugify
from .layout import resolve_knowledge_layout
from .models import PdfRenderBundle, RebuildPlan, RebuildPageUpdate, ResolvedKnowledgeLayout, SourceBinding
from .pdf_render import render_pdf_bundle
from .text import parse_sections, render_page, tokenize
from .validation import ValidationError, validate_save_decision


class KnowledgeRepository:
    def __init__(
        self,
        root: ResolvedKnowledgeLayout | Path | str,
        fallback_policy: str = "forbidden",
        *,
        install_manifest_path: Path | str | None = None,
        repo_root: Path | str | None = None,
    ) -> None:
        if isinstance(root, ResolvedKnowledgeLayout):
            self.layout = root
        else:
            self.layout = resolve_knowledge_layout(
                data_root=root,
                install_manifest_path=install_manifest_path,
                repo_root=repo_root,
            )
        self.fallback_policy = fallback_policy
        self.root = self.layout.data_root
        self.data_root = self.layout.data_root
        self.config_root = self.layout.config_root
        self.state_root = self.layout.state_root
        self.install_manifest_path = self.layout.install_manifest_path
        self.knowledge_root = self.data_root
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
        pdf_render_bundles = self._persist_pdf_render_bundles(
            source_records=source_records,
            timestamp=timestamp,
        )
        provenance_records = self._persist_provenance_notes(
            decision=decision,
            source_records=source_records,
            pdf_render_bundles=pdf_render_bundles,
            timestamp=timestamp,
        )
        topic_records = self._apply_topic_actions(
            decision=decision,
            source_records=source_records,
            provenance_records=provenance_records,
            timestamp=timestamp,
        )
        receipt = self._write_save_receipt(
            decision=decision,
            source_records=source_records,
            pdf_render_bundles=pdf_render_bundles,
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
        replacement_paths = self._replacement_paths_by_knowledge_id(pages)
        results = []
        for page in pages:
            score, match_heading, match_section_id, snippet = self._score_page(
                page=page, query=query, query_tokens=query_tokens
            )
            if score <= 0:
                continue
            lifecycle_state = page["metadata"].get("lifecycle_state", "unknown")
            effective_lifecycle_state = self._effective_lifecycle_state(
                page, replacement_paths
            )
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
                    "lifecycle_state": lifecycle_state,
                    "effective_lifecycle_state": effective_lifecycle_state,
                    "last_supported_at": page["metadata"].get("last_supported_at"),
                }
            )

        results.sort(key=self._search_sort_key)
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
        replacement_paths = self._replacement_paths_by_knowledge_id(self._load_topics())
        provenance_map = self._load_provenance_map()
        relevant_provenance = self._supporting_provenance_for_section(
            page_metadata=page["metadata"], section_id=section_id
        )
        provenance_entries = [provenance_map[prov_id] for prov_id in relevant_provenance if prov_id in provenance_map]
        source_paths = []
        for entry in provenance_entries:
            source_paths.extend(entry["metadata"].get("source_record_paths", []))
        source_paths = list(dict.fromkeys(source_paths))

        source_manifests = self._load_source_record_manifests(source_paths)
        source_observed_at_by_source = {}
        captured_at_by_source = {}
        render_manifest_paths = []
        render_artifact_paths = []
        render_omissions = []
        for relative_path, manifest in source_manifests.items():
            source_id = manifest.get("source_id")
            if source_id:
                captured_at_by_source[source_id] = manifest.get("captured_at")
                if manifest.get("source_observed_at") is not None:
                    source_observed_at_by_source[source_id] = manifest["source_observed_at"]
            render_manifest_path = manifest.get("render_manifest_relative_path")
            render_path = manifest.get("render_relative_path")
            if render_manifest_path and render_manifest_path not in render_manifest_paths:
                render_manifest_paths.append(render_manifest_path)
            if render_path and render_path not in render_artifact_paths:
                render_artifact_paths.append(render_path)
            if render_manifest_path:
                render_manifest = self._load_render_manifest(render_manifest_path)
                for asset_path in render_manifest.get("asset_relative_paths", []):
                    if asset_path not in render_artifact_paths:
                        render_artifact_paths.append(asset_path)
            omission_reason = manifest.get("render_omission_reason")
            if omission_reason:
                render_omissions.append(
                    {
                        "source_id": manifest.get("source_id"),
                        "source_record": relative_path,
                        "omission_reason": omission_reason,
                    }
                )

        payload = {
            "ref": ref,
            "knowledge_id": page["metadata"]["knowledge_id"],
            "path": self._relative(page["path"]),
            "current_path": page["metadata"]["current_path"],
            "section_id": section_id,
            "authority_posture": page["metadata"].get("authority_posture", "tentative"),
            "lifecycle_state": page["metadata"].get("lifecycle_state", "unknown"),
            "effective_lifecycle_state": self._effective_lifecycle_state(
                page, replacement_paths
            ),
            "last_supported_at": page["metadata"].get("last_supported_at"),
            "replacement_paths": replacement_paths.get(page["metadata"]["knowledge_id"], []),
            "source_observed_at_by_source": source_observed_at_by_source,
            "captured_at_by_source": captured_at_by_source,
            "provenance": [entry["relative_path"] for entry in provenance_entries],
            "source_records": source_paths,
            "render_manifests": render_manifest_paths,
            "render_artifacts": render_artifact_paths,
            "render_omissions": render_omissions,
        }
        if write_receipt:
            self._write_receipt("trace", payload, timestamp=self._timestamp())
        return payload

    def status(
        self,
        *,
        runtime_manifests: Optional[Sequence[Mapping[str, Any]]] = None,
        write_receipt: bool = True,
    ) -> Dict[str, Any]:
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
        rendered_pdf_sources = 0
        limited_fidelity_pdf_sources = 0
        omitted_pdf_sources = 0

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
        replacement_paths = self._replacement_paths_by_knowledge_id(pages)
        last_rebuild = None
        if rebuild_receipts:
            last_rebuild = max(receipt["metadata"]["created_at"] for receipt in rebuild_receipts)

        for manifest in self._load_all_source_record_manifests():
            if manifest.get("source_family") != "pdf":
                continue
            if manifest.get("render_manifest_relative_path"):
                rendered_pdf_sources += 1
                render_manifest = self._load_render_manifest(
                    manifest["render_manifest_relative_path"]
                )
                if render_manifest.get("fidelity_mode") == "limited_fidelity":
                    limited_fidelity_pdf_sources += 1
                continue
            if manifest.get("render_omission_reason"):
                omitted_pdf_sources += 1
                continue

        recent_topics = [
            page["metadata"]["current_path"]
            for page in sorted(
                pages,
                key=lambda item: (
                    -self._timestamp_sort_key(self._page_recentness_timestamp(item["metadata"])),
                    item["metadata"]["current_path"],
                ),
            )[:5]
        ]
        recent_source_ingests = self._recent_source_ingests(save_receipts)
        historical_topic_count = sum(
            1 for page in pages if page["metadata"].get("lifecycle_state") == "historical"
        )
        stale_topic_count = sum(
            1 for page in pages if page["metadata"].get("lifecycle_state") == "stale"
        )
        superseded_topic_count = sum(
            1
            for page in pages
            if self._effective_lifecycle_state(page, replacement_paths) == "superseded"
        )

        payload = {
            "resolved_data_root": str(self.data_root),
            "install_manifest_path": str(self.install_manifest_path),
            "install_manifest_present": self.install_manifest_path.exists(),
            "legacy_repo_graph_detected": bool(
                self.layout.legacy_repo_graph_path
                and self.layout.legacy_repo_graph_path.exists()
            ),
            "pending_source_ingests": 0,
            "pending_rebuild_scope_count": len(set(pending_scopes)),
            "ingests_with_reading_limits": reading_limit_count,
            "approved_helpers_in_use": sorted(approved_helpers),
            "rebuild_pending": sorted(set(pending_scopes)),
            "hot_topics": [topic for topic, _ in topic_counter.most_common(3)],
            "recent_topics": recent_topics,
            "recent_source_ingests": recent_source_ingests,
            "historical_topic_count": historical_topic_count,
            "stale_topic_count": stale_topic_count,
            "superseded_topic_count": superseded_topic_count,
            "unresolved_contradictions": conflict_count,
            "last_rebuild": last_rebuild,
            "topic_count": len(pages),
            "pdf_rendered_sources": rendered_pdf_sources,
            "pdf_limited_fidelity_sources": limited_fidelity_pdf_sources,
            "pdf_render_omitted_sources": omitted_pdf_sources,
            "runtime_agreement": self._runtime_agreement(runtime_manifests or []),
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
                if binding.timestamp is not None:
                    pointer_payload["source_observed_at"] = binding.timestamp
                raw_destination = Path(f"{raw_destination}.pointer.json")
                raw_destination.write_text(json.dumps(pointer_payload, indent=2, sort_keys=True))
            else:
                storage_mode = "copy"
                shutil.copy2(binding.local_path, raw_destination)

            manifest_payload = {
                "source_id": source_id,
                "source_family": family,
                "source_kind": binding.source_kind,
                "authority_tier": binding.authority_tier,
                "sensitivity": binding.sensitivity,
                "storage_mode": storage_mode,
                "relative_path": self._relative(raw_destination),
                "sha256": self._sha256(binding.local_path),
                "captured_at": timestamp,
                "original_path": str(binding.local_path),
            }
            # Keep ingest time and source-observed time separate. They answer different questions.
            if binding.timestamp is not None:
                manifest_payload["source_observed_at"] = binding.timestamp
            if family == "pdf":
                manifest_payload.update(
                    {
                        "render_eligibility": storage_mode == "copy",
                        "render_omission_reason": (
                            self._pdf_render_omission_reason(binding)
                            if storage_mode != "copy"
                            else None
                        ),
                        "render_manifest_relative_path": None,
                        "render_relative_path": None,
                    }
                )
            manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True))
            records[source_id] = {
                "manifest_path": manifest_path,
                "raw_path": raw_destination,
                "relative_path": self._relative(raw_destination),
                "manifest_relative_path": self._relative(manifest_path),
                "binding": binding,
                "source_family": family,
                "storage_mode": storage_mode,
                "sha256": manifest_payload["sha256"],
                "manifest": manifest_payload,
            }
        return records

    def _persist_pdf_render_bundles(
        self,
        *,
        source_records: Mapping[str, Dict[str, Any]],
        timestamp: str,
    ) -> Dict[str, PdfRenderBundle]:
        bundles: Dict[str, PdfRenderBundle] = {}
        for source_id, record in source_records.items():
            if record["source_family"] != "pdf":
                continue

            binding = record["binding"]
            manifest_payload = dict(record["manifest"])
            if record["storage_mode"] != "copy":
                bundle = PdfRenderBundle(
                    source_id=source_id,
                    render_eligible=False,
                    omission_reason=self._pdf_render_omission_reason(binding),
                    source_sha256=record["sha256"],
                )
            else:
                # PDF rendering is the fail-loud boundary before provenance or topic writes.
                bundle = render_pdf_bundle(
                    root=self.data_root,
                    raw_pdf_path=record["raw_path"],
                    source_id=source_id,
                    source_sha256=record["sha256"],
                    timestamp=timestamp,
                )
                if not bundle.render_manifest_relative_path or not bundle.render_relative_path:
                    raise ValidationError(
                        f"eligible PDF render bundle is incomplete for {source_id}"
                    )

            manifest_payload.update(
                {
                    "render_eligibility": bundle.render_eligible,
                    "render_omission_reason": bundle.omission_reason,
                    "render_manifest_relative_path": bundle.render_manifest_relative_path,
                    "render_relative_path": bundle.render_relative_path,
                }
            )
            record["manifest"] = manifest_payload
            record["manifest_path"].write_text(
                json.dumps(manifest_payload, indent=2, sort_keys=True)
            )
            bundles[source_id] = bundle
        return bundles

    def _persist_provenance_notes(
        self,
        *,
        decision: Mapping[str, Any],
        source_records: Mapping[str, Dict[str, Any]],
        pdf_render_bundles: Mapping[str, PdfRenderBundle],
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
            source_observed_at_by_source = {}
            captured_at_by_source = {}
            render_manifest_paths = {}
            render_paths = {}
            render_fidelity_by_source = {}
            render_gaps_by_source = {}
            render_omissions_by_source = {}
            for source_id in note["source_ids"]:
                report = reports_by_source[source_id]
                source_manifest = source_records[source_id]["manifest"]
                reading_modes[source_id] = report["reading_mode"]
                reading_gaps[source_id] = report["gaps"]
                approved_helpers.extend(report["approved_helpers_used"])
                captured_at_by_source[source_id] = source_manifest["captured_at"]
                observed_at = source_manifest.get("source_observed_at")
                if observed_at is not None:
                    source_observed_at_by_source[source_id] = observed_at
                render_bundle = pdf_render_bundles.get(source_id)
                if render_bundle is None:
                    continue
                if render_bundle.render_manifest_relative_path:
                    render_manifest_paths[source_id] = render_bundle.render_manifest_relative_path
                if render_bundle.render_relative_path:
                    render_paths[source_id] = render_bundle.render_relative_path
                if render_bundle.fidelity_mode:
                    render_fidelity_by_source[source_id] = render_bundle.fidelity_mode
                if render_bundle.declared_gaps:
                    render_gaps_by_source[source_id] = list(render_bundle.declared_gaps)
                if render_bundle.omission_reason:
                    render_omissions_by_source[source_id] = render_bundle.omission_reason

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
                "source_observed_at_by_source": source_observed_at_by_source,
                "captured_at_by_source": captured_at_by_source,
                "latest_source_observed_at": self._latest_timestamp(
                    source_observed_at_by_source.values()
                ),
                "knowledge_sections_touched": list(note["knowledge_sections_touched"]),
                "render_manifest_paths": render_manifest_paths,
                "render_paths": render_paths,
                "render_fidelity_by_source": render_fidelity_by_source,
                "render_gaps_by_source": render_gaps_by_source,
                "render_omissions_by_source": render_omissions_by_source,
                "created_at": timestamp,
            }
            body = self._render_provenance_body(
                note,
                {
                    source_id: pdf_render_bundles[source_id]
                    for source_id in note["source_ids"]
                    if source_id in pdf_render_bundles
                },
            )
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
        source_records: Mapping[str, Dict[str, Any]],
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
            section_temporal = dict(metadata.get("section_temporal", {}))
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
                section_temporal[section_id] = {
                    "last_supported_at": self._latest_supported_at(unit["evidence"], source_records),
                    "temporal_scope": unit.get("temporal_scope", "unknown"),
                }
                touched_sections.append(f"{knowledge_id}#{section_id}")
                touched_topics.append(action["topic_path"])

            page_last_supported_at = self._latest_timestamp(
                entry.get("last_supported_at")
                for entry in section_temporal.values()
                if isinstance(entry, dict)
            )
            metadata.update(
                {
                    "knowledge_id": knowledge_id,
                    "current_path": action["topic_path"],
                    "aliases": aliases,
                    "page_kind": action["page_kind"],
                    "parent_topics": self._parent_topics(action["topic_path"]),
                    "section_ids": section_ids,
                    "section_support": section_support,
                    "section_temporal": section_temporal,
                    "authority_posture": merge_authority_postures(authority_values),
                    "last_supported_at": page_last_supported_at,
                    "temporal_scope": self._rollup_temporal_scope(section_temporal.values()),
                    "last_updated_at": timestamp,
                    "last_reorganized_at": metadata.get("last_reorganized_at"),
                    "supersedes": metadata.get("supersedes", []),
                }
            )
            if "lifecycle_state" in action:
                metadata["lifecycle_state"] = action["lifecycle_state"]
            elif "lifecycle_state" not in metadata:
                metadata.pop("lifecycle_state", None)

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
        pdf_render_bundles: Mapping[str, PdfRenderBundle],
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

        saved_render_manifests = [
            bundle.render_manifest_relative_path
            for bundle in pdf_render_bundles.values()
            if bundle.render_manifest_relative_path
        ]
        saved_renders = [
            bundle.render_relative_path
            for bundle in pdf_render_bundles.values()
            if bundle.render_relative_path
        ]
        limited_fidelity_sources = [
            bundle.source_id
            for bundle in pdf_render_bundles.values()
            if bundle.fidelity_mode == "limited_fidelity"
        ]
        render_omitted_sources = [
            {
                "source_id": bundle.source_id,
                "omission_reason": bundle.omission_reason,
            }
            for bundle in pdf_render_bundles.values()
            if bundle.omission_reason
        ]

        metadata = {
            "receipt_id": receipt_id,
            "command": "save",
            "created_at": timestamp,
            "resolved_data_root": str(self.data_root),
            "install_manifest_path": str(self.install_manifest_path),
            "install_manifest_present": self.install_manifest_path.exists(),
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
            "saved_render_manifests": saved_render_manifests,
            "saved_renders": saved_renders,
            "limited_fidelity_sources": limited_fidelity_sources,
            "render_omitted_sources": render_omitted_sources,
            "rebuild_pending_scopes": list(decision["recommended_next_step"]["scope"])
            if decision["recommended_next_step"]["action"] == "queue_rebuild_topic"
            else [],
            "conflicts_or_questions": list(decision["conflicts_or_questions"]),
        }
        body_lines = [
            "# Save Receipt",
            "",
            "## Summary",
            f"- {decision['ingest_summary']['semantic_summary']}",
            "",
        ]
        if saved_render_manifests or render_omitted_sources:
            body_lines.extend(["## Structured Render Results"])
            for render_manifest in saved_render_manifests:
                body_lines.append(f"- `{render_manifest}`")
            for omitted in render_omitted_sources:
                body_lines.append(
                    f"- omitted `{omitted['source_id']}` because `{omitted['omission_reason']}`"
                )
            body_lines.append("")
        body_lines.extend(
            [
                "## Next Step",
                f"- `{decision['recommended_next_step']['action']}`",
                f"- {decision['recommended_next_step']['why']}",
                "",
            ]
        )
        body = "\n".join(body_lines)
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
            "saved_render_manifests": metadata["saved_render_manifests"],
            "saved_renders": metadata["saved_renders"],
            "limited_fidelity_sources": metadata["limited_fidelity_sources"],
            "render_omitted_sources": metadata["render_omitted_sources"],
            "rebuild_pending_scopes": metadata["rebuild_pending_scopes"],
        }

    def _write_receipt(self, kind: str, payload: Mapping[str, Any], timestamp: str) -> None:
        receipt_id = make_opaque_id("receipt")
        path = self.receipts_root / kind / f"{receipt_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {
            "receipt_id": receipt_id,
            "command": kind,
            "created_at": timestamp,
            "resolved_data_root": str(self.data_root),
            "install_manifest_path": str(self.install_manifest_path),
        }
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

        if update.delete_page:
            if update.new_current_path or update.add_supersedes or update.lifecycle_state is not None:
                raise ValidationError(
                    "delete_page update must not also change path, supersedes, or lifecycle_state"
                )
            if metadata.get("lifecycle_state") != "stale":
                raise ValidationError("delete_page is only allowed for already stale pages")
            if page["path"].exists():
                page["path"].unlink()
            return {
                "knowledge_id": update.knowledge_id,
                "old_current_path": old_current_path,
                "new_current_path": None,
                "deleted_page": True,
                "note": update.note,
            }

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
        if update.lifecycle_state is not None:
            metadata["lifecycle_state"] = update.lifecycle_state
        metadata["last_reorganized_at"] = timestamp

        target_path.write_text(dump_frontmatter(metadata, body))
        if target_path != page["path"] and page["path"].exists():
            page["path"].unlink()

        return {
            "knowledge_id": update.knowledge_id,
            "old_current_path": old_current_path,
            "new_current_path": metadata["current_path"],
            "lifecycle_state": metadata.get("lifecycle_state", "unknown"),
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
                -self._timestamp_sort_key(self._page_recentness_timestamp(item["metadata"])),
                item["metadata"]["current_path"],
            ),
        )
        recent_body = "# Recent Changes\n\n"
        for page in recent_sorted[:20]:
            recent_body += (
                f"- `{page['metadata']['current_path']}`"
                f" lifecycle=`{page['metadata'].get('lifecycle_state', 'unknown')}`"
                f" supported=`{page['metadata'].get('last_supported_at')}`"
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

    def _load_all_source_record_manifests(self) -> List[Dict[str, Any]]:
        manifests = []
        if not self.sources_root.exists():
            return manifests
        for path in self.sources_root.rglob("*.record.json"):
            try:
                manifests.append(json.loads(path.read_text()))
            except Exception:
                continue
        return manifests

    def _load_source_record_manifests(
        self,
        relative_paths: Sequence[str],
    ) -> Dict[str, Dict[str, Any]]:
        manifests: Dict[str, Dict[str, Any]] = {}
        for relative_path in relative_paths:
            manifest_path = self.data_root / relative_path
            if not manifest_path.exists():
                continue
            try:
                manifests[relative_path] = json.loads(manifest_path.read_text())
            except Exception:
                continue
        return manifests

    def _load_render_manifest(self, relative_path: str) -> Dict[str, Any]:
        path = self.data_root / relative_path
        return json.loads(path.read_text())

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
        query_lower = query.lower()
        current_path = page["metadata"]["current_path"].lower()
        aliases = " ".join(page["metadata"].get("aliases", [])).lower()
        title = page["title"]
        title_lower = title.lower()
        meaningful_sections = {
            heading: section_lines
            for heading, section_lines in page["sections"].items()
            if heading != "Provenance Notes"
        }
        section_text = " ".join(
            line
            for lines in meaningful_sections.values()
            for line in lines
        ).lower()
        haystack = " ".join([current_path, aliases, title_lower, section_text])
        if query_lower not in haystack and not any(token in haystack for token in query_tokens):
            return 0, None, None, ""

        page_score = 0
        if query_lower in title_lower:
            page_score += 20
        if query_lower in section_text:
            page_score += 12
        if query_lower in aliases:
            page_score += 6
        if query_lower in current_path:
            page_score += 4
        page_score += title_lower.count(query_lower) * 6
        page_score += sum(title_lower.count(token) * 4 for token in query_tokens)
        page_score += sum(section_text.count(token) * 3 for token in query_tokens)
        page_score += sum(aliases.count(token) * 2 for token in query_tokens)
        page_score += sum(current_path.count(token) for token in query_tokens)

        best_heading = None
        best_section_id = None
        best_snippet = title
        best_section_score = -1
        section_ids = page["metadata"].get("section_ids", {})
        for heading, section_lines in meaningful_sections.items():
            section_text = " ".join(section_lines).lower()
            score = sum(section_text.count(token) for token in query_tokens)
            if heading.lower().find(query_lower) != -1:
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

    def _search_sort_key(self, item: Mapping[str, Any]) -> Tuple[int, int, int, int, float, str]:
        effective = item["effective_lifecycle_state"]
        lifecycle = item["lifecycle_state"]
        demotion_bucket = 0 if effective in {"superseded", "stale"} else 1
        lifecycle_rank = {
            "current": 2,
            "unknown": 1,
            "historical": 0,
            "stale": -1,
            "superseded": -2,
        }.get(lifecycle, 1)
        return (
            -demotion_bucket,
            -item["score"],
            -authority_rank(item["authority_posture"]),
            -lifecycle_rank,
            -self._timestamp_sort_key(item.get("last_supported_at")),
            item["current_path"],
        )

    def _effective_lifecycle_state(
        self,
        page: Mapping[str, Any],
        replacement_paths: Mapping[str, List[str]],
    ) -> str:
        stored = page["metadata"].get("lifecycle_state", "unknown")
        if replacement_paths.get(page["metadata"]["knowledge_id"]):
            return "superseded"
        return stored

    def _replacement_paths_by_knowledge_id(
        self,
        pages: Sequence[Mapping[str, Any]],
    ) -> Dict[str, List[str]]:
        page_refs: Dict[str, List[str]] = defaultdict(list)
        for page in pages:
            knowledge_id = page["metadata"]["knowledge_id"]
            refs = {knowledge_id, page["metadata"]["current_path"]}
            refs.update(page["metadata"].get("aliases", []))
            for ref in refs:
                page_refs[ref].append(knowledge_id)

        replacement_paths: Dict[str, set[str]] = defaultdict(set)
        for page in pages:
            if page["metadata"].get("lifecycle_state") == "stale":
                continue
            current_path = page["metadata"]["current_path"]
            for superseded_ref in page["metadata"].get("supersedes", []):
                for knowledge_id in page_refs.get(superseded_ref, []):
                    if knowledge_id != page["metadata"]["knowledge_id"]:
                        replacement_paths[knowledge_id].add(current_path)
        return {
            knowledge_id: sorted(paths)
            for knowledge_id, paths in replacement_paths.items()
        }

    def _page_recentness_timestamp(self, metadata: Mapping[str, Any]) -> Optional[str]:
        candidates = [
            metadata.get("last_reorganized_at"),
            metadata.get("last_updated_at"),
        ]
        return self._latest_timestamp(candidates)

    def _recent_source_ingests(
        self,
        save_receipts: Sequence[Mapping[str, Any]],
    ) -> List[str]:
        ordered_receipts = sorted(
            save_receipts,
            key=lambda item: -self._timestamp_sort_key(item["metadata"].get("created_at")),
        )
        recent_sources: List[str] = []
        for receipt in ordered_receipts:
            for relative_path in receipt["metadata"].get("saved_source_records", []):
                if relative_path not in recent_sources:
                    recent_sources.append(relative_path)
                if len(recent_sources) >= 5:
                    return recent_sources
        return recent_sources

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

    def _render_provenance_body(
        self,
        note: Mapping[str, Any],
        pdf_render_bundles: Mapping[str, PdfRenderBundle],
    ) -> str:
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
        if pdf_render_bundles:
            lines.extend(["## Structured Render Summary"])
            for source_id in note["source_ids"]:
                render_bundle = pdf_render_bundles.get(source_id)
                if render_bundle is None:
                    continue
                if render_bundle.render_manifest_relative_path and render_bundle.render_relative_path:
                    summary = (
                        f"- `{source_id}` -> `{render_bundle.render_relative_path}`"
                        f" (`{render_bundle.fidelity_mode}`)"
                    )
                    if render_bundle.page_count is not None:
                        summary += f", pages={render_bundle.page_count}"
                    lines.append(summary)
                elif render_bundle.omission_reason:
                    lines.append(
                        f"- `{source_id}` -> omitted (`{render_bundle.omission_reason}`)"
                    )
            lines.append("")
        return "\n".join(lines)

    def _latest_supported_at(
        self,
        evidence_entries: Sequence[Mapping[str, Any]],
        source_records: Mapping[str, Dict[str, Any]],
    ) -> Optional[str]:
        observed_times = []
        for evidence in evidence_entries:
            source_id = evidence["source_id"]
            observed_at = source_records[source_id]["manifest"].get("source_observed_at")
            if observed_at:
                observed_times.append(observed_at)
        return self._latest_timestamp(observed_times)

    def _latest_timestamp(self, values: Iterable[Optional[str]]) -> Optional[str]:
        cleaned = [value for value in values if value]
        if not cleaned:
            return None
        return max(cleaned, key=self._timestamp_sort_key)

    def _timestamp_sort_key(self, value: Optional[str]) -> float:
        if not value:
            return 0.0
        rendered = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(rendered).timestamp()
        except ValueError:
            return 0.0

    def _rollup_temporal_scope(
        self,
        temporal_entries: Iterable[Mapping[str, Any]],
    ) -> str:
        scopes = {
            entry.get("temporal_scope", "unknown")
            for entry in temporal_entries
            if isinstance(entry, Mapping)
        }
        scopes.discard(None)
        if not scopes:
            return "unknown"
        if len(scopes) == 1:
            return next(iter(scopes))
        if scopes == {"unknown"}:
            return "unknown"
        return "mixed"

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

    def _pdf_render_omission_reason(self, binding: SourceBinding) -> str:
        if binding.sensitivity == "secret_pointer_only":
            return "disallowed_by_sensitivity"
        if binding.preserve_mode == "pointer":
            return "disallowed_by_storage_mode"
        raise ValidationError(
            f"unable to infer PDF render omission reason for {binding.source_id}"
        )

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.data_root).as_posix()

    def _runtime_agreement(
        self,
        manifests: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        agreement: Dict[str, Dict[str, Any]] = {}
        for manifest in manifests:
            runtime = str(manifest.get("runtime", "unknown"))
            manifest_data_root = manifest.get("data_root")
            manifest_install_manifest_path = manifest.get("install_manifest_path")
            agreement[runtime] = {
                "data_root_match": manifest_data_root == str(self.data_root),
                "install_manifest_path_match": (
                    manifest_install_manifest_path == str(self.install_manifest_path)
                ),
                "target_skill_paths": list(
                    manifest.get("target_skill_paths")
                    or [
                        item
                        for item in [
                            manifest.get("managed_skill_path"),
                            manifest.get("shared_skill_path"),
                        ]
                        if item
                    ]
                ),
                "adapter_mode": manifest.get("adapter_mode"),
            }
        return agreement

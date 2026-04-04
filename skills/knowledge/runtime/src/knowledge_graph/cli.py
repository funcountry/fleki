from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

from .authority import LIFECYCLE_STATES
from .layout import resolve_knowledge_layout
from .models import RebuildPageUpdate, RebuildPlan, SourceBinding
from .repository import KnowledgeRepository
from .validation import (
    SOURCE_FAMILIES,
    ValidationError,
    validate_source_family,
    validate_source_timestamp,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)

        if args.command == "status":
            return _command_status(args)
        if args.command == "search":
            return _command_search(args)
        if args.command == "trace":
            return _command_trace(args)
        if args.command == "save":
            return _command_save(args)
        if args.command == "rebuild":
            return _command_rebuild(args)
    except ValidationError as exc:
        return _emit_error(str(exc))
    except FileNotFoundError as exc:
        return _emit_error(f"file not found: {exc.filename or exc}")
    except json.JSONDecodeError as exc:
        return _emit_error(
            f"invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        )

    parser.error(f"unknown command: {args.command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="knowledge",
        description="Manage the Fleki shared semantic knowledge graph.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show graph status.")
    _add_common_layout_args(status)
    status.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    status.add_argument(
        "--no-receipt",
        action="store_true",
        help="Do not write a status receipt.",
    )

    search = subparsers.add_parser("search", help="Search semantic knowledge pages.")
    _add_common_layout_args(search)
    search.add_argument(
        "query",
        help="Exact ref or literal query for candidate discovery.",
    )
    search.add_argument("--limit", type=int, default=5, help="Maximum number of results.")
    search.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    search.add_argument(
        "--no-receipt",
        action="store_true",
        help="Do not write a search receipt.",
    )

    trace = subparsers.add_parser(
        "trace",
        help="Trace an exact knowledge ref back to sources.",
    )
    _add_common_layout_args(trace)
    trace.add_argument(
        "ref",
        help=(
            "Exact ref: knowledge_id, knowledge_id#section_id, current_path, page alias, "
            "or current_path#section_alias. Section aliases accept deterministic heading normalization."
        ),
    )
    trace.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    trace.add_argument(
        "--no-receipt",
        action="store_true",
        help="Do not write a trace receipt.",
    )

    save = subparsers.add_parser(
        "save",
        help="Apply a save decision from JSON inputs.",
        description="Apply a save decision from JSON inputs.",
        epilog=(
            f'Bindings must include "source_family": {" | ".join(sorted(SOURCE_FAMILIES))}.\n'
            'Bindings must include "timestamp" (ISO 8601 source-observed time).\n'
            "ingest_summary.authority_tier: generated_mirror | historical_support | live_doctrine | mixed | raw_runtime\n"
            "knowledge_units[].authority_posture: live_doctrine | mixed | supported_by_internal_session | supported_by_runtime | tentative\n"
            "knowledge_units[].kind: fact | principle | playbook | decision | pattern | regression | glossary | question\n"
            "knowledge_units[].temporal_scope: evergreen | time_bound | ephemeral\n"
            "topic_actions[].lifecycle_state: current | historical\n"
            "Rebuild owns stale transitions and delete.\n"
            "Topic paths must be semantic, not source-family-first.\n"
            "See the bundled runtime README.md for a valid save example, naming crosswalk, and persistent-root notes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_common_layout_args(save)
    save.add_argument(
        "--bindings",
        required=True,
        help="Path to a JSON file containing a list of source-binding objects.",
    )
    save.add_argument(
        "--decision",
        required=True,
        help="Path to a JSON file containing the save decision payload.",
    )
    save.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    rebuild = subparsers.add_parser("rebuild", help="Apply a rebuild plan from JSON.")
    _add_common_layout_args(rebuild)
    rebuild.add_argument(
        "--plan",
        required=True,
        help="Path to a JSON file containing the rebuild plan payload.",
    )
    rebuild.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def _add_common_layout_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-root", help="Explicit canonical data root.")
    parser.add_argument("--config-root", help="Explicit config root.")
    parser.add_argument("--state-root", help="Explicit state root.")
    parser.add_argument("--install-manifest-path", help="Explicit install manifest path.")
    parser.add_argument("--repo-root", help="Optional Fleki repo root for legacy graph detection.")


def _command_status(args: argparse.Namespace) -> int:
    repo = _build_repo(args)
    result = repo.status(write_receipt=not args.no_receipt)
    _emit_payload(
        result,
        as_json=args.json,
        lines=(
            f"resolved_data_root={result['resolved_data_root']}",
            f"install_manifest_path={result['install_manifest_path']}",
            f"topic_count={result['topic_count']}",
            f"recent_topics={','.join(result['recent_topics']) or 'none'}",
            f"recent_source_ingests={','.join(result['recent_source_ingests']) or 'none'}",
            f"historical_topic_count={result['historical_topic_count']}",
            f"stale_topic_count={result['stale_topic_count']}",
            f"superseded_topic_count={result['superseded_topic_count']}",
            f"missing_lifecycle_state_count={result['missing_lifecycle_state_count']}",
            f"ingests_with_confidence_caveats={result['ingests_with_confidence_caveats']}",
            f"pdf_render_contract_gap_count={result['pdf_render_contract_gap_count']}",
        ),
    )
    return 0


def _command_search(args: argparse.Namespace) -> int:
    repo = _build_repo(args)
    result = repo.search(args.query, limit=args.limit, write_receipt=not args.no_receipt)
    if args.json:
        _emit_payload(result, as_json=True, lines=())
        return 0
    if not result["results"]:
        print("no_results")
        return 0
    lines = []
    for item in result["results"]:
        lines.append(
            f"{item['current_path']} match_kind={item['match_kind']} "
            f"authority={item['authority_posture']} "
            f"lifecycle={item['lifecycle_state']} effective={item['effective_lifecycle_state']} "
            f"last_supported_at={item['last_supported_at']} trace_ref={item['trace_ref']}"
        )
    _emit_payload(result, as_json=False, lines=lines)
    return 0


def _command_trace(args: argparse.Namespace) -> int:
    repo = _build_repo(args)
    result = repo.trace(args.ref, write_receipt=not args.no_receipt)
    if args.json:
        _emit_payload(result, as_json=True, lines=())
        return 0
    lines = [
        f"current_path={result['current_path']}",
        f"matched_heading={result['matched_heading'] or 'none'}",
        f"matched_snippet={result['matched_snippet'] or 'none'}",
        f"matched_evidence_locators={','.join(result['matched_evidence_locators']) or 'none'}",
        "supported_sections="
        + (
            ",".join(
                f"{item['trace_ref']}:{item['heading']}"
                for item in result["supported_sections"]
            )
            or "none"
        ),
        f"authority_posture={result['authority_posture']}",
        f"lifecycle_state={result['lifecycle_state']}",
        f"effective_lifecycle_state={result['effective_lifecycle_state']}",
        f"last_supported_at={result['last_supported_at']}",
        f"provenance_count={len(result['provenance'])}",
        f"source_record_count={len(result['source_records'])}",
        f"render_contract_gap_count={len(result['render_contract_gaps'])}",
    ]
    _emit_payload(result, as_json=False, lines=lines)
    return 0


def _command_save(args: argparse.Namespace) -> int:
    repo = _build_repo(args)
    bindings = _load_bindings(args.bindings)
    decision = _load_json(args.decision)
    if not isinstance(decision, dict):
        raise SystemExit("--decision must point to a JSON object")
    result = repo.apply_save(source_bindings=bindings, decision=decision)
    if args.json:
        _emit_payload(result, as_json=True, lines=())
    else:
        _emit_payload(
            result,
            as_json=False,
            lines=(
                f"result={result['result']}",
                f"receipt_path={result['receipt_path']}",
                f"saved_sources={len(result['saved_sources'])}",
                f"provenance_notes={len(result['provenance_notes'])}",
            ),
        )
    return 0


def _command_rebuild(args: argparse.Namespace) -> int:
    repo = _build_repo(args)
    plan_payload = _load_json(args.plan)
    if not isinstance(plan_payload, dict):
        raise SystemExit("--plan must point to a JSON object")
    plan = _rebuild_plan_from_dict(plan_payload)
    result = repo.apply_rebuild(plan)
    if args.json:
        _emit_payload(result, as_json=True, lines=())
    else:
        _emit_payload(
            result,
            as_json=False,
            lines=(
                f"cleared_scopes={','.join(result['cleared_scopes'])}",
                f"changes={len(result['changes'])}",
                f"open_questions={len(result['open_questions'])}",
            ),
        )
    return 0


def _build_repo(args: argparse.Namespace) -> KnowledgeRepository:
    layout = resolve_knowledge_layout(
        data_root=_optional_path(args.data_root),
        config_root=_optional_path(args.config_root),
        state_root=_optional_path(args.state_root),
        install_manifest_path=_optional_path(args.install_manifest_path),
        repo_root=_optional_path(args.repo_root),
    )
    return KnowledgeRepository(layout)


def _binding_from_dict(payload: Any) -> SourceBinding:
    if not isinstance(payload, dict):
        raise SystemExit("each source binding must be a JSON object")
    if "preserve_mode" in payload:
        raise ValidationError(
            "source binding must not include preserve_mode; storage policy is owned by Fleki"
        )
    missing = [
        key
        for key in ["source_id", "local_path", "source_kind", "source_family", "timestamp"]
        if key not in payload
    ]
    if missing:
        raise ValidationError(
            f"source binding missing required keys: {', '.join(missing)}"
        )
    return SourceBinding(
        source_id=str(payload["source_id"]),
        local_path=Path(payload["local_path"]),
        source_kind=str(payload["source_kind"]),
        source_family=validate_source_family(
            payload.get("source_family"),
            field_name="source_binding.source_family",
        ),
        authority_tier=str(payload.get("authority_tier", "historical_support")),
        sensitivity=str(payload.get("sensitivity", "internal")),
        timestamp=validate_source_timestamp(
            payload.get("timestamp"),
            field_name="source_binding.timestamp",
        ),
        notes=_optional_string(payload.get("notes")),
    )


def _rebuild_plan_from_dict(payload: dict[str, Any]) -> RebuildPlan:
    page_updates = []
    for update in payload.get("page_updates", []):
        if not isinstance(update, dict):
            raise SystemExit("each rebuild page update must be a JSON object")
        page_updates.append(
            RebuildPageUpdate(
                knowledge_id=str(update["knowledge_id"]),
                new_current_path=_optional_string(update.get("new_current_path")),
                add_supersedes=tuple(str(item) for item in update.get("add_supersedes", [])),
                lifecycle_state=_optional_lifecycle_state(update.get("lifecycle_state")),
                delete_page=bool(update.get("delete_page", False)),
                note=_optional_string(update.get("note")),
            )
        )
    return RebuildPlan(
        scope=tuple(str(item) for item in payload.get("scope", [])),
        page_updates=tuple(page_updates),
        open_questions=tuple(str(item) for item in payload.get("open_questions", [])),
        refresh_indexes=bool(payload.get("refresh_indexes", True)),
    )


def _optional_path(value: str | None) -> Path | None:
    if value in {None, ""}:
        return None
    return Path(value)


def _optional_string(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    return str(value)


def _optional_lifecycle_state(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    rendered = str(value)
    if rendered not in LIFECYCLE_STATES:
        raise SystemExit(
            "rebuild page update lifecycle_state must be one of: current, historical, stale"
        )
    return rendered


def _load_bindings(path_text: str) -> tuple[SourceBinding, ...]:
    bindings_payload = _load_json(path_text)
    if not isinstance(bindings_payload, list):
        raise SystemExit("--bindings must point to a JSON list")
    return tuple(_binding_from_dict(item) for item in bindings_payload)


def _load_json(path_text: str) -> Any:
    return json.loads(Path(path_text).read_text())


def _emit_payload(payload: dict[str, Any], *, as_json: bool, lines: Iterable[str]) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for line in lines:
        print(line)


def _emit_error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

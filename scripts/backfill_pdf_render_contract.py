#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from knowledge_graph.layout import resolve_knowledge_layout  # noqa: E402
from knowledge_graph.pdf_render import render_pdf_bundle  # noqa: E402
from knowledge_graph.repository import KnowledgeRepository  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="backfill_pdf_render_contract",
        description="Repair legacy PDF source records that predate the render-or-omission contract.",
    )
    parser.add_argument("--data-root", help="Explicit canonical data root.")
    parser.add_argument("--config-root", help="Explicit config root.")
    parser.add_argument("--state-root", help="Explicit state root.")
    parser.add_argument("--install-manifest-path", help="Explicit install manifest path.")
    parser.add_argument("--repo-root", help="Optional Fleki repo root for legacy graph detection.")
    parser.add_argument(
        "--source-record",
        action="append",
        default=[],
        help="Optional relative source-record path to repair. Repeat to target multiple records.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    layout = resolve_knowledge_layout(
        data_root=_optional_path(args.data_root),
        config_root=_optional_path(args.config_root),
        state_root=_optional_path(args.state_root),
        install_manifest_path=_optional_path(args.install_manifest_path),
        repo_root=_optional_path(args.repo_root),
    )
    repo = KnowledgeRepository(layout)
    payload = backfill_pdf_render_contract(
        repo,
        selected_source_records=tuple(args.source_record),
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"resolved_data_root={payload['resolved_data_root']}")
        print(f"updated_source_records={len(payload['updated_source_records'])}")
        print(f"errors={len(payload['errors'])}")
    return 0 if not payload["errors"] else 1


def backfill_pdf_render_contract(
    repo: KnowledgeRepository,
    *,
    selected_source_records: Sequence[str] = (),
) -> dict[str, object]:
    selected = set(selected_source_records)
    timestamp = repo._timestamp()
    updated_source_records: list[str] = []
    rendered_sources: list[dict[str, str]] = []
    omitted_sources: list[dict[str, str]] = []
    skipped_source_records: list[str] = []
    errors: list[dict[str, str]] = []

    entries = repo._load_all_source_record_manifest_entries()
    seen_selected: set[str] = set()
    for entry in entries:
        relative_path = entry["relative_path"]
        manifest = dict(entry["manifest"])
        if selected and relative_path not in selected:
            continue
        if selected:
            seen_selected.add(relative_path)
        if repo._manifest_source_family(manifest) != "pdf":
            skipped_source_records.append(relative_path)
            continue
        gap_reason = repo._render_contract_gap_reason(manifest)
        if gap_reason is None:
            skipped_source_records.append(relative_path)
            continue

        manifest_path = entry["path"]
        try:
            if manifest.get("storage_mode") == "copy":
                raw_relative_path = manifest.get("relative_path")
                raw_path = repo.data_root / str(raw_relative_path)
                if not raw_path.exists():
                    raise FileNotFoundError(f"raw PDF is missing: {raw_relative_path}")
                bundle = render_pdf_bundle(
                    root=repo.data_root,
                    raw_pdf_path=raw_path,
                    source_id=str(manifest.get("source_id")),
                    source_sha256=str(manifest.get("sha256")),
                    timestamp=timestamp,
                )
                manifest.update(
                    {
                        "render_eligibility": bundle.render_eligible,
                        "render_omission_reason": bundle.omission_reason,
                        "render_manifest_relative_path": bundle.render_manifest_relative_path,
                        "render_relative_path": bundle.render_relative_path,
                    }
                )
                rendered_sources.append(
                    {
                        "source_id": str(manifest.get("source_id")),
                        "source_record": relative_path,
                        "render_manifest_path": str(bundle.render_manifest_relative_path),
                        "render_markdown_path": str(bundle.render_relative_path),
                    }
                )
            else:
                omission_reason = repo._pdf_render_omission_reason_from_manifest(manifest)
                manifest.update(
                    {
                        "render_eligibility": False,
                        "render_omission_reason": omission_reason,
                        "render_manifest_relative_path": None,
                        "render_relative_path": None,
                    }
                )
                omitted_sources.append(
                    {
                        "source_id": str(manifest.get("source_id")),
                        "source_record": relative_path,
                        "omission_reason": omission_reason,
                    }
                )
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
            updated_source_records.append(relative_path)
        except Exception as exc:  # fail loud and preserve the original manifest on error
            errors.append(
                {
                    "source_record": relative_path,
                    "gap_reason": str(gap_reason),
                    "error": str(exc),
                }
            )

    missing_requested_records = sorted(selected - seen_selected)
    for relative_path in missing_requested_records:
        errors.append(
            {
                "source_record": relative_path,
                "gap_reason": "requested_record_not_found",
                "error": "requested source record was not found under sources/**",
            }
        )

    return {
        "result": "repaired" if not errors else "failed",
        "resolved_data_root": str(repo.data_root),
        "updated_source_records": updated_source_records,
        "rendered_sources": rendered_sources,
        "omitted_sources": omitted_sources,
        "skipped_source_records": skipped_source_records,
        "errors": errors,
    }


def _optional_path(value: str | None) -> Path | None:
    if value in {None, ""}:
        return None
    return Path(value)


if __name__ == "__main__":
    raise SystemExit(main())

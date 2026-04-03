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
from knowledge_graph.repository import KnowledgeRepository  # noqa: E402
from knowledge_graph.validation import ValidationError, validate_source_family  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="backfill_source_family",
        description="Repair legacy source records that are missing explicit source_family.",
    )
    parser.add_argument("--data-root", help="Explicit canonical data root.")
    parser.add_argument("--config-root", help="Explicit config root.")
    parser.add_argument("--state-root", help="Explicit state root.")
    parser.add_argument("--install-manifest-path", help="Explicit install manifest path.")
    parser.add_argument("--repo-root", help="Optional Fleki repo root for legacy graph detection.")
    parser.add_argument(
        "--source-record",
        action="append",
        required=True,
        help="Relative source-record path to repair. Repeat to target multiple records.",
    )
    parser.add_argument(
        "--source-family",
        required=True,
        help="Explicit family to write to each selected source record.",
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
    payload = backfill_source_family(
        repo,
        selected_source_records=tuple(args.source_record),
        source_family=args.source_family,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"resolved_data_root={payload['resolved_data_root']}")
        print(f"updated_source_records={len(payload['updated_source_records'])}")
        print(f"skipped_source_records={len(payload['skipped_source_records'])}")
        print(f"errors={len(payload['errors'])}")
    return 0 if not payload["errors"] else 1


def backfill_source_family(
    repo: KnowledgeRepository,
    *,
    selected_source_records: Sequence[str],
    source_family: str,
) -> dict[str, object]:
    family = validate_source_family(
        source_family,
        field_name="source_family",
    )
    entries_by_path = {
        entry["relative_path"]: entry
        for entry in repo._load_all_source_record_manifest_entries()
    }
    updated_source_records: list[str] = []
    skipped_source_records: list[str] = []
    errors: list[dict[str, str]] = []

    for relative_path in selected_source_records:
        entry = entries_by_path.get(relative_path)
        if entry is None:
            errors.append(
                {
                    "source_record": relative_path,
                    "error": "requested source record was not found under sources/**",
                }
            )
            continue

        manifest = dict(entry["manifest"])
        try:
            _validate_relative_path_family(relative_path, manifest, family)
            stored_family = manifest.get("source_family")
            if stored_family == family:
                skipped_source_records.append(relative_path)
                continue
            if stored_family not in {None, ""}:
                raise ValidationError(
                    f"source record already declares source_family={stored_family!r}"
                )
            manifest["source_family"] = family
            entry["path"].write_text(json.dumps(manifest, indent=2, sort_keys=True))
            updated_source_records.append(relative_path)
        except Exception as exc:
            errors.append(
                {
                    "source_record": relative_path,
                    "error": str(exc),
                }
            )

    return {
        "result": "repaired" if not errors else "failed",
        "resolved_data_root": str(repo.data_root),
        "updated_source_records": updated_source_records,
        "skipped_source_records": skipped_source_records,
        "errors": errors,
    }


def _validate_relative_path_family(
    relative_path: str,
    manifest: dict[str, object],
    source_family: str,
) -> None:
    stored_relative_path = str(manifest.get("relative_path", ""))
    expected_prefix = f"sources/{source_family}/"
    if not relative_path.startswith(expected_prefix):
        raise ValidationError(
            f"source record path {relative_path!r} does not live under {expected_prefix!r}"
        )
    if not stored_relative_path.startswith(expected_prefix):
        raise ValidationError(
            f"manifest relative_path {stored_relative_path!r} does not live under {expected_prefix!r}"
        )


def _optional_path(value: str | None) -> Path | None:
    if value in {None, ""}:
        return None
    return Path(value)


if __name__ == "__main__":
    raise SystemExit(main())

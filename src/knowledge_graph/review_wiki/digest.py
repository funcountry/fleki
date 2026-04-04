from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .exporter import ExportSnapshot


def calculate_export_digest(snapshot: ExportSnapshot) -> str:
    hasher = hashlib.sha256()
    for export_file in snapshot.files:
        hasher.update(export_file.relative_path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(export_file.content)
        hasher.update(b"\0")
    return hasher.hexdigest()


def load_saved_export_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    digest = payload.get("digest")
    if not isinstance(digest, str) or not digest:
        return None
    return digest


def write_saved_export_digest(path: Path, digest: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"digest": digest}, indent=2, sort_keys=True) + "\n")

from __future__ import annotations

import base64
import os
import re
import time

_NON_PATH_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def make_opaque_id(prefix: str) -> str:
    timestamp_bytes = int(time.time() * 1000).to_bytes(6, "big", signed=False)
    raw = timestamp_bytes + os.urandom(10)
    encoded = base64.b32encode(raw).decode("ascii").rstrip("=").lower()
    return f"{prefix}_{encoded}"


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = _NON_SLUG.sub("-", lowered).strip("-")
    return slug or "untitled"


def section_key(heading: str) -> str:
    return slugify(heading).replace("-", "_")


def safe_filename(value: str) -> str:
    return _NON_PATH_SAFE.sub("_", value).strip("._") or "item"

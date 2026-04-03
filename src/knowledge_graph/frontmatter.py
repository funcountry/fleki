from __future__ import annotations

import json
from typing import Any, Dict, Tuple


def dump_frontmatter(metadata: Dict[str, Any], body: str) -> str:
    rendered = json.dumps(metadata, indent=2, sort_keys=True)
    return f"---\n{rendered}\n---\n{body.lstrip()}"


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter start")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing frontmatter end")
    raw = text[4:end]
    metadata = json.loads(raw)
    body = text[end + 5 :]
    return metadata, body

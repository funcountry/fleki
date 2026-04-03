from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Dict, Tuple

import yaml


class _FrontmatterLoader(yaml.SafeLoader):
    pass


_FrontmatterLoader.yaml_implicit_resolvers = deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for key, resolvers in list(_FrontmatterLoader.yaml_implicit_resolvers.items()):
    _FrontmatterLoader.yaml_implicit_resolvers[key] = [
        (tag, pattern) for tag, pattern in resolvers if tag != "tag:yaml.org,2002:timestamp"
    ]


def _extract_frontmatter(text: str) -> Tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter start")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing frontmatter end")
    return text[4:end], text[end + 5 :]


def _load_yaml_metadata(raw: str) -> Dict[str, Any]:
    metadata = yaml.load(raw, Loader=_FrontmatterLoader) if raw.strip() else {}
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata


def dump_frontmatter(metadata: Dict[str, Any], body: str) -> str:
    rendered = yaml.safe_dump(metadata, sort_keys=True, default_flow_style=False).strip()
    return f"---\n{rendered}\n---\n{body.lstrip()}"


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    raw, body = _extract_frontmatter(text)
    if raw.lstrip().startswith("{"):
        raise ValueError("legacy JSON frontmatter is not supported")
    return _load_yaml_metadata(raw), body


def split_frontmatter_for_migration(text: str) -> Tuple[Dict[str, Any], str]:
    raw, body = _extract_frontmatter(text)
    if raw.lstrip().startswith("{"):
        metadata = json.loads(raw)
        if not isinstance(metadata, dict):
            raise ValueError("frontmatter must be a mapping")
        return metadata, body
    return _load_yaml_metadata(raw), body


def uses_legacy_json_frontmatter(text: str) -> bool:
    raw, _ = _extract_frontmatter(text)
    return raw.lstrip().startswith("{")

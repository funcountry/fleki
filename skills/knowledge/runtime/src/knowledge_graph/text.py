from __future__ import annotations

import re
from collections import OrderedDict
from typing import Iterable, List, MutableMapping, OrderedDict as OrderedDictType, Tuple

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(value: str) -> List[str]:
    return TOKEN_RE.findall(value.lower())


def parse_sections(body: str) -> Tuple[str, OrderedDictType[str, List[str]]]:
    title = "Untitled"
    sections: OrderedDictType[str, List[str]] = OrderedDict()
    current_heading = None
    current_lines: List[str] = []

    def flush() -> None:
        nonlocal current_heading, current_lines
        if current_heading is not None:
            sections[current_heading] = current_lines[:]
        current_heading = None
        current_lines = []

    for raw_line in body.splitlines():
        if raw_line.startswith("# "):
            title = raw_line[2:].strip() or title
            continue
        if raw_line.startswith("## "):
            flush()
            current_heading = raw_line[3:].strip()
            current_lines = []
            continue
        if current_heading is not None:
            current_lines.append(raw_line)

    flush()
    return title, sections


def ensure_bullet(section_lines: MutableMapping[str, List[str]], heading: str, statement: str) -> None:
    lines = section_lines.setdefault(heading, [])
    bullet = f"- {statement}"
    if bullet not in lines:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(bullet)


def render_page(title: str, sections: OrderedDictType[str, List[str]], provenance_refs: Iterable[str]) -> str:
    # Semantic topic pages stay meaning-first; PDF fidelity lives in source-adjacent render bundles.
    lines: List[str] = [f"# {title}", ""]
    for heading, section_lines in sections.items():
        lines.append(f"## {heading}")
        if section_lines:
            lines.extend(section_lines)
        else:
            lines.append("- Pending content")
        lines.append("")

    provenance_list = sorted(set(provenance_refs))
    if provenance_list:
        lines.append("## Provenance Notes")
        for ref in provenance_list:
            lines.append(f"- `{ref}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

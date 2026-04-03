from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import ResolvedKnowledgeLayout


REVIEW_WIKI_HOST = "127.0.0.1"
REVIEW_WIKI_PORT = 4151
REVIEW_WIKI_POLL_SECONDS = 5
QUARTZ_REQUIRED_NODE_MAJOR = 22
QUARTZ_NPM_MIN_VERSION = "10.9.2"
QUARTZ_VERSION = "4.5.2"
QUARTZ_PACKAGE_REFERENCE = (
    f"https://codeload.github.com/jackyzha0/quartz/tar.gz/refs/tags/v{QUARTZ_VERSION}"
)


@dataclass(frozen=True)
class ReviewWikiLayout:
    root: Path
    quartz_root: Path
    content_root: Path
    public_root: Path
    export_digest_path: Path
    build_log_path: Path


def resolve_review_wiki_layout(layout: ResolvedKnowledgeLayout) -> ReviewWikiLayout:
    root = layout.state_root / "review-wiki"
    quartz_root = root / "quartz"
    return ReviewWikiLayout(
        root=root,
        quartz_root=quartz_root,
        content_root=quartz_root / "content",
        public_root=quartz_root / "public",
        export_digest_path=root / "export-digest.json",
        build_log_path=root / "build.log",
    )

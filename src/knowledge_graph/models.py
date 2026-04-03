from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple


@dataclass(frozen=True)
class SourceBinding:
    source_id: str
    local_path: Path
    source_kind: str
    authority_tier: str = "historical_support"
    sensitivity: str = "internal"
    preserve_mode: str = "copy"
    timestamp: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "local_path", Path(self.local_path))


@dataclass(frozen=True)
class RebuildPageUpdate:
    knowledge_id: str
    new_current_path: Optional[str] = None
    add_supersedes: Tuple[str, ...] = field(default_factory=tuple)
    note: Optional[str] = None


@dataclass(frozen=True)
class RebuildPlan:
    scope: Tuple[str, ...]
    page_updates: Tuple[RebuildPageUpdate, ...] = field(default_factory=tuple)
    open_questions: Tuple[str, ...] = field(default_factory=tuple)
    refresh_indexes: bool = True

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NoteNormalizationResult:
    """AI may only return note-related fields — never commercial quantities/prices."""

    summary: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    source: str = "mock"  # mock | codex | fallback

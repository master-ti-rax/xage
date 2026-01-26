from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional


class GitToolbox:
    def __init__(self, default_author: str = "Xage Bot") -> None:
        self.default_author = default_author

    def build_commit_message(
        self,
        commit_type: str,
        summary: str,
        bullet_points: Optional[Iterable[str]] = None,
    ) -> str:
        header = f"{commit_type}: {summary}".strip()
        body = ""
        if bullet_points:
            body = "\n".join(str(point) for point in bullet_points)
        return f"{header}\n\n{body}".strip()

    def summarize_changes(self, changes: Iterable[dict]) -> str:
        entries = list(changes)
        if not entries:
            return "No changes detected."
        lines = [
            f"{entry.get('path')}: +{entry.get('added', 0)} -{entry.get('removed', 0)}"
            for entry in entries
        ]
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        return f"Summary at {timestamp} UTC\n" + "\n".join(lines)

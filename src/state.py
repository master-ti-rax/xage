from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AssetRecord:
    name: str
    type: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionState:
    goal: str = ""
    plan: List[str] = field(default_factory=list)
    assets: Dict[str, AssetRecord] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def record_event(self, message: str) -> None:
        self.history.append(message)

    def add_asset(self, record: AssetRecord) -> None:
        self.assets[record.name] = record
        self.record_event(f"Asset registered: {record.name} ({record.type})")

    def set_plan(self, plan: List[str]) -> None:
        self.plan = plan
        self.record_event(f"Plan updated: {len(plan)} step(s)")

    def complete_step(self, step: str, success: bool = True, detail: str = "") -> None:
        status = "success" if success else "failed"
        message = f"Step '{step}' {status}"
        if detail:
            message += f" - {detail}"
        self.record_event(message)
        if not success:
            self.errors.append(message)

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .persistence import JsonStore
from .types import Assumption


class AssumptionsRepository:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()

    def add(self, payload: dict[str, Any]) -> Assumption:
        data = self.store.load()
        assumption_id = payload.get("assumption_id") or f"asm-{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        assumption = Assumption(
            assumption_id=assumption_id,
            title=payload["title"],
            description=payload["description"],
            source_type=payload["source_type"],
            confidence=payload["confidence"],
            evidence_refs=payload.get("evidence_refs", []),
            limitations=payload.get("limitations", []),
            created_at=now,
            updated_at=now,
        )
        data["assumptions"][assumption.assumption_id] = asdict(assumption)
        self.store.save(data)
        return assumption

    def list(self) -> list[Assumption]:
        data = self.store.load()
        assumptions = [Assumption(**item) for item in data["assumptions"].values()]
        return sorted(assumptions, key=lambda x: x.assumption_id)

    def update(self, assumption_id: str, updates: dict[str, Any]) -> Assumption:
        data = self.store.load()
        current = data["assumptions"].get(assumption_id)
        if current is None:
            raise KeyError(f"Assumption not found: {assumption_id}")
        merged = {**current, **updates, "assumption_id": assumption_id, "updated_at": datetime.now(timezone.utc).isoformat()}
        assumption = Assumption(**merged)
        data["assumptions"][assumption_id] = asdict(assumption)
        self.store.save(data)
        return assumption

    def delete(self, assumption_id: str) -> bool:
        data = self.store.load()
        existed = assumption_id in data["assumptions"]
        if existed:
            del data["assumptions"][assumption_id]
            self.store.save(data)
        return existed

    def export(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.list()]

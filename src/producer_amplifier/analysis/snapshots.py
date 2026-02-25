from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .persistence import JsonStore
from .types import AnalysisSnapshot, Assumption, Recommendation, RiskFlag


class SnapshotsRepository:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()

    def create_snapshot(
        self,
        project_id: str,
        risk_flags: list[RiskFlag],
        recommendations: list[Recommendation],
        summary_metrics: dict[str, Any],
        assumptions: list[Assumption],
        inputs_metadata: dict[str, Any] | None = None,
        parser_version: str = "v2",
        scoring_version: str = "v2",
        source_files: list[str] | None = None,
    ) -> str:
        data = self.store.load()
        snapshot_id = f"snp-{uuid4().hex[:12]}"
        snapshot = AnalysisSnapshot(
            snapshot_id=snapshot_id,
            project_id=project_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            parser_version=parser_version,
            scoring_version=scoring_version,
            source_files=sorted(source_files or []),
            assumptions=sorted(assumptions, key=lambda a: a.assumption_id),
            risk_flags=sorted(risk_flags, key=lambda r: r.risk_id),
            recommendations=sorted(recommendations, key=lambda r: r.recommendation_id),
            summary_metrics=summary_metrics,
            inputs_metadata=inputs_metadata or {},
        )
        data["snapshots"][snapshot_id] = asdict(snapshot)
        data["snapshot_index_by_project"].setdefault(project_id, []).append(snapshot_id)
        data["snapshot_index_by_project"][project_id] = sorted(data["snapshot_index_by_project"][project_id])
        self.store.save(data)
        return snapshot_id

    def list_snapshots(self, project_id: str) -> list[dict[str, Any]]:
        data = self.store.load()
        ids = sorted(data["snapshot_index_by_project"].get(project_id, []))
        return [
            {
                "snapshot_id": snapshot_id,
                "project_id": project_id,
                "created_at": data["snapshots"][snapshot_id]["created_at"],
            }
            for snapshot_id in ids
            if snapshot_id in data["snapshots"]
        ]

    def load_snapshot(self, snapshot_id: str) -> AnalysisSnapshot:
        data = self.store.load()
        item = data["snapshots"].get(snapshot_id)
        if item is None:
            raise KeyError(f"Snapshot not found: {snapshot_id}")
        return AnalysisSnapshot(
            snapshot_id=item["snapshot_id"],
            project_id=item["project_id"],
            created_at=item["created_at"],
            parser_version=item["parser_version"],
            scoring_version=item["scoring_version"],
            source_files=item["source_files"],
            assumptions=[Assumption(**a) for a in item["assumptions"]],
            risk_flags=[RiskFlag(**r) for r in item["risk_flags"]],
            recommendations=[Recommendation(**r) for r in item["recommendations"]],
            summary_metrics=item["summary_metrics"],
            inputs_metadata=item.get("inputs_metadata", {}),
        )

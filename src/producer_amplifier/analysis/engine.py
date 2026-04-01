from __future__ import annotations

from .rules import (
    cast_concentration_alerts,
    hidden_cost_flags,
    location_clustering_opportunities,
    night_shoot_concentration_alerts,
    overtime_risk_indicators,
)
from .scoring import scene_complexity_score, vfx_risk_score
from .types import Project, Recommendation, RiskFlag


def analyze_project(project: Project) -> tuple[list[RiskFlag], list[Recommendation], dict]:
    risk_flags: list[RiskFlag] = []
    recommendations: list[Recommendation] = []

    risk_flags.extend(hidden_cost_flags(project))
    risk_flags.extend(overtime_risk_indicators(project))
    risk_flags.extend(cast_concentration_alerts(project))
    risk_flags.extend(night_shoot_concentration_alerts(project))
    recommendations.extend(location_clustering_opportunities(project))

    complexity_scores = [scene_complexity_score(scene)["score"] for scene in project.scenes]
    vfx_scores = [vfx_risk_score(scene)["score"] for scene in project.scenes]
    summary = {
        "scene_count": len(project.scenes),
        "risk_count": len(risk_flags),
        "recommendation_count": len(recommendations),
        "avg_scene_complexity": round(sum(complexity_scores) / len(complexity_scores), 2) if complexity_scores else 0,
        "avg_vfx_risk": round(sum(vfx_scores) / len(vfx_scores), 2) if vfx_scores else 0,
    }
    return sorted(risk_flags, key=lambda r: r.risk_id), sorted(recommendations, key=lambda r: r.recommendation_id), summary

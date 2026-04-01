from __future__ import annotations

from collections import Counter, defaultdict

from .constants import HIDDEN_COST_KEYWORDS, AnalysisWeights
from .types import Project, Recommendation, RiskFlag


def _severity_from_ratio(ratio: float) -> str:
    if ratio >= 0.7:
        return "high"
    if ratio >= 0.4:
        return "med"
    return "low"


def hidden_cost_flags(project: Project, weights: AnalysisWeights | None = None) -> list[RiskFlag]:
    weights = weights or AnalysisWeights()
    flags: list[RiskFlag] = []

    for idx, item in enumerate(project.budget_items, start=1):
        keyword_hit = any(token in item.account_name.lower() for token in HIDDEN_COST_KEYWORDS)
        threshold_hit = item.total >= weights.hidden_cost_threshold
        if keyword_hit or threshold_hit:
            severity = "high" if threshold_hit else "med"
            flags.append(
                RiskFlag(
                    risk_id=f"hidden-cost-{idx}",
                    category="hidden_cost",
                    severity=severity,
                    confidence=0.85,
                    rationale="Line item appears likely to conceal variable or insufficiently scoped costs.",
                    evidence_refs=[
                        f"budget:{item.account_code}",
                        f"account:{item.account_name}",
                        f"total:{item.total}",
                    ],
                    assumptions_used=["rule:hidden_cost_keyword_or_threshold"],
                    is_heuristic=False,
                )
            )
    return flags


def overtime_risk_indicators(project: Project, weights: AnalysisWeights | None = None) -> list[RiskFlag]:
    weights = weights or AnalysisWeights()
    heavy_scenes = [scene for scene in project.scenes if len(scene.cast_names) >= 5 or len(scene.tags) >= 3]
    ratio = len(heavy_scenes) / len(project.scenes) if project.scenes else 0

    if len(heavy_scenes) < weights.overtime_scene_threshold and ratio < 0.5:
        return []

    return [
        RiskFlag(
            risk_id="overtime-1",
            category="overtime",
            severity=_severity_from_ratio(ratio),
            confidence=0.7,
            rationale="High concentration of cast-heavy or technically complex scenes can increase overtime risk.",
            evidence_refs=[f"heavy_scene_count:{len(heavy_scenes)}", f"total_scene_count:{len(project.scenes)}"],
            assumptions_used=["heuristic:heavy_scene_overtime_proxy"],
            is_heuristic=True,
            limitations=["Does not account for actual stripboard timings or union break rules."],
        )
    ]


def location_clustering_opportunities(project: Project, weights: AnalysisWeights | None = None) -> list[Recommendation]:
    weights = weights or AnalysisWeights()
    location_counts = Counter(scene.location_name for scene in project.scenes)
    recs: list[Recommendation] = []

    for location, count in sorted(location_counts.items(), key=lambda item: item[0].lower()):
        if count >= weights.location_cluster_min_repeat:
            recs.append(
                Recommendation(
                    recommendation_id=f"location-cluster-{location.lower().replace(' ', '-')}",
                    title=f"Cluster {location} scenes",
                    rationale="Multiple scenes share this location and may benefit from grouped shooting days.",
                    expected_upside="Reduced company moves and setup repetition.",
                    expected_downside="May reduce narrative shooting order flexibility.",
                    impacted_departments=["AD", "Locations", "Transport", "Camera"],
                    confidence=0.8,
                    rollback_instruction="Revert to script-order schedule if creative continuity suffers.",
                    evidence_refs=[f"location:{location}", f"scene_count:{count}"],
                    assumptions_used=["rule:location_repeat_threshold"],
                    is_heuristic=False,
                )
            )
    return recs


def cast_concentration_alerts(project: Project, weights: AnalysisWeights | None = None) -> list[RiskFlag]:
    weights = weights or AnalysisWeights()
    appearances = defaultdict(int)

    for scene in project.scenes:
        for cast_member in scene.cast_names:
            appearances[cast_member] += 1

    total_scenes = len(project.scenes) or 1
    flags: list[RiskFlag] = []
    for cast_member, count in sorted(appearances.items(), key=lambda item: item[0].lower()):
        ratio = count / total_scenes
        if ratio >= weights.cast_concentration_ratio_threshold:
            flags.append(
                RiskFlag(
                    risk_id=f"cast-concentration-{cast_member.lower().replace(' ', '-')}",
                    category="cast",
                    severity=_severity_from_ratio(ratio),
                    confidence=0.75,
                    rationale="A single cast member appears in a high share of scenes, increasing schedule fragility.",
                    evidence_refs=[f"cast:{cast_member}", f"appearance_ratio:{ratio:.2f}"],
                    assumptions_used=["heuristic:cast_concentration_threshold"],
                    is_heuristic=True,
                    limitations=["Does not account for actor availability windows or turnaround rules."],
                )
            )
    return flags


def night_shoot_concentration_alerts(project: Project, weights: AnalysisWeights | None = None) -> list[RiskFlag]:
    weights = weights or AnalysisWeights()
    night_scenes = [scene for scene in project.scenes if scene.day_night.lower() == "night"]
    ratio = len(night_scenes) / len(project.scenes) if project.scenes else 0

    if ratio < weights.night_shoot_ratio_threshold:
        return []

    return [
        RiskFlag(
            risk_id="night-concentration-1",
            category="schedule_pressure",
            severity=_severity_from_ratio(ratio),
            confidence=0.8,
            rationale="High concentration of night scenes can increase fatigue and reduce schedule resilience.",
            evidence_refs=[f"night_scene_ratio:{ratio:.2f}", f"night_scene_count:{len(night_scenes)}"],
            assumptions_used=["heuristic:night_scene_ratio_threshold"],
            is_heuristic=True,
            limitations=["Does not model company turnaround, local permit curfews, or weather variance."],
        )
    ]

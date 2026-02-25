from __future__ import annotations

from .constants import COMPLEXITY_TAGS, AnalysisWeights
from .types import ScriptScene


def scene_complexity_score(scene: ScriptScene, weights: AnalysisWeights | None = None) -> dict:
    weights = weights or AnalysisWeights()
    page_component = (scene.page_length or 1.0) * weights.page_length_weight
    cast_component = len(scene.cast_names) * weights.cast_count_weight
    tag_component = sum(COMPLEXITY_TAGS.get(tag.lower(), 0.5) for tag in scene.tags) * weights.tag_complexity_weight
    day_night_component = weights.night_weight if scene.day_night.strip().lower() == "night" else 0.0
    int_ext_component = weights.ext_weight if scene.int_ext.strip().lower() == "ext" else 0.0
    total = round(page_component + cast_component + tag_component + day_night_component + int_ext_component, 2)

    return {
        "scene_id": scene.scene_id,
        "score": total,
        "rationale": "Complexity score combines page length, cast count, tag burden, and shooting conditions.",
        "evidence_refs": [
            f"scene:{scene.scene_id}",
            f"location:{scene.location_name}",
            f"tags:{','.join(scene.tags) if scene.tags else 'none'}",
        ],
        "is_heuristic": False,
        "components": {
            "page_component": round(page_component, 2),
            "cast_component": round(cast_component, 2),
            "tag_component": round(tag_component, 2),
            "day_night_component": round(day_night_component, 2),
            "int_ext_component": round(int_ext_component, 2),
        },
    }


def vfx_risk_score(scene: ScriptScene, weights: AnalysisWeights | None = None) -> dict:
    weights = weights or AnalysisWeights()
    vfx_tag_count = sum(1 for tag in scene.tags if tag.lower() in {"vfx", "sfx"})
    base_score = scene_complexity_score(scene, weights)["score"]
    vfx_score = round(base_score + (vfx_tag_count * weights.vfx_tag_bonus), 2)

    severity = "low"
    if vfx_score >= 20:
        severity = "high"
    elif vfx_score >= 12:
        severity = "med"

    return {
        "scene_id": scene.scene_id,
        "score": vfx_score,
        "severity": severity,
        "rationale": "VFX risk score adds VFX/SFX tag pressure on top of deterministic scene complexity.",
        "evidence_refs": [f"scene:{scene.scene_id}", f"vfx_tags:{vfx_tag_count}"],
        "is_heuristic": False,
    }

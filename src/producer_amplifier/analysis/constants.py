from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisWeights:
    page_length_weight: float = 1.5
    cast_count_weight: float = 1.0
    tag_complexity_weight: float = 2.0
    night_weight: float = 1.2
    ext_weight: float = 1.0
    vfx_tag_bonus: float = 4.0
    hidden_cost_threshold: float = 5000.0
    overtime_scene_threshold: int = 5
    location_cluster_min_repeat: int = 2
    cast_concentration_ratio_threshold: float = 0.5
    night_shoot_ratio_threshold: float = 0.4


COMPLEXITY_TAGS = {
    "stunts": 3.0,
    "sfx": 2.5,
    "vfx": 3.0,
    "vehicles": 1.5,
    "crowds": 2.0,
}

HIDDEN_COST_KEYWORDS = {"contingency", "misc", "kit", "allowance", "unknown", "unspecified"}

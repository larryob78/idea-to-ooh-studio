from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Severity = Literal["low", "med", "high"]
RiskCategory = Literal["vfx", "overtime", "location", "cast", "schedule_pressure", "hidden_cost"]


@dataclass(frozen=True)
class ScriptScene:
    scene_id: str
    page_length: float | None
    int_ext: str
    day_night: str
    location_name: str
    cast_names: list[str]
    tags: list[str]
    raw_text_excerpt: str | None = None


@dataclass(frozen=True)
class BudgetLineItem:
    account_code: str
    account_name: str
    quantity: float
    unit: str
    rate: float
    total: float
    source_file: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None

    def __post_init__(self) -> None:
        if self.quantity < 0 or self.rate < 0 or self.total < 0:
            raise ValueError("Budget quantities, rates, and totals must be non-negative")


@dataclass(frozen=True)
class RiskFlag:
    risk_id: str
    category: RiskCategory
    severity: Severity
    confidence: float
    rationale: str
    evidence_refs: list[str]
    is_heuristic: bool
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    title: str
    rationale: str
    expected_upside: str
    expected_downside: str
    impacted_departments: list[str]
    confidence: float
    rollback_instruction: str
    evidence_refs: list[str]
    is_heuristic: bool
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Project:
    project_id: str
    title: str
    scenes: list[ScriptScene]
    budget_items: list[BudgetLineItem]

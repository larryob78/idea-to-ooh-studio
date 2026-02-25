from producer_amplifier.analysis.rules import (
    cast_concentration_alerts,
    hidden_cost_flags,
    location_clustering_opportunities,
    night_shoot_concentration_alerts,
    overtime_risk_indicators,
)
from producer_amplifier.analysis.scoring import scene_complexity_score, vfx_risk_score
from producer_amplifier.analysis.types import BudgetLineItem, Project, ScriptScene


def _project_fixture() -> Project:
    scenes = [
        ScriptScene("1", 3.0, "EXT", "NIGHT", "Street", ["Alex", "Blair"], ["vfx", "crowds"]),
        ScriptScene("2", 2.0, "INT", "DAY", "Apartment", ["Alex"], ["dialogue"]),
        ScriptScene("3", 4.0, "EXT", "NIGHT", "Street", ["Alex", "Casey", "Dev", "Eli", "Fran"], ["stunts", "vehicles", "sfx"]),
    ]
    budget_items = [
        BudgetLineItem("500", "Misc contingency", 1, "lot", 6000, 6000),
        BudgetLineItem("210", "Grip", 2, "day", 500, 1000),
    ]
    return Project(project_id="p-01", title="Feature", scenes=scenes, budget_items=budget_items)


def test_scoring_is_deterministic() -> None:
    project = _project_fixture()
    first = scene_complexity_score(project.scenes[0])
    second = scene_complexity_score(project.scenes[0])
    assert first == second

    first_vfx = vfx_risk_score(project.scenes[0])
    second_vfx = vfx_risk_score(project.scenes[0])
    assert first_vfx == second_vfx


def test_rules_return_structured_outputs() -> None:
    project = _project_fixture()

    assert hidden_cost_flags(project)
    assert location_clustering_opportunities(project)
    assert cast_concentration_alerts(project)
    assert night_shoot_concentration_alerts(project)

    overtime_flags = overtime_risk_indicators(project)
    if overtime_flags:
        assert overtime_flags[0].is_heuristic is True
        assert overtime_flags[0].limitations

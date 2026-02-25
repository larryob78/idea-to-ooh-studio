import pytest

from producer_amplifier.analysis.types import BudgetLineItem, Project, ScriptScene


def test_schema_minimum_project() -> None:
    scene = ScriptScene(
        scene_id="1",
        page_length=2.0,
        int_ext="INT",
        day_night="DAY",
        location_name="Apartment",
        cast_names=["Alex"],
        tags=["dialogue"],
    )
    item = BudgetLineItem(
        account_code="100",
        account_name="Camera package",
        quantity=1,
        unit="lot",
        rate=2000,
        total=2000,
    )
    project = Project(project_id="p1", title="Test", scenes=[scene], budget_items=[item])

    assert project.title == "Test"
    assert project.scenes[0].scene_id == "1"


def test_budget_line_item_validation() -> None:
    with pytest.raises(ValueError):
        BudgetLineItem(
            account_code="101",
            account_name="Bad",
            quantity=-1,
            unit="day",
            rate=100,
            total=100,
        )

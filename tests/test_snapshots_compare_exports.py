from pathlib import Path

from producer_amplifier.analysis.assumptions import AssumptionsRepository
from producer_amplifier.analysis.compare import compare_snapshots
from producer_amplifier.analysis.engine import analyze_project
from producer_amplifier.analysis.exports import export_json_report, export_memo_markdown, export_risks_csv
from producer_amplifier.analysis.persistence import JsonStore
from producer_amplifier.analysis.snapshots import SnapshotsRepository
from producer_amplifier.analysis.types import BudgetLineItem, Project, ScriptScene


def _project() -> Project:
    scenes = [
        ScriptScene("1", 1.0, "INT", "DAY", "Office", ["A"], ["dialogue"]),
        ScriptScene("2", 3.0, "EXT", "NIGHT", "Street", ["A", "B", "C", "D", "E"], ["stunts", "sfx", "vfx"]),
    ]
    budget = [
        BudgetLineItem("100", "Misc contingency", 1, "lot", 7000, 7000),
    ]
    return Project(project_id="proj-1", title="Demo", scenes=scenes, budget_items=budget)


def test_snapshot_create_list_load_compare_and_exports(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "store.json")
    asm_repo = AssumptionsRepository(store)
    snp_repo = SnapshotsRepository(store)

    assumption = asm_repo.add(
        {
            "title": "Night permit reliable",
            "description": "City quote indicates likely approval",
            "source_type": "quote",
            "confidence": 0.8,
        }
    )

    project = _project()
    risks, recs, summary = analyze_project(project)
    snapshot_a = snp_repo.create_snapshot(
        project_id=project.project_id,
        risk_flags=risks,
        recommendations=recs,
        summary_metrics=summary,
        assumptions=[assumption],
        source_files=["script.csv", "budget.csv"],
    )

    asm_repo.update(assumption.assumption_id, {"confidence": 0.6})
    assumptions_b = asm_repo.list()
    snapshot_b = snp_repo.create_snapshot(
        project_id=project.project_id,
        risk_flags=risks,
        recommendations=recs,
        summary_metrics={**summary, "risk_count": summary["risk_count"] + 1},
        assumptions=assumptions_b,
        source_files=["script.csv", "budget.csv"],
    )

    listed = snp_repo.list_snapshots(project.project_id)
    assert [item["snapshot_id"] for item in listed] == sorted([snapshot_a, snapshot_b])

    loaded_b = snp_repo.load_snapshot(snapshot_b)
    diff = compare_snapshots(snp_repo.load_snapshot(snapshot_a), loaded_b)
    assert diff["snapshot_a"] == snapshot_a
    assert diff["snapshot_b"] == snapshot_b
    assert diff["metric_deltas"]["risk_count"]["delta"] == 1
    assert diff["assumption_diffs"]["changed"]

    json_path = export_json_report(loaded_b, tmp_path / "exports" / "report.json")
    csv_path = export_risks_csv(loaded_b, tmp_path / "exports" / "risks.csv")
    memo_path = export_memo_markdown(loaded_b, tmp_path / "exports" / "memo.md", compare_diff=diff)

    assert json_path.exists()
    assert csv_path.exists()
    assert memo_path.exists()
    memo = memo_path.read_text(encoding="utf-8")
    assert "HEURISTIC AND LIMITATION NOTICE" in memo

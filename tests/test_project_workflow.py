import json
from pathlib import Path

from producer_amplifier.analysis.project_workflow import (
    project_analyze,
    project_compare,
    project_export,
    project_ingest,
    project_init,
    project_list_snapshots,
    project_snapshot,
)


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    script = tmp_path / "script.csv"
    budget = tmp_path / "budget.csv"
    schedule = tmp_path / "schedule.csv"
    script.write_text(
        "scene_id,int_ext,day_night,location_name,page_length,cast_names,tags\n"
        "1,EXT,NIGHT,Street,2.0,A|B|C|D|E,stunts|vfx|sfx\n",
        encoding="utf-8",
    )
    budget.write_text(
        "account_code,account_name,quantity,unit,rate,total\n"
        "500,Misc contingency,1,lot,6000,6000\n",
        encoding="utf-8",
    )
    schedule.write_text("day,scene_id\n1,1\n", encoding="utf-8")
    return script, budget, schedule


def test_project_init_creates_structure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = project_init("demo")
    root = Path(out["root"])
    assert (root / "inputs").exists()
    assert (root / "outputs").exists()
    assert (root / "snapshots").exists()
    assert (root / "logs").exists()
    assert (root / "config").exists()


def test_ingest_report_and_deterministic_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    project_init("demo")
    script, budget, schedule = _write_inputs(tmp_path)
    report = project_ingest("demo", script, budget, schedule)
    assert "parse_confidence" in report
    ingest_report = Path("projects/demo/outputs/ingest_report.json")
    assert ingest_report.exists()

    analyze = project_analyze("demo")
    assert analyze["snapshot_id"].startswith("snp-")
    project_snapshot("demo", "baseline")
    snapshots = project_list_snapshots("demo")
    assert snapshots

    project_export("demo", "all")
    outputs = Path("projects/demo/outputs")
    assert (outputs / "project_summary.json").exists()
    assert (outputs / "risk_register.csv").exists()
    assert (outputs / "recommendations.csv").exists()
    assert (outputs / "assumptions.csv").exists()
    assert (outputs / "producer_memo.md").exists()


def test_compare_and_audit_log_contains_required_keys(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    project_init("demo")
    script, budget, schedule = _write_inputs(tmp_path)
    project_ingest("demo", script, budget, schedule)
    a = project_analyze("demo")["snapshot_id"]
    b = project_analyze("demo")["snapshot_id"]
    diff = project_compare("demo", a, b)
    assert "metric_deltas" in diff

    log_path = Path("projects/demo/logs/audit.log")
    lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    required = {"action", "timestamp", "inputs", "artifacts", "warnings_count", "versions"}
    assert required.issubset(lines[-1].keys())

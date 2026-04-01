import json
import os
import subprocess
import sys
from pathlib import Path


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    repo_src = Path(__file__).resolve().parents[1] / "src"
    env["PYTHONPATH"] = str(repo_src)
    return subprocess.run([sys.executable, "-m", "producer_amplifier.cli", *args], cwd=cwd, capture_output=True, text=True, check=True, env=env)


def test_cli_full_project_flow(tmp_path: Path) -> None:
    script = tmp_path / "script.csv"
    budget = tmp_path / "budget.csv"
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

    _run(tmp_path, "project", "init", "p-cli")
    _run(tmp_path, "project", "ingest", "--project", "p-cli", "--script", str(script), "--budget", str(budget))
    analyzed = _run(tmp_path, "project", "analyze", "--project", "p-cli")
    snapshot_id = json.loads(analyzed.stdout)["snapshot_id"]
    _run(tmp_path, "project", "snapshot", "--project", "p-cli", "--label", "baseline")
    _run(tmp_path, "project", "export", "--project", "p-cli", "--format", "all")

    out = tmp_path / "projects" / "p-cli" / "outputs"
    assert (out / "ingest_report.json").exists()
    assert (out / "project_summary.json").exists()
    assert (out / "risk_register.csv").exists()
    assert (out / "recommendations.csv").exists()
    assert (out / "assumptions.csv").exists()
    assert (out / "producer_memo.md").exists()
    assert snapshot_id.startswith("snp-")

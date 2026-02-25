import json
import os
import subprocess
import sys
from pathlib import Path


def _run(*args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run([sys.executable, "-m", "producer_amplifier.cli", *args], capture_output=True, text=True, check=True, env=env)


def test_cli_assumptions_snapshot_export_flow(tmp_path: Path) -> None:
    store = tmp_path / "store.json"
    project = {
        "project_id": "p-cli",
        "title": "CLI Demo",
        "scenes": [
            {
                "scene_id": "1",
                "page_length": 2.0,
                "int_ext": "EXT",
                "day_night": "NIGHT",
                "location_name": "Street",
                "cast_names": ["A", "B", "C", "D", "E"],
                "tags": ["stunts", "vfx", "sfx"],
                "raw_text_excerpt": None,
            }
        ],
        "budget_items": [
            {
                "account_code": "500",
                "account_name": "Misc contingency",
                "quantity": 1,
                "unit": "lot",
                "rate": 6000,
                "total": 6000,
                "source_file": None,
                "source_sheet": None,
                "source_row": None,
            }
        ],
    }
    project_path = tmp_path / "project.json"
    project_path.write_text(json.dumps(project), encoding="utf-8")

    _run("--store", str(store), "assumptions", "add", "--title", "Permits stable", "--description", "Quoted by office", "--source-type", "quote", "--confidence", "0.9")
    created = _run("--store", str(store), "snapshots", "create", str(project_path))
    snapshot_id = json.loads(created.stdout)["snapshot_id"]

    listed = _run("--store", str(store), "snapshots", "list", "p-cli")
    assert snapshot_id in listed.stdout

    out_dir = tmp_path / "exports"
    _run("--store", str(store), "export", "all", snapshot_id, "--out-dir", str(out_dir))

    assert (out_dir / f"{snapshot_id}.json").exists()
    assert (out_dir / f"{snapshot_id}-risks.csv").exists()
    assert (out_dir / f"{snapshot_id}-memo.md").exists()

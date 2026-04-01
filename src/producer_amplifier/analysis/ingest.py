from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .types import BudgetLineItem, Project, ScriptScene


SCRIPT_REQUIRED = ["scene_id", "int_ext", "day_night", "location_name"]
BUDGET_REQUIRED = ["account_code", "account_name", "quantity", "unit", "rate", "total"]


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            warnings.append(f"No header row found in {path}")
            return rows, warnings
        for idx, row in enumerate(reader, start=2):
            cleaned = {k.strip(): (v.strip() if isinstance(v, str) else "") for k, v in row.items() if k}
            cleaned["_source_row"] = str(idx)
            rows.append(cleaned)
    return rows, warnings


def ingest_project_inputs(
    project_slug: str,
    script_path: Path,
    budget_path: Path,
    schedule_path: Path | None,
    project_root: Path,
) -> dict[str, Any]:
    warnings: list[str] = []
    guessed_fields: list[str] = []
    provenance: list[dict[str, Any]] = []

    script_rows, script_warnings = _read_csv(script_path)
    budget_rows, budget_warnings = _read_csv(budget_path)
    warnings.extend(script_warnings + budget_warnings)

    scenes: list[ScriptScene] = []
    for row in script_rows:
        missing = [field for field in SCRIPT_REQUIRED if not row.get(field)]
        if missing:
            warnings.append(f"script row {row.get('_source_row')} missing required fields: {missing}")
            continue
        page_length = None
        if row.get("page_length"):
            try:
                page_length = float(row["page_length"])
            except ValueError:
                warnings.append(f"script row {row.get('_source_row')} invalid page_length; treated as unknown")
                guessed_fields.append(f"script:{row.get('_source_row')}:page_length")
        cast_names = [x.strip() for x in row.get("cast_names", "").split("|") if x.strip()]
        tags = [x.strip() for x in row.get("tags", "").split("|") if x.strip()]
        scenes.append(
            ScriptScene(
                scene_id=row["scene_id"],
                page_length=page_length,
                int_ext=row["int_ext"],
                day_night=row["day_night"],
                location_name=row["location_name"],
                cast_names=cast_names,
                tags=tags,
                raw_text_excerpt=row.get("raw_text_excerpt") or None,
            )
        )
        provenance.append({"type": "script", "file": str(script_path), "row": int(row["_source_row"])})

    budget_items: list[BudgetLineItem] = []
    for row in budget_rows:
        missing = [field for field in BUDGET_REQUIRED if not row.get(field)]
        if missing:
            warnings.append(f"budget row {row.get('_source_row')} missing required fields: {missing}")
            continue
        try:
            item = BudgetLineItem(
                account_code=row["account_code"],
                account_name=row["account_name"],
                quantity=float(row["quantity"]),
                unit=row["unit"],
                rate=float(row["rate"]),
                total=float(row["total"]),
                source_file=str(budget_path),
                source_sheet=row.get("source_sheet") or None,
                source_row=int(row["_source_row"]),
            )
            budget_items.append(item)
            provenance.append({"type": "budget", "file": str(budget_path), "row": int(row["_source_row"])})
        except Exception as exc:  # parse validation path
            warnings.append(f"budget row {row.get('_source_row')} parse error: {exc}")

    schedule_rows = []
    if schedule_path:
        schedule_rows, schedule_warnings = _read_csv(schedule_path)
        warnings.extend(schedule_warnings)
        if not schedule_rows:
            warnings.append("schedule file provided but no rows were parsed")

    parse_confidence = round(max(0.0, 1.0 - (0.05 * len(warnings))), 2)
    report = {
        "project_slug": project_slug,
        "missing_fields": [w for w in warnings if "missing required fields" in w],
        "guessed_fields": sorted(set(guessed_fields)),
        "parse_confidence": parse_confidence,
        "limitations": [
            "CSV ingest uses deterministic field mapping and does not infer complex screenplay semantics.",
            "Rows with missing required fields are skipped and logged as warnings.",
            "Optional schedule ingest is stored for provenance only in this phase.",
        ],
        "warnings": warnings,
        "provenance": {
            "sources": [str(script_path), str(budget_path)] + ([str(schedule_path)] if schedule_path else []),
            "rows": provenance,
        },
    }

    project = Project(project_id=project_slug, title=project_slug, scenes=scenes, budget_items=budget_items)
    bundle = {
        "project": {
            "project_id": project.project_id,
            "title": project.title,
            "scenes": [asdict(scene) for scene in project.scenes],
            "budget_items": [asdict(item) for item in project.budget_items],
        },
        "schedule_rows": schedule_rows,
    }

    config_dir = project_root / "config"
    outputs_dir = project_root / "outputs"
    config_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "project_data.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (outputs_dir / "ingest_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report

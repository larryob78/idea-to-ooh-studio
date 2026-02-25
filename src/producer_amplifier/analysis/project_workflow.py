from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .assumptions import AssumptionsRepository
from .audit import write_audit_log
from .compare import compare_snapshots, summarize_diff
from .engine import analyze_project
from .exports import export_json_report, export_memo_markdown, export_risks_csv
from .ingest import ingest_project_inputs
from .persistence import JsonStore
from .snapshots import SnapshotsRepository
from .types import AnalysisSnapshot, Assumption, BudgetLineItem, Project, ScriptScene


PROJECTS_ROOT = Path("projects")


def project_paths(slug: str) -> dict[str, Path]:
    root = PROJECTS_ROOT / slug
    return {
        "root": root,
        "inputs": root / "inputs",
        "outputs": root / "outputs",
        "snapshots": root / "snapshots",
        "logs": root / "logs",
        "config": root / "config",
        "audit_log": root / "logs" / "audit.log",
        "store": root / "config" / "store.json",
    }


def project_init(slug: str) -> dict[str, str]:
    paths = project_paths(slug)
    for key in ["inputs", "outputs", "snapshots", "logs", "config"]:
        paths[key].mkdir(parents=True, exist_ok=True)
    metadata = {"project_slug": slug, "created": True}
    (paths["config"] / "project.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_audit_log(paths["audit_log"], "project_init", [], [paths["config"] / "project.json"], 0)
    return {k: str(v) for k, v in paths.items() if k != "audit_log" and k != "store"}


def project_ingest(slug: str, script: Path, budget: Path, schedule: Path | None = None) -> dict[str, Any]:
    paths = project_paths(slug)
    for key in ["inputs", "outputs", "snapshots", "logs", "config"]:
        paths[key].mkdir(parents=True, exist_ok=True)

    script_dst = paths["inputs"] / "script.csv"
    budget_dst = paths["inputs"] / "budget.csv"
    shutil.copy2(script, script_dst)
    shutil.copy2(budget, budget_dst)
    schedule_dst = None
    if schedule:
        schedule_dst = paths["inputs"] / "schedule.csv"
        shutil.copy2(schedule, schedule_dst)

    report = ingest_project_inputs(slug, script_dst, budget_dst, schedule_dst, paths["root"])
    write_audit_log(
        paths["audit_log"],
        "project_ingest",
        [script_dst, budget_dst] + ([schedule_dst] if schedule_dst else []),
        [paths["outputs"] / "ingest_report.json", paths["config"] / "project_data.json"],
        len(report["warnings"]),
    )
    return report


def _load_project_data(slug: str) -> Project:
    paths = project_paths(slug)
    payload = json.loads((paths["config"] / "project_data.json").read_text(encoding="utf-8"))
    project_payload = payload["project"]
    scenes = [ScriptScene(**row) for row in project_payload["scenes"]]
    budget_items = [BudgetLineItem(**row) for row in project_payload["budget_items"]]
    return Project(project_id=project_payload["project_id"], title=project_payload["title"], scenes=scenes, budget_items=budget_items)


def _repos(slug: str) -> tuple[AssumptionsRepository, SnapshotsRepository, dict[str, Path]]:
    paths = project_paths(slug)
    store = JsonStore(paths["store"])
    return AssumptionsRepository(store), SnapshotsRepository(store), paths


def project_analyze(slug: str) -> dict[str, Any]:
    asm_repo, snp_repo, paths = _repos(slug)
    project = _load_project_data(slug)
    risks, recommendations, summary = analyze_project(project)
    assumptions = asm_repo.list()
    snapshot_id = snp_repo.create_snapshot(
        project_id=slug,
        risk_flags=risks,
        recommendations=recommendations,
        summary_metrics=summary,
        assumptions=assumptions,
        inputs_metadata={"analysis": "project_analyze"},
        source_files=[str(paths["inputs"] / "script.csv"), str(paths["inputs"] / "budget.csv")],
    )
    latest = {
        "snapshot_id": snapshot_id,
        "summary": summary,
        "risk_flags": [asdict(r) for r in risks],
        "recommendations": [asdict(r) for r in recommendations],
        "assumptions": [asdict(a) for a in assumptions],
    }
    (paths["config"] / "latest_analysis.json").write_text(json.dumps(latest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary_path = paths["outputs"] / "project_summary.json"
    summary_path.write_text(json.dumps(latest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_audit_log(paths["audit_log"], "project_analyze", [paths["config"] / "project_data.json"], [summary_path], 0, extra={"snapshot_id": snapshot_id})
    return {"snapshot_id": snapshot_id, "summary": summary}


def project_snapshot(slug: str, label: str) -> dict[str, str]:
    _, snp_repo, paths = _repos(slug)
    latest = json.loads((paths["config"] / "latest_analysis.json").read_text(encoding="utf-8"))
    snapshot_id = latest["snapshot_id"]
    label_slug = "-".join(label.lower().split())
    marker = paths["snapshots"] / f"{label_slug}__{snapshot_id}.txt"
    marker.write_text(f"label={label}\nsnapshot_id={snapshot_id}\n", encoding="utf-8")
    write_audit_log(paths["audit_log"], "project_snapshot", [paths["config"] / "latest_analysis.json"], [marker], 0)
    return {"label": label, "snapshot_id": snapshot_id, "marker": str(marker), "known_snapshots": str(len(snp_repo.list_snapshots(slug)))}


def project_list_snapshots(slug: str) -> list[dict[str, Any]]:
    _, snp_repo, paths = _repos(slug)
    snapshots = snp_repo.list_snapshots(slug)
    write_audit_log(paths["audit_log"], "project_list_snapshots", [], [], 0, extra={"count": len(snapshots)})
    return snapshots


def project_compare(slug: str, snapshot_a: str, snapshot_b: str) -> dict[str, Any]:
    _, snp_repo, paths = _repos(slug)
    loaded_a = snp_repo.load_snapshot(snapshot_a)
    loaded_b = snp_repo.load_snapshot(snapshot_b)
    diff = compare_snapshots(loaded_a, loaded_b)
    diff_json = paths["outputs"] / "snapshot_diff.json"
    diff_md = paths["outputs"] / "snapshot_diff.md"
    diff_json.write_text(json.dumps(diff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    diff_md.write_text("# Snapshot Diff\n\n" + summarize_diff(diff) + "\n", encoding="utf-8")
    write_audit_log(paths["audit_log"], "project_compare", [], [diff_json, diff_md], 0)
    return diff


def _write_recommendations_csv(snapshot: AnalysisSnapshot, path: Path) -> None:
    fields = [
        "recommendation_id",
        "title",
        "rationale",
        "expected_upside",
        "expected_downside",
        "impacted_departments",
        "confidence",
        "assumptions_used",
        "is_heuristic",
        "limitations",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rec in snapshot.recommendations:
            writer.writerow(
                {
                    "recommendation_id": rec.recommendation_id,
                    "title": rec.title,
                    "rationale": rec.rationale,
                    "expected_upside": rec.expected_upside,
                    "expected_downside": rec.expected_downside,
                    "impacted_departments": " | ".join(rec.impacted_departments),
                    "confidence": rec.confidence,
                    "assumptions_used": " | ".join(rec.assumptions_used),
                    "is_heuristic": rec.is_heuristic,
                    "limitations": " | ".join(rec.limitations),
                }
            )


def _write_assumptions_csv(assumptions: list[Assumption], path: Path) -> None:
    fields = ["assumption_id", "title", "description", "source_type", "confidence", "evidence_refs", "limitations"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for asm in assumptions:
            writer.writerow(
                {
                    "assumption_id": asm.assumption_id,
                    "title": asm.title,
                    "description": asm.description,
                    "source_type": asm.source_type,
                    "confidence": asm.confidence,
                    "evidence_refs": " | ".join(asm.evidence_refs),
                    "limitations": " | ".join(asm.limitations),
                }
            )


def project_export(slug: str, export_format: str = "all", compare: tuple[str, str] | None = None) -> dict[str, str]:
    _, snp_repo, paths = _repos(slug)
    latest = json.loads((paths["config"] / "latest_analysis.json").read_text(encoding="utf-8"))
    snapshot = snp_repo.load_snapshot(latest["snapshot_id"])

    compare_diff = None
    if compare:
        compare_diff = compare_snapshots(snp_repo.load_snapshot(compare[0]), snp_repo.load_snapshot(compare[1]))
        (paths["outputs"] / "snapshot_diff.md").write_text("# Snapshot Diff\n\n" + summarize_diff(compare_diff) + "\n", encoding="utf-8")

    artifacts: list[Path] = []
    summary_path = paths["outputs"] / "project_summary.json"
    summary_path.write_text(json.dumps(asdict(snapshot), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.append(summary_path)

    if export_format in {"all", "json"}:
        artifacts.append(export_json_report(snapshot, paths["outputs"] / "analysis_snapshot.json"))
    if export_format in {"all", "csv", "risks-csv"}:
        artifacts.append(export_risks_csv(snapshot, paths["outputs"] / "risk_register.csv"))
        _write_recommendations_csv(snapshot, paths["outputs"] / "recommendations.csv")
        _write_assumptions_csv(snapshot.assumptions, paths["outputs"] / "assumptions.csv")
        artifacts.extend([paths["outputs"] / "recommendations.csv", paths["outputs"] / "assumptions.csv"])
    if export_format in {"all", "memo", "memo-md"}:
        artifacts.append(export_memo_markdown(snapshot, paths["outputs"] / "producer_memo.md", compare_diff=compare_diff))

    write_audit_log(paths["audit_log"], "project_export", [paths["config"] / "latest_analysis.json"], artifacts, 0)
    return {"status": "ok", "outputs": str(paths["outputs"])}

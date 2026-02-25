from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from producer_amplifier.analysis.assumptions import AssumptionsRepository
from producer_amplifier.analysis.compare import compare_snapshots, summarize_diff
from producer_amplifier.analysis.engine import analyze_project
from producer_amplifier.analysis.exports import export_json_report, export_memo_markdown, export_risks_csv
from producer_amplifier.analysis.snapshots import SnapshotsRepository
from producer_amplifier.analysis.types import BudgetLineItem, Project, ScriptScene


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sba", description="Trustable analysis CLI")
    parser.add_argument("--store", default=".data/trustable_analysis_v2.json")
    sub = parser.add_subparsers(dest="entity", required=True)

    assumptions = sub.add_parser("assumptions")
    a_sub = assumptions.add_subparsers(dest="action", required=True)

    add = a_sub.add_parser("add")
    add.add_argument("--title", required=True)
    add.add_argument("--description", required=True)
    add.add_argument("--source-type", required=True)
    add.add_argument("--confidence", required=True, type=float)

    a_sub.add_parser("list")
    update = a_sub.add_parser("update")
    update.add_argument("assumption_id")
    update.add_argument("--title")
    update.add_argument("--description")
    update.add_argument("--source-type")
    update.add_argument("--confidence", type=float)

    delete = a_sub.add_parser("delete")
    delete.add_argument("assumption_id")

    a_sub.add_parser("export")

    snapshots = sub.add_parser("snapshots")
    s_sub = snapshots.add_subparsers(dest="action", required=True)
    c = s_sub.add_parser("create")
    c.add_argument("project_json")
    c.add_argument("--project-id")
    c.add_argument("--source-files", nargs="*", default=[])

    l = s_sub.add_parser("list")
    l.add_argument("project_id")
    ld = s_sub.add_parser("load")
    ld.add_argument("snapshot_id")
    cmp = s_sub.add_parser("compare")
    cmp.add_argument("snapshot_a")
    cmp.add_argument("snapshot_b")

    exports = sub.add_parser("export")
    e_sub = exports.add_subparsers(dest="action", required=True)
    for name in ["json", "risks-csv", "memo-md", "all"]:
        e = e_sub.add_parser(name)
        e.add_argument("snapshot_id")
        e.add_argument("--out-dir", default="exports")
        e.add_argument("--compare-with")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    asm_repo = AssumptionsRepository()
    snp_repo = SnapshotsRepository()
    asm_repo.store.path = Path(args.store)
    snp_repo.store.path = Path(args.store)

    if args.entity == "assumptions":
        if args.action == "add":
            obj = asm_repo.add(
                {
                    "title": args.title,
                    "description": args.description,
                    "source_type": args.source_type,
                    "confidence": args.confidence,
                }
            )
            print(json.dumps(asdict(obj), indent=2, sort_keys=True))
        elif args.action == "list":
            print(json.dumps([asdict(x) for x in asm_repo.list()], indent=2, sort_keys=True))
        elif args.action == "update":
            updates = {k: v for k, v in {"title": args.title, "description": args.description, "source_type": args.source_type, "confidence": args.confidence}.items() if v is not None}
            print(json.dumps(asdict(asm_repo.update(args.assumption_id, updates)), indent=2, sort_keys=True))
        elif args.action == "delete":
            print(json.dumps({"deleted": asm_repo.delete(args.assumption_id), "assumption_id": args.assumption_id}, indent=2, sort_keys=True))
        elif args.action == "export":
            print(json.dumps(asm_repo.export(), indent=2, sort_keys=True))
        return 0

    if args.entity == "snapshots":
        if args.action == "create":
            payload = json.loads(Path(args.project_json).read_text(encoding="utf-8"))
            scenes = [ScriptScene(**scene) for scene in payload["scenes"]]
            budget_items = [BudgetLineItem(**item) for item in payload["budget_items"]]
            project = Project(
                project_id=args.project_id or payload["project_id"],
                title=payload.get("title", "Untitled"),
                scenes=scenes,
                budget_items=budget_items,
            )
            risks, recs, summary = analyze_project(project)
            snapshot_id = snp_repo.create_snapshot(
                project_id=project.project_id,
                risk_flags=risks,
                recommendations=recs,
                summary_metrics=summary,
                assumptions=asm_repo.list(),
                inputs_metadata={"source": str(Path(args.project_json).resolve())},
                source_files=args.source_files,
            )
            print(json.dumps({"snapshot_id": snapshot_id, "project_id": project.project_id}, indent=2, sort_keys=True))
        elif args.action == "list":
            print(json.dumps(snp_repo.list_snapshots(args.project_id), indent=2, sort_keys=True))
        elif args.action == "load":
            print(json.dumps(asdict(snp_repo.load_snapshot(args.snapshot_id)), indent=2, sort_keys=True))
        elif args.action == "compare":
            diff = compare_snapshots(snp_repo.load_snapshot(args.snapshot_a), snp_repo.load_snapshot(args.snapshot_b))
            print(json.dumps({"diff": diff, "summary": summarize_diff(diff)}, indent=2, sort_keys=True))
        return 0

    if args.entity == "export":
        snapshot = snp_repo.load_snapshot(args.snapshot_id)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        compare_diff = None
        if args.compare_with:
            compare_diff = compare_snapshots(snp_repo.load_snapshot(args.compare_with), snapshot)

        if args.action in {"json", "all"}:
            export_json_report(snapshot, out_dir / f"{snapshot.snapshot_id}.json")
        if args.action in {"risks-csv", "all"}:
            export_risks_csv(snapshot, out_dir / f"{snapshot.snapshot_id}-risks.csv")
        if args.action in {"memo-md", "all"}:
            export_memo_markdown(snapshot, out_dir / f"{snapshot.snapshot_id}-memo.md", compare_diff=compare_diff)
        print(json.dumps({"status": "ok", "out_dir": str(out_dir.resolve())}, indent=2, sort_keys=True))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

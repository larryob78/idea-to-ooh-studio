from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from producer_amplifier.analysis.assumptions import AssumptionsRepository
from producer_amplifier.analysis.compare import compare_snapshots, summarize_diff
from producer_amplifier.analysis.exports import export_json_report, export_memo_markdown, export_risks_csv
from producer_amplifier.analysis.project_workflow import (
    project_analyze,
    project_compare,
    project_export,
    project_ingest,
    project_init,
    project_list_snapshots,
    project_snapshot,
)
from producer_amplifier.analysis.snapshots import SnapshotsRepository


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

    project = sub.add_parser("project")
    p_sub = project.add_subparsers(dest="action", required=True)
    pi = p_sub.add_parser("init")
    pi.add_argument("slug")

    pig = p_sub.add_parser("ingest")
    pig.add_argument("--project", required=True)
    pig.add_argument("--script", required=True)
    pig.add_argument("--budget", required=True)
    pig.add_argument("--schedule")

    pa = p_sub.add_parser("analyze")
    pa.add_argument("--project", required=True)

    ps = p_sub.add_parser("snapshot")
    ps.add_argument("--project", required=True)
    ps.add_argument("--label", required=True)

    pls = p_sub.add_parser("list-snapshots")
    pls.add_argument("--project", required=True)

    pc = p_sub.add_parser("compare")
    pc.add_argument("--project", required=True)
    pc.add_argument("--a", required=True)
    pc.add_argument("--b", required=True)

    pe = p_sub.add_parser("export")
    pe.add_argument("--project", required=True)
    pe.add_argument("--format", default="all")
    pe.add_argument("--compare", nargs=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    asm_repo = AssumptionsRepository()
    snp_repo = SnapshotsRepository()
    asm_repo.store.path = Path(args.store)
    snp_repo.store.path = Path(args.store)

    if args.entity == "project":
        if args.action == "init":
            print(json.dumps(project_init(args.slug), indent=2, sort_keys=True))
        elif args.action == "ingest":
            report = project_ingest(args.project, Path(args.script), Path(args.budget), Path(args.schedule) if args.schedule else None)
            print(json.dumps(report, indent=2, sort_keys=True))
        elif args.action == "analyze":
            print(json.dumps(project_analyze(args.project), indent=2, sort_keys=True))
        elif args.action == "snapshot":
            print(json.dumps(project_snapshot(args.project, args.label), indent=2, sort_keys=True))
        elif args.action == "list-snapshots":
            print(json.dumps(project_list_snapshots(args.project), indent=2, sort_keys=True))
        elif args.action == "compare":
            print(json.dumps(project_compare(args.project, args.a, args.b), indent=2, sort_keys=True))
        elif args.action == "export":
            cmp = tuple(args.compare) if args.compare else None
            print(json.dumps(project_export(args.project, export_format=args.format, compare=cmp), indent=2, sort_keys=True))
        return 0

    if args.entity == "assumptions":
        if args.action == "add":
            obj = asm_repo.add({"title": args.title, "description": args.description, "source_type": args.source_type, "confidence": args.confidence})
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
        if args.action == "list":
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
        compare_diff = compare_snapshots(snp_repo.load_snapshot(args.compare_with), snapshot) if args.compare_with else None
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

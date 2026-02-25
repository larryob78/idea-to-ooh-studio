from __future__ import annotations

from dataclasses import asdict

from .types import AnalysisSnapshot


def _index_by(items: list[dict], key: str) -> dict[str, dict]:
    return {item[key]: item for item in items}


def compare_snapshots(snapshot_a: AnalysisSnapshot, snapshot_b: AnalysisSnapshot) -> dict:
    a_metrics = snapshot_a.summary_metrics
    b_metrics = snapshot_b.summary_metrics
    metric_keys = sorted(set(a_metrics.keys()) | set(b_metrics.keys()))
    metric_deltas = {
        key: {
            "from": a_metrics.get(key),
            "to": b_metrics.get(key),
            "delta": (b_metrics.get(key, 0) - a_metrics.get(key, 0))
            if isinstance(a_metrics.get(key, 0), (int, float)) and isinstance(b_metrics.get(key, 0), (int, float))
            else None,
        }
        for key in metric_keys
    }

    a_risks = _index_by([asdict(r) for r in snapshot_a.risk_flags], "risk_id")
    b_risks = _index_by([asdict(r) for r in snapshot_b.risk_flags], "risk_id")
    a_recs = _index_by([asdict(r) for r in snapshot_a.recommendations], "recommendation_id")
    b_recs = _index_by([asdict(r) for r in snapshot_b.recommendations], "recommendation_id")
    a_asm = _index_by([asdict(a) for a in snapshot_a.assumptions], "assumption_id")
    b_asm = _index_by([asdict(a) for a in snapshot_b.assumptions], "assumption_id")

    def diff_sets(lhs: dict[str, dict], rhs: dict[str, dict]) -> dict[str, list]:
        l_keys = set(lhs)
        r_keys = set(rhs)
        added = sorted(r_keys - l_keys)
        removed = sorted(l_keys - r_keys)
        changed = sorted([k for k in l_keys & r_keys if lhs[k] != rhs[k]])
        return {
            "added": [rhs[k] for k in added],
            "removed": [lhs[k] for k in removed],
            "changed": [{"id": k, "from": lhs[k], "to": rhs[k]} for k in changed],
        }

    risk_diffs = diff_sets(a_risks, b_risks)
    rec_diffs = diff_sets(a_recs, b_recs)
    asm_diffs = diff_sets(a_asm, b_asm)

    no_changes = all(
        [
            all(v["delta"] in (0, None) and v["from"] == v["to"] for v in metric_deltas.values()),
            not risk_diffs["added"] and not risk_diffs["removed"] and not risk_diffs["changed"],
            not rec_diffs["added"] and not rec_diffs["removed"] and not rec_diffs["changed"],
            not asm_diffs["added"] and not asm_diffs["removed"] and not asm_diffs["changed"],
        ]
    )

    return {
        "snapshot_a": snapshot_a.snapshot_id,
        "snapshot_b": snapshot_b.snapshot_id,
        "metric_deltas": metric_deltas,
        "risk_diffs": risk_diffs,
        "recommendation_diffs": rec_diffs,
        "assumption_diffs": asm_diffs,
        "no_changes": no_changes,
    }


def summarize_diff(diff: dict) -> str:
    if diff["no_changes"]:
        return "No changes detected between snapshots."
    return (
        "Snapshot diff summary: "
        f"{len(diff['risk_diffs']['added'])} risk(s) added, "
        f"{len(diff['risk_diffs']['removed'])} removed, "
        f"{len(diff['risk_diffs']['changed'])} changed; "
        f"{len(diff['recommendation_diffs']['added'])} recommendation(s) added, "
        f"{len(diff['recommendation_diffs']['removed'])} removed, "
        f"{len(diff['recommendation_diffs']['changed'])} changed; "
        f"{len(diff['assumption_diffs']['added'])} assumption(s) added, "
        f"{len(diff['assumption_diffs']['removed'])} removed, "
        f"{len(diff['assumption_diffs']['changed'])} changed."
    )

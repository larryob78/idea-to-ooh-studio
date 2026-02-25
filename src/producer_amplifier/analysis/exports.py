from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .compare import summarize_diff
from .types import AnalysisSnapshot


def export_json_report(snapshot: AnalysisSnapshot, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(snapshot)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def export_risks_csv(snapshot: AnalysisSnapshot, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "risk_id",
        "severity",
        "confidence",
        "category",
        "rationale",
        "evidence_refs",
        "assumptions_used",
        "is_heuristic",
        "limitations",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for risk in sorted(snapshot.risk_flags, key=lambda r: r.risk_id):
            writer.writerow(
                {
                    "risk_id": risk.risk_id,
                    "severity": risk.severity,
                    "confidence": risk.confidence,
                    "category": risk.category,
                    "rationale": risk.rationale,
                    "evidence_refs": " | ".join(risk.evidence_refs),
                    "assumptions_used": " | ".join(risk.assumptions_used),
                    "is_heuristic": risk.is_heuristic,
                    "limitations": " | ".join(risk.limitations),
                }
            )
    return output


def export_memo_markdown(snapshot: AnalysisSnapshot, output_path: str | Path, compare_diff: dict[str, Any] | None = None) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    ranked_risks = sorted(
        snapshot.risk_flags,
        key=lambda r: ({"high": 3, "med": 2, "low": 1}[r.severity], r.confidence),
        reverse=True,
    )
    lines = [
        "# Producer Analysis Memo",
        "",
        "## HEURISTIC AND LIMITATION NOTICE (REQUIRED)",
        "This analysis includes deterministic rules and explicitly labeled heuristic indicators.",
        "Do not treat heuristic outputs, mock inputs, or placeholders as market-rate truth.",
        "",
        "## 1) Executive summary",
        f"- Project: `{snapshot.project_id}`",
        f"- Snapshot: `{snapshot.snapshot_id}`",
        f"- Total risks: {len(snapshot.risk_flags)}",
        f"- Total recommendations: {len(snapshot.recommendations)}",
        "",
        "## 2) Top risks (severity then confidence)",
    ]
    for risk in ranked_risks:
        lines.extend(
            [
                f"- **{risk.risk_id}** [{risk.severity} | confidence {risk.confidence:.2f}]",
                f"  - category: {risk.category}",
                f"  - rationale: {risk.rationale}",
                f"  - evidence: {', '.join(risk.evidence_refs)}",
                f"  - assumptions_used: {', '.join(risk.assumptions_used) if risk.assumptions_used else 'none'}",
                f"  - heuristic: {risk.is_heuristic}",
                f"  - limitations: {', '.join(risk.limitations) if risk.limitations else 'none'}",
            ]
        )

    lines.extend(["", "## 3) Recommended actions"])
    for rec in sorted(snapshot.recommendations, key=lambda x: x.recommendation_id):
        lines.extend(
            [
                f"- **{rec.title}** ({rec.recommendation_id})",
                f"  - rationale: {rec.rationale}",
                f"  - upside: {rec.expected_upside}",
                f"  - downside: {rec.expected_downside}",
                f"  - assumptions_used: {', '.join(rec.assumptions_used) if rec.assumptions_used else 'none'}",
                f"  - confidence: {rec.confidence:.2f}",
            ]
        )

    lines.extend(["", "## 4) Assumptions and confidence", "| assumption_id | source_type | confidence | title |", "|---|---:|---:|---|"])
    for assumption in sorted(snapshot.assumptions, key=lambda x: x.assumption_id):
        lines.append(f"| {assumption.assumption_id} | {assumption.source_type} | {assumption.confidence:.2f} | {assumption.title} |")

    lines.extend(["", "## 5) What changed since last snapshot"])
    lines.append(summarize_diff(compare_diff) if compare_diff else "No snapshot comparison provided.")

    lines.extend(
        [
            "",
            "## 6) Known limitations",
            "- Heuristic flags are deterministic proxies, not schedule-verified outcomes.",
            "- Outputs depend on available scene/budget inputs and assumption quality.",
            "",
            "## 7) Provenance",
            f"- parser_version: {snapshot.parser_version}",
            f"- scoring_version: {snapshot.scoring_version}",
            f"- source_files: {', '.join(snapshot.source_files) if snapshot.source_files else 'none'}",
            f"- created_at: {snapshot.created_at}",
        ]
    )

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output

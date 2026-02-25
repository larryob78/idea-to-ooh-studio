from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from producer_amplifier.analysis.compare import compare_snapshots
from producer_amplifier.analysis.engine import analyze_project
from producer_amplifier.analysis.exports import export_memo_markdown, export_risks_csv
from producer_amplifier.analysis.ingest import ingest_project_inputs
from producer_amplifier.analysis.types import Assumption, BudgetLineItem, Project, ScriptScene

from .db import get_conn
from .storage import hash_bytes, make_signed_token, read_blob, write_blob


APP_VERSION = "0.6.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_defaults(org_id: str, user_id: str) -> None:
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO organizations(id,name) VALUES (?,?)", (org_id, org_id))
        conn.execute("INSERT OR IGNORE INTO users(id,email) VALUES (?,?)", (user_id, f"{user_id}@local"))
        conn.execute(
            "INSERT OR IGNORE INTO memberships(id,org_id,user_id,role) VALUES (?,?,?,?)",
            (f"m-{org_id}-{user_id}", org_id, user_id, "owner"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO plans(id,code,max_projects,max_collaborators,max_storage_gb,max_jobs_per_day,max_exports_per_day) VALUES (?,?,?,?,?,?,?)",
            ("plan-pro", "pro", 10, 20, 10, 200, 200),
        )
        conn.execute(
            "INSERT OR IGNORE INTO plans(id,code,max_projects,max_collaborators,max_storage_gb,max_jobs_per_day,max_exports_per_day) VALUES (?,?,?,?,?,?,?)",
            ("plan-studio", "studio", 100, 200, 100, 5000, 5000),
        )
        conn.execute(
            "INSERT OR IGNORE INTO subscriptions(id,org_id,plan_id,status) VALUES (?,?,?,?)",
            (f"sub-{org_id}", org_id, "plan-pro", "active"),
        )


def create_project(org_id: str, name: str) -> dict[str, Any]:
    slug = "-".join(name.lower().split())
    pid = f"prj-{uuid.uuid4().hex[:10]}"
    with get_conn() as conn:
        conn.execute("INSERT INTO projects(id,org_id,name,slug) VALUES (?,?,?,?)", (pid, org_id, name, slug))
    return {"id": pid, "org_id": org_id, "name": name, "slug": slug}


def list_projects(org_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id,org_id,name,slug,created_at FROM projects WHERE org_id=? AND deleted_at IS NULL ORDER BY created_at DESC", (org_id,)).fetchall()
    return [dict(row) for row in rows]


def get_project(org_id: str, project_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT id,org_id,name,slug,created_at FROM projects WHERE id=? AND org_id=? AND deleted_at IS NULL", (project_id, org_id)).fetchone()
    if not row:
        raise KeyError("Project not found")
    return dict(row)


def record_audit(org_id: str, project_id: str | None, action: str, details: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log_events(id,org_id,project_id,action,details_json) VALUES (?,?,?,?,?)",
            (f"aud-{uuid.uuid4().hex[:10]}", org_id, project_id, action, json.dumps(details, sort_keys=True)),
        )


def add_upload(org_id: str, project_id: str, file_type: str, filename: str, content: bytes, created_by: str) -> dict[str, Any]:
    uid = f"upl-{uuid.uuid4().hex[:12]}"
    sha = hash_bytes(content)
    key = f"{org_id}/{project_id}/uploads/{uid}-{filename}"
    write_blob(key, content)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO uploads(id,org_id,project_id,file_type,filename,storage_key,sha256,size_bytes,created_by) VALUES (?,?,?,?,?,?,?,?,?)",
            (uid, org_id, project_id, file_type, filename, key, sha, len(content), created_by),
        )
    record_audit(org_id, project_id, "upload_created", {"upload_id": uid, "file_type": file_type, "sha256": sha})
    return {"id": uid, "file_type": file_type, "filename": filename, "sha256": sha, "size_bytes": len(content)}


def list_uploads(org_id: str, project_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id,file_type,filename,sha256,size_bytes,created_at FROM uploads WHERE org_id=? AND project_id=? ORDER BY created_at DESC", (org_id, project_id)).fetchall()
    return [dict(row) for row in rows]


def _uploads_by_type(org_id: str, project_id: str) -> dict[str, dict[str, Any]]:
    uploads = list_uploads(org_id, project_id)
    return {u["file_type"]: u for u in uploads}


def _upload_storage_key(org_id: str, project_id: str, file_type: str) -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT storage_key FROM uploads WHERE org_id=? AND project_id=? AND file_type=? ORDER BY created_at DESC LIMIT 1", (org_id, project_id, file_type)).fetchone()
    if not row:
        raise KeyError(f"Missing upload for {file_type}")
    return row["storage_key"]


def _save_artifact(org_id: str, project_id: str, artifact_type: str, data: bytes, snapshot_id: str | None = None) -> dict[str, Any]:
    aid = f"art-{uuid.uuid4().hex[:12]}"
    key = f"{org_id}/{project_id}/artifacts/{aid}-{artifact_type}"
    write_blob(key, data)
    meta = {"sha256": hash_bytes(data), "size_bytes": len(data), "app_version": APP_VERSION}
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO artifacts(id,org_id,project_id,snapshot_id,artifact_type,storage_key,metadata_json) VALUES (?,?,?,?,?,?,?)",
            (aid, org_id, project_id, snapshot_id, artifact_type, key, json.dumps(meta, sort_keys=True)),
        )
    return {"id": aid, "artifact_type": artifact_type, "storage_key": key, "metadata": meta}


def list_artifacts(org_id: str, project_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id,artifact_type,snapshot_id,metadata_json,created_at FROM artifacts WHERE org_id=? AND project_id=? ORDER BY created_at DESC", (org_id, project_id)).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json"))
        item["signed_token"] = make_signed_token(item["id"])
        out.append(item)
    return out


def get_artifact_bytes(org_id: str, artifact_id: str) -> bytes:
    with get_conn() as conn:
        row = conn.execute("SELECT storage_key,org_id FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
    if not row or row["org_id"] != org_id:
        raise KeyError("Artifact not found")
    return read_blob(row["storage_key"])


def add_assumption(org_id: str, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    asm = Assumption(
        assumption_id=f"asm-{uuid.uuid4().hex[:10]}",
        title=payload["title"],
        description=payload["description"],
        source_type=payload["source_type"],
        confidence=float(payload["confidence"]),
        evidence_refs=payload.get("evidence_refs", []),
        limitations=payload.get("limitations", []),
    )
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO assumptions(id,org_id,project_id,title,description,source_type,confidence,evidence_refs_json,limitations_json) VALUES (?,?,?,?,?,?,?,?,?)",
            (asm.assumption_id, org_id, project_id, asm.title, asm.description, asm.source_type, asm.confidence, json.dumps(asm.evidence_refs), json.dumps(asm.limitations)),
        )
    return {"id": asm.assumption_id, **payload}


def list_assumptions(org_id: str, project_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id,title,description,source_type,confidence,evidence_refs_json,limitations_json,created_at FROM assumptions WHERE org_id=? AND project_id=? ORDER BY created_at DESC", (org_id, project_id)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["evidence_refs"] = json.loads(d.pop("evidence_refs_json"))
        d["limitations"] = json.loads(d.pop("limitations_json"))
        d["assumptions_used"] = [d["id"]]
        d["is_heuristic"] = d["source_type"] == "heuristic"
        out.append(d)
    return out


def _load_project_from_uploads(org_id: str, project_id: str) -> Project:
    root = Path(".data/tmp") / org_id / project_id
    root.mkdir(parents=True, exist_ok=True)
    script_key = _upload_storage_key(org_id, project_id, "script")
    budget_key = _upload_storage_key(org_id, project_id, "budget")
    schedule = None
    try:
        schedule_key = _upload_storage_key(org_id, project_id, "schedule")
        schedule = root / "schedule.csv"
        schedule.write_bytes(read_blob(schedule_key))
    except KeyError:
        schedule = None
    script_path = root / "script.csv"
    budget_path = root / "budget.csv"
    script_path.write_bytes(read_blob(script_key))
    budget_path.write_bytes(read_blob(budget_key))
    report = ingest_project_inputs(project_id, script_path, budget_path, schedule, root)
    payload = json.loads((root / "config" / "project_data.json").read_text(encoding="utf-8"))["project"]
    project = Project(
        project_id=payload["project_id"],
        title=payload["title"],
        scenes=[ScriptScene(**x) for x in payload["scenes"]],
        budget_items=[BudgetLineItem(**x) for x in payload["budget_items"]],
    )
    _save_artifact(org_id, project_id, "ingest_report.json", json.dumps(report, indent=2, sort_keys=True).encode())
    return project


def create_job(org_id: str, project_id: str, job_type: str, payload: dict[str, Any], idempotency_key: str | None = None) -> dict[str, Any]:
    jid = f"job-{uuid.uuid4().hex[:12]}"
    with get_conn() as conn:
        if idempotency_key:
            existing = conn.execute(
                "SELECT id,status,result_json FROM jobs WHERE org_id=? AND project_id=? AND type=? AND idempotency_key=?",
                (org_id, project_id, job_type, idempotency_key),
            ).fetchone()
            if existing:
                return {"id": existing["id"], "status": existing["status"], "idempotent_reuse": True}
        conn.execute(
            "INSERT INTO jobs(id,org_id,project_id,type,status,idempotency_key,payload_json) VALUES (?,?,?,?,?,?,?)",
            (jid, org_id, project_id, job_type, "queued", idempotency_key, json.dumps(payload, sort_keys=True)),
        )
    run_job(jid)
    return get_job(org_id, jid)


def get_job(org_id: str, job_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=? AND org_id=?", (job_id, org_id)).fetchone()
    if not row:
        raise KeyError("Job not found")
    d = dict(row)
    d["payload"] = json.loads(d.pop("payload_json"))
    d["result"] = json.loads(d.pop("result_json")) if d.get("result_json") else None
    return d


def run_job(job_id: str) -> None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        return
    job = dict(row)
    payload = json.loads(job["payload_json"])
    status = "running"
    result: dict[str, Any] | None = None
    error = None
    try:
        if job["type"] == "ingest":
            _load_project_from_uploads(job["org_id"], job["project_id"])
            result = {"ingested": True}
        elif job["type"] == "analyze":
            project = _load_project_from_uploads(job["org_id"], job["project_id"])
            risks, recs, summary = analyze_project(project)
            assumptions = list_assumptions(job["org_id"], job["project_id"])
            snapshot_id = f"snp-{uuid.uuid4().hex[:10]}"
            snap = {
                "snapshot_id": snapshot_id,
                "project_id": job["project_id"],
                "risk_flags": [r.__dict__ for r in risks],
                "recommendations": [r.__dict__ for r in recs],
                "summary_metrics": summary,
                "assumptions": assumptions,
                "provenance": {"app_version": APP_VERSION, "timestamp": _now()},
            }
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO snapshots(id,org_id,project_id,summary_metrics_json,data_json) VALUES (?,?,?,?,?)",
                    (snapshot_id, job["org_id"], job["project_id"], json.dumps(summary), json.dumps(snap)),
                )
            _save_artifact(job["org_id"], job["project_id"], "analysis_snapshot.json", json.dumps(snap, indent=2, sort_keys=True).encode(), snapshot_id=snapshot_id)
            result = {"snapshot_id": snapshot_id, "summary": summary}
        elif job["type"] == "snapshot":
            result = {"ok": True}
        elif job["type"] == "compare":
            with get_conn() as conn:
                a = conn.execute("SELECT data_json FROM snapshots WHERE id=? AND org_id=?", (payload["a"], job["org_id"])).fetchone()
                b = conn.execute("SELECT data_json FROM snapshots WHERE id=? AND org_id=?", (payload["b"], job["org_id"])).fetchone()
            da, db = json.loads(a["data_json"]), json.loads(b["data_json"])
            # compatible compare using previous diff function structure
            class _S: pass
            sa = _S(); sb = _S()
            sa.snapshot_id = da["snapshot_id"]; sb.snapshot_id = db["snapshot_id"]
            sa.summary_metrics = da["summary_metrics"]; sb.summary_metrics = db["summary_metrics"]
            sa.risk_flags = []; sb.risk_flags = []
            sa.recommendations = []; sb.recommendations = []
            sa.assumptions = []; sb.assumptions = []
            diff = {"snapshot_a": payload["a"], "snapshot_b": payload["b"], "summary_only": True, "metric_deltas": {k: {"from": da["summary_metrics"].get(k), "to": db["summary_metrics"].get(k)} for k in sorted(set(da["summary_metrics"])|set(db["summary_metrics"]))}}
            _save_artifact(job["org_id"], job["project_id"], "snapshot_diff.json", json.dumps(diff, indent=2, sort_keys=True).encode())
            result = diff
        elif job["type"] == "export":
            with get_conn() as conn:
                s = conn.execute("SELECT data_json,id FROM snapshots WHERE org_id=? AND project_id=? ORDER BY created_at DESC LIMIT 1", (job["org_id"], job["project_id"])).fetchone()
            if not s:
                raise ValueError("No snapshot available")
            data = json.loads(s["data_json"])
            _save_artifact(job["org_id"], job["project_id"], "project_summary.json", json.dumps(data, indent=2, sort_keys=True).encode(), snapshot_id=s["id"])
            result = {"exported": True}
        status = "succeeded"
    except Exception as exc:
        error = str(exc)
        retries = int(job.get("retries", 0)) + 1
        if retries > int(job.get("max_retries", 3)):
            status = "dead-letter"
        else:
            status = "failed"
        with get_conn() as conn:
            conn.execute("UPDATE jobs SET retries=?, dead_letter=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (retries, 1 if status == "dead-letter" else 0, job_id))
    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET status=?, result_json=?, error_message=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, json.dumps(result, sort_keys=True) if result is not None else None, error, job_id),
        )
    record_audit(job["org_id"], job["project_id"], f"job_{job['type']}_{status}", {"job_id": job_id})


def list_snapshots(org_id: str, project_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id,created_at,summary_metrics_json FROM snapshots WHERE org_id=? AND project_id=? ORDER BY created_at DESC", (org_id, project_id)).fetchall()
    return [{"id": r["id"], "created_at": r["created_at"], "summary_metrics": json.loads(r["summary_metrics_json"])} for r in rows]


def get_snapshot(org_id: str, snapshot_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT data_json FROM snapshots WHERE id=? AND org_id=?", (snapshot_id, org_id)).fetchone()
    if not row:
        raise KeyError("Snapshot not found")
    return json.loads(row["data_json"])


def org_usage(org_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        projects = conn.execute("SELECT COUNT(*) c FROM projects WHERE org_id=? AND deleted_at IS NULL", (org_id,)).fetchone()["c"]
        jobs_today = conn.execute("SELECT COUNT(*) c FROM jobs WHERE org_id=? AND date(created_at)=date('now')", (org_id,)).fetchone()["c"]
        exports_today = conn.execute("SELECT COUNT(*) c FROM artifacts WHERE org_id=? AND artifact_type LIKE '%csv%' AND date(created_at)=date('now')", (org_id,)).fetchone()["c"]
        sub = conn.execute("SELECT plan_id,status FROM subscriptions WHERE org_id=?", (org_id,)).fetchone()
        plan = conn.execute("SELECT * FROM plans WHERE id=?", (sub["plan_id"],)).fetchone() if sub else None
    return {
        "org_id": org_id,
        "projects": projects,
        "jobs_today": jobs_today,
        "exports_today": exports_today,
        "plan": dict(plan) if plan else None,
        "subscription_status": sub["status"] if sub else "none",
    }


def enforce_entitlement(org_id: str, kind: str) -> None:
    usage = org_usage(org_id)
    plan = usage.get("plan") or {}
    if kind == "projects" and usage["projects"] >= int(plan.get("max_projects", 0)):
        raise PermissionError("Project limit reached")
    if kind == "jobs" and usage["jobs_today"] >= int(plan.get("max_jobs_per_day", 0)):
        raise PermissionError("Daily job limit reached")


def stripe_webhook(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    org_id = payload.get("metadata", {}).get("org_id")
    if not org_id:
        return {"ok": False, "message": "missing org_id"}
    with get_conn() as conn:
        if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
            plan_id = payload.get("metadata", {}).get("plan_id", "plan-pro")
            conn.execute(
                "INSERT INTO subscriptions(id,org_id,plan_id,status,stripe_customer_id,stripe_subscription_id) VALUES (?,?,?,?,?,?) ON CONFLICT(org_id) DO UPDATE SET plan_id=excluded.plan_id,status=excluded.status,stripe_customer_id=excluded.stripe_customer_id,stripe_subscription_id=excluded.stripe_subscription_id,updated_at=CURRENT_TIMESTAMP",
                (f"sub-{org_id}", org_id, plan_id, payload.get("status", "active"), payload.get("customer_id"), payload.get("subscription_id")),
            )
        elif event_type == "customer.subscription.deleted":
            conn.execute("UPDATE subscriptions SET status='canceled', updated_at=CURRENT_TIMESTAMP WHERE org_id=?", (org_id,))
    return {"ok": True}


def gdpr_export_project(org_id: str, project_id: str) -> dict[str, Any]:
    return {
        "project": get_project(org_id, project_id),
        "uploads": list_uploads(org_id, project_id),
        "assumptions": list_assumptions(org_id, project_id),
        "snapshots": list_snapshots(org_id, project_id),
        "artifacts": list_artifacts(org_id, project_id),
    }


def gdpr_delete_project(org_id: str, project_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        conn.execute("UPDATE projects SET deleted_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=? AND org_id=?", (project_id, org_id))
        conn.execute("DELETE FROM uploads WHERE org_id=? AND project_id=?", (org_id, project_id))
        conn.execute("DELETE FROM assumptions WHERE org_id=? AND project_id=?", (org_id, project_id))
        conn.execute("DELETE FROM snapshots WHERE org_id=? AND project_id=?", (org_id, project_id))
        conn.execute("DELETE FROM artifacts WHERE org_id=? AND project_id=?", (org_id, project_id))
    record_audit(org_id, project_id, "gdpr_delete_project", {"deleted": True})
    return {"deleted": True, "project_id": project_id}

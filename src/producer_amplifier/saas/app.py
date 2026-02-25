from __future__ import annotations

import json
import os
import uuid
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from .db import init_db
from .security import AuthContext, allowed_origins, enforce_rate_limit, require_auth, require_role
from .service import (
    add_assumption,
    add_upload,
    create_job,
    create_project,
    enforce_entitlement,
    gdpr_delete_project,
    gdpr_export_project,
    get_artifact_bytes,
    get_job,
    get_project,
    get_snapshot,
    list_artifacts,
    list_assumptions,
    list_projects,
    list_snapshots,
    list_uploads,
    org_usage,
    seed_defaults,
    stripe_webhook,
)
from .storage import verify_signed_token

app = FastAPI(title="Producer Amplifier SaaS v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", f"req-{uuid.uuid4().hex[:10]}")
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    return response


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "producer-amplifier-saas"}


def _ctx(request: Request, ctx: AuthContext = Depends(require_auth)) -> AuthContext:
    enforce_rate_limit(request, ctx)
    seed_defaults(ctx.org_id, ctx.user_id)
    return ctx


@app.get("/api/org")
def get_org(ctx: AuthContext = Depends(_ctx)):
    return {"org_id": ctx.org_id, "user_id": ctx.user_id, "role": ctx.role}


@app.get("/api/org/usage")
def get_org_usage(ctx: AuthContext = Depends(_ctx)):
    return org_usage(ctx.org_id)


@app.get("/api/projects")
def api_list_projects(ctx: AuthContext = Depends(_ctx)):
    return list_projects(ctx.org_id)


@app.post("/api/projects")
def api_create_project(payload: dict, ctx: AuthContext = Depends(_ctx)):
    if ctx.role not in {"owner", "admin", "editor"}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    try:
        enforce_entitlement(ctx.org_id, "projects")
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return create_project(ctx.org_id, payload["name"])


@app.get("/api/projects/{project_id}")
def api_get_project(project_id: str, ctx: AuthContext = Depends(_ctx)):
    try:
        return get_project(ctx.org_id, project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/uploads")
async def api_upload(project_id: str, file_type: str, file: UploadFile = File(...), ctx: AuthContext = Depends(_ctx)):
    if file_type not in {"script", "budget", "schedule", "quotes"}:
        raise HTTPException(status_code=400, detail="Unsupported file_type")
    data = await file.read()
    max_size = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    if len(data) > max_size:
        raise HTTPException(status_code=413, detail="File too large")
    return add_upload(ctx.org_id, project_id, file_type, file.filename, data, ctx.user_id)


@app.get("/api/projects/{project_id}/uploads")
def api_list_uploads(project_id: str, ctx: AuthContext = Depends(_ctx)):
    return list_uploads(ctx.org_id, project_id)


@app.get("/api/projects/{project_id}/assumptions")
def api_list_assumptions(project_id: str, ctx: AuthContext = Depends(_ctx)):
    return list_assumptions(ctx.org_id, project_id)


@app.post("/api/projects/{project_id}/assumptions")
def api_add_assumption(project_id: str, payload: dict, ctx: AuthContext = Depends(_ctx)):
    return add_assumption(ctx.org_id, project_id, payload)


@app.get("/api/projects/{project_id}/snapshots")
def api_list_snapshots(project_id: str, ctx: AuthContext = Depends(_ctx)):
    return list_snapshots(ctx.org_id, project_id)


@app.get("/api/snapshots/{snapshot_id}")
def api_get_snapshot(snapshot_id: str, ctx: AuthContext = Depends(_ctx)):
    try:
        return get_snapshot(ctx.org_id, snapshot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/jobs/ingest")
def api_job_ingest(project_id: str, request: Request, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return create_job(ctx.org_id, project_id, "ingest", {}, idempotency_key=idempotency_key)


@app.post("/api/projects/{project_id}/jobs/analyze")
def api_job_analyze(project_id: str, request: Request, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    try:
        enforce_entitlement(ctx.org_id, "jobs")
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return create_job(ctx.org_id, project_id, "analyze", {}, idempotency_key=idempotency_key)


@app.post("/api/projects/{project_id}/jobs/snapshot")
def api_job_snapshot(project_id: str, payload: dict, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return create_job(ctx.org_id, project_id, "snapshot", payload, idempotency_key=idempotency_key)


@app.post("/api/projects/{project_id}/jobs/compare")
def api_job_compare(project_id: str, payload: dict, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return create_job(ctx.org_id, project_id, "compare", payload, idempotency_key=idempotency_key)


@app.post("/api/projects/{project_id}/jobs/export")
def api_job_export(project_id: str, payload: dict, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return create_job(ctx.org_id, project_id, "export", payload, idempotency_key=idempotency_key)


@app.get("/api/jobs/{job_id}")
def api_job_get(job_id: str, ctx: AuthContext = Depends(_ctx)):
    try:
        return get_job(ctx.org_id, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/projects/{project_id}/artifacts")
def api_artifacts(project_id: str, ctx: AuthContext = Depends(_ctx)):
    return list_artifacts(ctx.org_id, project_id)


@app.get("/api/artifacts/{artifact_id}")
def api_artifact_download(artifact_id: str, token: str, ctx: AuthContext = Depends(_ctx)):
    validated = verify_signed_token(token)
    if validated != artifact_id:
        raise HTTPException(status_code=403, detail="Invalid signed token")
    try:
        data = get_artifact_bytes(ctx.org_id, artifact_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=data, media_type="application/octet-stream")


@app.post("/api/projects/{project_id}/compare")
def api_compare_inline(project_id: str, payload: dict, ctx: AuthContext = Depends(_ctx)):
    return create_job(ctx.org_id, project_id, "compare", payload)


@app.get("/api/projects/{project_id}/risks")
def api_risks(project_id: str, ctx: AuthContext = Depends(_ctx)):
    snaps = list_snapshots(ctx.org_id, project_id)
    if not snaps:
        return []
    data = get_snapshot(ctx.org_id, snaps[0]["id"])
    return data.get("risk_flags", [])


@app.get("/api/projects/{project_id}/recommendations")
def api_recommendations(project_id: str, ctx: AuthContext = Depends(_ctx)):
    snaps = list_snapshots(ctx.org_id, project_id)
    if not snaps:
        return []
    data = get_snapshot(ctx.org_id, snaps[0]["id"])
    return data.get("recommendations", [])


@app.post("/api/billing/stripe/webhook")
def api_stripe_webhook(payload: dict):
    event_type = payload.get("type", "")
    data = payload.get("data", {})
    return stripe_webhook(event_type, data)


@app.post("/api/projects/{project_id}/gdpr/export")
def api_gdpr_export(project_id: str, ctx: AuthContext = Depends(_ctx)):
    return gdpr_export_project(ctx.org_id, project_id)


@app.delete("/api/projects/{project_id}")
def api_delete_project(project_id: str, ctx: AuthContext = Depends(_ctx)):
    if ctx.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return gdpr_delete_project(ctx.org_id, project_id)


@app.get("/api/admin/diagnostics")
def api_admin_diag(ctx: AuthContext = Depends(_ctx)):
    if ctx.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    usage = org_usage(ctx.org_id)
    return {
        "recent_job_failures": [],
        "queue_depth": 0,
        "slow_endpoints": [],
        "storage_usage": usage,
        "plan_usage_counters": usage,
    }


@app.get("/metrics")
def metrics(ctx: AuthContext = Depends(_ctx)):
    usage = org_usage(ctx.org_id)
    body = "\n".join(
        [
            f"producer_projects_total {usage['projects']}",
            f"producer_jobs_today {usage['jobs_today']}",
            f"producer_exports_today {usage['exports_today']}",
        ]
    )
    return Response(content=body + "\n", media_type="text/plain")


@app.get("/app/login", response_class=HTMLResponse)
def ui_login():
    return "<html><body><h1>Login</h1><p>Use dev bearer token format: dev-&lt;user&gt;:&lt;org&gt;:&lt;role&gt;</p></body></html>"


@app.get("/app/projects", response_class=HTMLResponse)
def ui_projects():
    return "<html><body><h1>Projects</h1><p>Use /api/projects endpoints for CRUD.</p></body></html>"


@app.get("/app/projects/{project_id}", response_class=HTMLResponse)
def ui_project_detail(project_id: str):
    return f"<html><body><h1>Project {project_id}</h1><ul><li>Uploads</li><li>Ingest report</li><li>Jobs</li><li>Risks/Recommendations</li><li>Assumptions</li><li>Snapshots</li><li>Compare</li><li>Exports</li><li>Audit Log</li></ul></body></html>"

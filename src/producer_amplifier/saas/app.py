from __future__ import annotations

import uuid
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from .db import init_db
from .security import AuthContext, allowed_origins, enforce_rate_limit, require_auth
from .service import (
    accept_invite,
    add_assumption,
    add_upload,
    create_invite,
    create_job,
    create_org,
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
    list_invites,
    list_members,
    list_notifications,
    list_projects,
    list_snapshots,
    list_uploads,
    mark_notification_read,
    org_usage,
    rerun_job,
    seed_defaults,
    stripe_webhook,
    support_bundle,
    update_member_role,
    wizard_status,
)
from .storage import verify_signed_token

app = FastAPI(title="Producer Amplifier SaaS v1")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


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


@app.post("/api/onboarding/org")
def api_create_org(payload: dict, ctx: AuthContext = Depends(_ctx)):
    return create_org(payload["name"], ctx.user_id, payload.get("email", f"{ctx.user_id}@local"))


@app.get("/api/org")
def get_org(ctx: AuthContext = Depends(_ctx)):
    return {"org_id": ctx.org_id, "user_id": ctx.user_id, "role": ctx.role}


@app.get("/api/org/usage")
def get_org_usage(ctx: AuthContext = Depends(_ctx)):
    return org_usage(ctx.org_id)


@app.get("/api/org/members")
def api_members(ctx: AuthContext = Depends(_ctx)):
    return list_members(ctx.org_id)


@app.patch("/api/org/members/{user_id}/role")
def api_member_role(user_id: str, payload: dict, ctx: AuthContext = Depends(_ctx)):
    try:
        return update_member_role(ctx.org_id, ctx.role, user_id, payload["role"])
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/api/org/invites")
def api_invite(payload: dict, ctx: AuthContext = Depends(_ctx)):
    try:
        return create_invite(ctx.org_id, ctx.role, payload["email"], payload["role"], ctx.user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.get("/api/org/invites")
def api_list_invites(ctx: AuthContext = Depends(_ctx)):
    return list_invites(ctx.org_id)


@app.post("/api/onboarding/accept-invite")
def api_accept_invite(payload: dict):
    try:
        return accept_invite(payload["token"], payload["user_id"], payload.get("email", f"{payload['user_id']}@local"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/notifications")
def api_notifications(ctx: AuthContext = Depends(_ctx)):
    return list_notifications(ctx.org_id, ctx.user_id)


@app.post("/api/notifications/{notification_id}/read")
def api_notification_read(notification_id: str, ctx: AuthContext = Depends(_ctx)):
    return mark_notification_read(ctx.org_id, ctx.user_id, notification_id)


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


@app.get("/api/projects/{project_id}/wizard")
def api_wizard(project_id: str, ctx: AuthContext = Depends(_ctx)):
    return wizard_status(ctx.org_id, project_id)


@app.post("/api/projects/{project_id}/wizard/continue")
def api_wizard_continue(project_id: str, payload: dict, ctx: AuthContext = Depends(_ctx)):
    status = wizard_status(ctx.org_id, project_id)
    if status["continue_requires_ack"] and not payload.get("acknowledge_warnings"):
        raise HTTPException(status_code=400, detail="Ingest warnings require explicit acknowledgement")
    return {"continued": True, "wizard": status}


@app.post("/api/projects/{project_id}/uploads")
async def api_upload(project_id: str, file_type: str, file: UploadFile = File(...), ctx: AuthContext = Depends(_ctx)):
    if file_type not in {"script", "budget", "schedule", "quotes"}:
        raise HTTPException(status_code=400, detail="Unsupported file_type")
    data = await file.read()
    if len(data) > int((__import__("os").getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))):
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


def _job(project_id: str, job_type: str, payload: dict, idempotency_key: str | None, ctx: AuthContext):
    try:
        if job_type in {"analyze", "export"}:
            enforce_entitlement(ctx.org_id, "jobs")
        return create_job(ctx.org_id, project_id, job_type, payload, idempotency_key=idempotency_key, actor_user_id=ctx.user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/jobs/ingest")
def api_job_ingest(project_id: str, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return _job(project_id, "ingest", {}, idempotency_key, ctx)


@app.post("/api/projects/{project_id}/jobs/analyze")
def api_job_analyze(project_id: str, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return _job(project_id, "analyze", {}, idempotency_key, ctx)


@app.post("/api/projects/{project_id}/jobs/snapshot")
def api_job_snapshot(project_id: str, payload: dict, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return _job(project_id, "snapshot", payload, idempotency_key, ctx)


@app.post("/api/projects/{project_id}/jobs/compare")
def api_job_compare(project_id: str, payload: dict, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return _job(project_id, "compare", payload, idempotency_key, ctx)


@app.post("/api/projects/{project_id}/jobs/export")
def api_job_export(project_id: str, payload: dict, idempotency_key: str | None = Header(default=None), ctx: AuthContext = Depends(_ctx)):
    return _job(project_id, "export", payload, idempotency_key, ctx)


@app.get("/api/jobs/{job_id}")
def api_job_get(job_id: str, ctx: AuthContext = Depends(_ctx)):
    try:
        return get_job(ctx.org_id, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/jobs/{job_id}/rerun")
def api_job_rerun(job_id: str, ctx: AuthContext = Depends(_ctx)):
    try:
        return rerun_job(ctx.org_id, job_id, actor_user_id=ctx.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/projects/{project_id}/artifacts")
def api_artifacts(project_id: str, ctx: AuthContext = Depends(_ctx)):
    return list_artifacts(ctx.org_id, project_id)


@app.get("/api/artifacts/{artifact_id}")
def api_artifact_download(artifact_id: str, token: str, ctx: AuthContext = Depends(_ctx)):
    if verify_signed_token(token) != artifact_id:
        raise HTTPException(status_code=403, detail="Invalid signed token")
    try:
        data = get_artifact_bytes(ctx.org_id, artifact_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=data, media_type="application/octet-stream")


@app.post("/api/projects/{project_id}/support-bundle")
def api_support_bundle(project_id: str, ctx: AuthContext = Depends(_ctx)):
    if ctx.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    name, data = support_bundle(ctx.org_id, project_id)
    return Response(content=data, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename={name}"})


@app.get("/api/projects/{project_id}/risks")
def api_risks(project_id: str, ctx: AuthContext = Depends(_ctx)):
    snaps = list_snapshots(ctx.org_id, project_id)
    return [] if not snaps else get_snapshot(ctx.org_id, snaps[0]["id"]).get("risk_flags", [])


@app.get("/api/projects/{project_id}/recommendations")
def api_recommendations(project_id: str, ctx: AuthContext = Depends(_ctx)):
    snaps = list_snapshots(ctx.org_id, project_id)
    return [] if not snaps else get_snapshot(ctx.org_id, snaps[0]["id"]).get("recommendations", [])


@app.post("/api/billing/stripe/webhook")
def api_stripe_webhook(payload: dict):
    return stripe_webhook(payload.get("type", ""), payload.get("data", {}))


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
    return {"recent_job_failures": usage["job_failures"], "queue_depth": 0, "slow_endpoints": [{"path": "/api/projects/{id}/jobs/analyze", "p95_ms": 1200}], "storage_usage": {"bytes": usage["storage_bytes"]}, "plan_usage_counters": usage}


@app.get("/metrics")
def metrics(ctx: AuthContext = Depends(_ctx)):
    u = org_usage(ctx.org_id)
    return Response(content=f"producer_projects_total {u['projects']}\nproducer_jobs_today {u['jobs_today']}\nproducer_exports_today {u['exports_today']}\n", media_type="text/plain")


@app.get("/app/login", response_class=HTMLResponse)
def ui_login():
    return "<html><body><h1>Login</h1><p>Use dev token: dev-&lt;user&gt;:&lt;org&gt;:&lt;role&gt;</p></body></html>"


@app.get("/app/org/settings", response_class=HTMLResponse)
def ui_org_settings():
    return "<html><body><h1>Org Settings</h1><ul><li>Members list</li><li>Invite member</li><li>Role management</li></ul></body></html>"


@app.get("/app/projects", response_class=HTMLResponse)
def ui_projects():
    return "<html><body><h1>Projects</h1><p>Create Project Wizard available from project detail.</p></body></html>"


@app.get("/app/projects/{project_id}", response_class=HTMLResponse)
def ui_project_detail(project_id: str):
    return f"<html><body><h1>Project {project_id}</h1><h2>Create Project Wizard</h2><ol><li>Create project</li><li>Upload script/budget</li><li>Review ingest warnings</li><li>Run analysis</li><li>Review risks/recommendations</li><li>Create snapshot</li><li>Export memo/register</li></ol><h2>How to interpret results</h2><p>Confidence reflects evidence support level; heuristic items are clearly marked.</p><h2>Limitations</h2><p>Heuristic outputs are proxies; validate with production context.</p><h2>Data provenance</h2><p>Inputs and versions shown in snapshot provenance.</p></body></html>"

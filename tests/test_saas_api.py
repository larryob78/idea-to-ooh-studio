import io
import zipfile
from pathlib import Path

import pytest
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from producer_amplifier.saas.app import app
from producer_amplifier.saas.db import init_db


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'saas.db'}")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    init_db()
    return TestClient(app)


def _auth(role: str = "owner", org: str = "org-a", user: str = "u1"):
    return {"Authorization": f"Bearer dev-{user}:{org}:{role}"}


def _project(client: TestClient) -> str:
    return client.post("/api/projects", json={"name": "Demo"}, headers=_auth()).json()["id"]


def _upload_minimum_inputs(client: TestClient, project_id: str) -> None:
    script = b"scene_id,int_ext,day_night,location_name,page_length,cast_names,tags\n1,EXT,NIGHT,Street,2.0,A|B|C|D|E,stunts|vfx|sfx\n"
    budget = b"account_code,account_name,quantity,unit,rate,total\n500,Misc contingency,1,lot,6000,6000\n"
    client.post(f"/api/projects/{project_id}/uploads?file_type=script", files={"file": ("script.csv", script, "text/csv")}, headers=_auth())
    client.post(f"/api/projects/{project_id}/uploads?file_type=budget", files={"file": ("budget.csv", budget, "text/csv")}, headers=_auth())


def test_invite_flow_access_control(client: TestClient):
    denied = client.post("/api/org/invites", json={"email": "new@x.com", "role": "viewer"}, headers=_auth(role="viewer"))
    assert denied.status_code == 403
    invited = client.post("/api/org/invites", json={"email": "new@x.com", "role": "viewer"}, headers=_auth(role="owner"))
    assert invited.status_code == 200
    token = invited.json()["token"]
    accepted = client.post("/api/onboarding/accept-invite", json={"token": token, "user_id": "u2", "email": "new@x.com"})
    assert accepted.status_code == 200


def test_wizard_step_transitions_smoke(client: TestClient):
    pid = _project(client)
    before = client.get(f"/api/projects/{pid}/wizard", headers=_auth()).json()
    assert before["steps"]["uploads_complete"] is False

    _upload_minimum_inputs(client, pid)
    client.post(f"/api/projects/{pid}/jobs/ingest", headers=_auth())
    after_ingest = client.get(f"/api/projects/{pid}/wizard", headers=_auth()).json()
    assert after_ingest["steps"]["uploads_complete"] is True
    if after_ingest["continue_requires_ack"]:
        blocked = client.post(f"/api/projects/{pid}/wizard/continue", json={"acknowledge_warnings": False}, headers=_auth())
        assert blocked.status_code == 400
        ok = client.post(f"/api/projects/{pid}/wizard/continue", json={"acknowledge_warnings": True}, headers=_auth())
        assert ok.status_code == 200

    client.post(f"/api/projects/{pid}/jobs/analyze", headers=_auth())
    final = client.get(f"/api/projects/{pid}/wizard", headers=_auth()).json()
    assert final["steps"]["analysis_completed"] is True


def test_support_bundle_generation_no_secrets(client: TestClient):
    pid = _project(client)
    _upload_minimum_inputs(client, pid)
    client.post(f"/api/projects/{pid}/jobs/ingest", headers=_auth())
    client.post(f"/api/projects/{pid}/jobs/analyze", headers=_auth())
    resp = client.post(f"/api/projects/{pid}/support-bundle", headers=_auth(role="admin"))
    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = set(zf.namelist())
    assert {"job_records.json", "job_status_history.json", "artifacts_index.json", "versions.json", "environment_summary.json"}.issubset(names)
    env_summary = zf.read("environment_summary.json").decode()
    assert "SIGNED_URL_SECRET" not in env_summary


def test_error_handling_failed_job_and_rerun(client: TestClient):
    pid = _project(client)
    failed = client.post(f"/api/projects/{pid}/jobs/analyze", headers=_auth()).json()
    job = client.get(f"/api/jobs/{failed['id']}", headers=_auth()).json()
    assert job["status"] in {"failed", "dead-letter"}
    assert "recovery" in job
    rerun = client.post(f"/api/jobs/{failed['id']}/rerun", headers=_auth())
    assert rerun.status_code == 200


def test_role_enforcement_for_support_bundle(client: TestClient):
    pid = _project(client)
    _upload_minimum_inputs(client, pid)
    deny = client.post(f"/api/projects/{pid}/support-bundle", headers=_auth(role="viewer"))
    assert deny.status_code == 403


def test_tenant_isolation_still_enforced(client: TestClient):
    pid = _project(client)
    denied = client.get(f"/api/projects/{pid}", headers=_auth(org="org-b"))
    assert denied.status_code == 404

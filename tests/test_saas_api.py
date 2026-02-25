import pytest
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from pathlib import Path


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


def test_health(client: TestClient):
    assert client.get("/healthz").status_code == 200


def test_tenant_isolation(client: TestClient):
    pid = client.post("/api/projects", json={"name": "Alpha"}, headers=_auth(org="org-a")).json()["id"]
    denied = client.get(f"/api/projects/{pid}", headers=_auth(org="org-b"))
    assert denied.status_code == 404


def test_project_upload_ingest_analyze_flow(client: TestClient):
    pid = client.post("/api/projects", json={"name": "Flow"}, headers=_auth()).json()["id"]
    script = b"scene_id,int_ext,day_night,location_name,page_length,cast_names,tags\n1,EXT,NIGHT,Street,2.0,A|B|C|D|E,stunts|vfx|sfx\n"
    budget = b"account_code,account_name,quantity,unit,rate,total\n500,Misc contingency,1,lot,6000,6000\n"
    assert client.post(f"/api/projects/{pid}/uploads?file_type=script", files={"file": ("script.csv", script, "text/csv")}, headers=_auth()).status_code == 200
    assert client.post(f"/api/projects/{pid}/uploads?file_type=budget", files={"file": ("budget.csv", budget, "text/csv")}, headers=_auth()).status_code == 200
    assert client.post(f"/api/projects/{pid}/jobs/ingest", headers={**_auth(), "idempotency-key": "x1"}).status_code == 200
    job_an = client.post(f"/api/projects/{pid}/jobs/analyze", headers={**_auth(), "idempotency-key": "x2"})
    assert job_an.status_code == 200
    status = client.get(f"/api/jobs/{job_an.json()['id']}", headers=_auth()).json()["status"]
    assert status in {"succeeded", "failed", "dead-letter"}


def test_job_idempotency(client: TestClient):
    pid = client.post("/api/projects", json={"name": "Idempotent"}, headers=_auth()).json()["id"]
    script = b"scene_id,int_ext,day_night,location_name\n1,INT,DAY,Office\n"
    budget = b"account_code,account_name,quantity,unit,rate,total\n100,Camera,1,lot,100,100\n"
    client.post(f"/api/projects/{pid}/uploads?file_type=script", files={"file": ("s.csv", script, "text/csv")}, headers=_auth())
    client.post(f"/api/projects/{pid}/uploads?file_type=budget", files={"file": ("b.csv", budget, "text/csv")}, headers=_auth())
    first = client.post(f"/api/projects/{pid}/jobs/ingest", headers={**_auth(), "idempotency-key": "same"}).json()
    second = client.post(f"/api/projects/{pid}/jobs/ingest", headers={**_auth(), "idempotency-key": "same"}).json()
    assert first["id"] == second["id"]


def test_stripe_webhook_mock(client: TestClient):
    payload = {"type": "customer.subscription.updated", "data": {"status": "active", "customer_id": "cus_123", "subscription_id": "sub_123", "metadata": {"org_id": "org-a", "plan_id": "plan-studio"}}}
    assert client.post("/api/billing/stripe/webhook", json=payload).json()["ok"] is True


def test_gdpr_export_delete(client: TestClient):
    pid = client.post("/api/projects", json={"name": "GDPR"}, headers=_auth()).json()["id"]
    assert client.post(f"/api/projects/{pid}/gdpr/export", headers=_auth()).status_code == 200
    assert client.delete(f"/api/projects/{pid}", headers=_auth()).status_code == 200


def test_artifact_access_control(client: TestClient):
    pid = client.post("/api/projects", json={"name": "Artifacts"}, headers=_auth()).json()["id"]
    script = b"scene_id,int_ext,day_night,location_name\n1,INT,DAY,Office\n"
    budget = b"account_code,account_name,quantity,unit,rate,total\n100,Camera,1,lot,100,100\n"
    client.post(f"/api/projects/{pid}/uploads?file_type=script", files={"file": ("s.csv", script, "text/csv")}, headers=_auth())
    client.post(f"/api/projects/{pid}/uploads?file_type=budget", files={"file": ("b.csv", budget, "text/csv")}, headers=_auth())
    client.post(f"/api/projects/{pid}/jobs/ingest", headers=_auth())
    artifacts = client.get(f"/api/projects/{pid}/artifacts", headers=_auth()).json()
    assert artifacts
    art = artifacts[0]
    assert client.get(f"/api/artifacts/{art['id']}?token={art['signed_token']}", headers=_auth()).status_code == 200
    assert client.get(f"/api/artifacts/{art['id']}?token={art['signed_token']}", headers=_auth(org="org-b")).status_code == 404
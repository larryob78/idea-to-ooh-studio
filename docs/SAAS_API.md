# SaaS API

## Health
- `GET /healthz`

## Org
- `GET /api/org`
- `GET /api/org/usage`

## Projects
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{id}`

## Uploads
- `POST /api/projects/{id}/uploads`
- `GET /api/projects/{id}/uploads`

## Analysis outputs
- `GET /api/projects/{id}/risks`
- `GET /api/projects/{id}/recommendations`
- `GET /api/projects/{id}/assumptions`

## Snapshots
- `GET /api/projects/{id}/snapshots`
- `GET /api/snapshots/{id}`

## Jobs
- `POST /api/projects/{id}/jobs/ingest`
- `POST /api/projects/{id}/jobs/analyze`
- `POST /api/projects/{id}/jobs/snapshot`
- `POST /api/projects/{id}/jobs/compare`
- `POST /api/projects/{id}/jobs/export`
- `GET /api/jobs/{id}`

## Artifacts
- `GET /api/projects/{id}/artifacts`
- `GET /api/artifacts/{id}?token=...`

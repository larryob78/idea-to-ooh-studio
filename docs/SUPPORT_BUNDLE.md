# Support Bundle

## Endpoint
- `POST /api/projects/{id}/support-bundle`
- Access: org `owner` or `admin` only.

## Contents
- `job_records.json`
- `job_status_history.json`
- `ingest_report.json` (if available)
- `audit_log_events.json`
- `artifacts_index.json`
- `versions.json` (app/parser/scoring)
- `environment_summary.json` (safe, non-secret subset)

## Safety
- No secrets included.
- Intended for debugging and support handoff.

# Launch Readiness (Phase 7)

## Goals achieved
- Onboarding and org role workflows (members, invites, role updates, invite acceptance).
- First-run project wizard status and guarded progression for ingest warnings.
- In-app guidance on interpretation, limitations, and provenance.
- Actionable job failure responses and rerun endpoint.
- In-app notifications for job outcomes.
- Admin diagnostics and support bundle export.

## Failure handling standards
- Job error responses include reason + where-to-look + next-step guidance.
- Users can rerun failed jobs without re-uploading files.
- Duplicate queued/running jobs are reused by default to prevent spam confusion.

## Support readiness
- Support bundle endpoint returns zip with jobs/history, ingest report, audit events, artifacts index, versions, and safe env summary.
- Bundle excludes secrets.

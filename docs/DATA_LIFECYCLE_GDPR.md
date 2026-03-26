# Data Lifecycle and GDPR Basics

## Export
- Endpoint: `POST /api/projects/{id}/gdpr/export`
- Returns project, uploads metadata, assumptions, snapshots, artifact references.

## Deletion
- Endpoint: `DELETE /api/projects/{id}`
- Soft deletes project and removes associated uploads/assumptions/snapshots/artifacts rows.

## Notes
- This build provides baseline operational GDPR flows for dev/test.

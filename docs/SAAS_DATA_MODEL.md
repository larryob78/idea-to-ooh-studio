# SaaS Data Model

Core tables from migration `001_init.sql`:
- organizations
- users
- memberships (RBAC roles)
- projects
- uploads
- assumptions
- snapshots
- artifacts
- jobs
- audit_log_events
- plans
- subscriptions

## Tenant isolation
- `org_id` is present on all tenant-owned tables.
- Every API query scopes by `org_id` from auth context.

## Common fields
- `created_at`, `updated_at` included broadly.
- `projects.deleted_at` supports soft delete.

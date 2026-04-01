# Onboarding and Roles

## Org onboarding
- `POST /api/onboarding/org` creates org and owner membership.
- `POST /api/org/invites` creates invite token (owner/admin only).
- `POST /api/onboarding/accept-invite` accepts invite and adds membership.

## Roles
- owner/admin: manage members, invites, support bundle, org diagnostics.
- editor: project and workflow operations.
- viewer: read-only project access.

## Org settings UI
- `/app/org/settings` provides members list, invite member, role management references.

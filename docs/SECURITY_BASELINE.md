# Security Baseline

- Bearer auth required for `/api/*`.
- Org scoping enforced at query level.
- Minimal RBAC: owner/admin/editor/viewer.
- Rate limiting by org+user+ip.
- CORS allowlist configurable.
- Secure headers added (`x-content-type-options`, `x-frame-options`).
- Upload validation for file type and max size.
- Artifact access via signed token with expiry.
- Secrets policy: use `.env`, commit `.env.example` only.

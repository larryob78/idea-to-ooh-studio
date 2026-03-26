# SaaS Setup

## Stack decisions
- Backend: FastAPI.
- DB: Postgres for deployment, SQLite fallback for local lightweight runs.
- Queue: Redis available in docker-compose; current implementation runs jobs inline with durable DB status.
- Auth: Supabase-compatible bearer flow planned; local dev uses deterministic dev bearer token (`dev-<user>:<org>:<role>`).
- Storage: S3/Supabase-compatible abstraction with local filesystem backend for dev.

## Local dev
1. Copy env:
   - `cp .env.example .env`
2. Start services:
   - `docker compose up --build`
3. Health check:
   - `curl http://localhost:8000/healthz`
4. Use API with bearer:
   - `Authorization: Bearer dev-u1:org-demo:owner`

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable

from fastapi import Header, HTTPException, Request


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    org_id: str
    role: str


RATE_LIMIT_WINDOW_S = int(os.getenv("RATE_LIMIT_WINDOW_S", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "120"))
_ALLOWED_ORIGINS = [x.strip() for x in os.getenv("CORS_ALLOWLIST", "http://localhost:3000").split(",") if x.strip()]
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


def allowed_origins() -> list[str]:
    return _ALLOWED_ORIGINS


def parse_dev_bearer(auth_header: str | None) -> AuthContext:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth_header.replace("Bearer ", "", 1)
    # dev token format: dev-<user_id>:<org_id>:<role>
    if not token.startswith("dev-"):
        raise HTTPException(status_code=401, detail="Unsupported auth token in local mode")
    try:
        payload = token.replace("dev-", "", 1)
        user_id, org_id, role = payload.split(":", 2)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token format") from exc
    if role not in {"owner", "admin", "editor", "viewer"}:
        raise HTTPException(status_code=403, detail="Invalid role")
    return AuthContext(user_id=user_id, org_id=org_id, role=role)


def require_auth(authorization: str | None = Header(default=None)) -> AuthContext:
    return parse_dev_bearer(authorization)


def require_role(min_roles: set[str]) -> Callable[[AuthContext], AuthContext]:
    def _guard(ctx: AuthContext) -> AuthContext:
        if ctx.role not in min_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return ctx

    return _guard


def enforce_rate_limit(request: Request, ctx: AuthContext) -> None:
    ip = request.client.host if request.client else "unknown"
    key = f"{ctx.org_id}:{ctx.user_id}:{ip}"
    now = time.time()
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_S:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)

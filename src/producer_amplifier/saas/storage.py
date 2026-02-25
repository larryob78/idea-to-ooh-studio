from __future__ import annotations

import hashlib
import hmac
import os
import time
from pathlib import Path


STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT", ".data/storage"))
SIGNING_SECRET = os.getenv("SIGNED_URL_SECRET", "dev-secret")


def write_blob(key: str, content: bytes) -> Path:
    target = STORAGE_ROOT / key
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(content)
    tmp.replace(target)
    return target


def read_blob(key: str) -> bytes:
    return (STORAGE_ROOT / key).read_bytes()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_signed_token(artifact_id: str, expires_in_s: int = 600) -> str:
    expires_at = int(time.time()) + expires_in_s
    payload = f"{artifact_id}:{expires_at}"
    sig = hmac.new(SIGNING_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{artifact_id}:{expires_at}:{sig}"


def verify_signed_token(token: str) -> str | None:
    try:
        artifact_id, expires_at, sig = token.split(":", 2)
        payload = f"{artifact_id}:{expires_at}"
        expected = hmac.new(SIGNING_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(expires_at) < int(time.time()):
            return None
        return artifact_id
    except Exception:
        return None

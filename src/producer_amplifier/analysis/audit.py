from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_VERSION = "0.3.0"
PARSER_VERSION = "v2"
SCORING_VERSION = "v2"


def _file_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_audit_log(
    log_path: Path,
    action: str,
    input_paths: list[Path],
    artifact_paths: list[Path],
    warnings_count: int,
    extra: dict[str, Any] | None = None,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "versions": {
            "app": APP_VERSION,
            "parser": PARSER_VERSION,
            "scoring": SCORING_VERSION,
        },
        "inputs": [
            {
                "path": str(path),
                "sha256": _file_hash(path),
                "mtime": path.stat().st_mtime if path.exists() else None,
            }
            for path in input_paths
        ],
        "artifacts": [str(path) for path in artifact_paths],
        "warnings_count": warnings_count,
        "extra": extra or {},
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

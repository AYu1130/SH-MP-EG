"""Append-only NDJSON debug logger for session 2d0ce5."""
from __future__ import annotations

import json
import time
from pathlib import Path

_LOG_PATH = Path(__file__).resolve().parents[3] / "debug-2d0ce5.log"


def agent_log(hypothesis_id: str, location: str, message: str, data: dict | None = None) -> None:
    payload = {
        "sessionId": "2d0ce5",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
        "runId": "bright-led-debug",
    }
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
"""Append-only NDJSON for debug sessions (see repo debug-2d0ce5.log)."""
from __future__ import annotations

import json
import time
from pathlib import Path

_LOG_PATH = Path(__file__).resolve().parents[3] / "debug-2d0ce5.log"


def agent_log(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict | None = None,
    *,
    run_id: str = "pre-fix",
) -> None:
    payload = {
        "sessionId": "2d0ce5",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
        "runId": run_id,
    }
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass

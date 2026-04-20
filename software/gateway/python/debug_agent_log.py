"""Append-only NDJSON for debug session 2d0ce5."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

_LOG_PATH = Path(__file__).resolve().parents[3] / "debug-2d0ce5.log"
_LOG = logging.getLogger("gateway.debug_agent_log")


def agent_log(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict | None = None,
    *,
    run_id: str = "bright-led-debug",
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
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError as e:
        _LOG.error("debug ndjson write failed path=%s err=%s", _LOG_PATH, e)

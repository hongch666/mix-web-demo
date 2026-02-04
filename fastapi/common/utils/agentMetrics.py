from __future__ import annotations

import time
from threading import Lock
from typing import Any, Dict, List

_metrics_lock: Lock = Lock()
_agent_stream_metrics: List[Dict[str, Any]] = []


def record_agent_stream_metric(
    service: str,
    user_id: Any,
    decision_ms: int,
    llm_wait_ms: int,
    total_ms: int,
    llm_wait_ratio: float,
) -> None:
    record: Dict[str, Any] = {
        "service": service,
        "user_id": user_id,
        "decision_ms": decision_ms,
        "llm_wait_ms": llm_wait_ms,
        "total_ms": total_ms,
        "llm_wait_ratio": round(llm_wait_ratio, 4),
        "timestamp": int(time.time()),
    }
    with _metrics_lock:
        _agent_stream_metrics.append(record)


def get_agent_stream_metrics() -> List[Dict[str, Any]]:
    with _metrics_lock:
        return list(_agent_stream_metrics)


def clear_agent_stream_metrics() -> int:
    with _metrics_lock:
        count = len(_agent_stream_metrics)
        _agent_stream_metrics.clear()
        return count

"""In-process runtime telemetry for PBL canary rollout monitoring."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock
from time import time
from typing import Dict, Any


_lock = Lock()
_counters = defaultdict(int)
_timing_sums = defaultdict(float)
_timing_counts = defaultdict(int)
_started_at = int(time())


def incr(name: str, value: int = 1) -> None:
    with _lock:
        _counters[name] += int(value)


def timing(name: str, ms: float) -> None:
    try:
        val = float(ms)
    except Exception:
        return
    if val < 0:
        return
    with _lock:
        _timing_sums[name] += val
        _timing_counts[name] += 1


def snapshot() -> Dict[str, Any]:
    with _lock:
        counters = dict(_counters)
        timing_avg_ms = {}
        for key, total in _timing_sums.items():
            count = _timing_counts.get(key, 0)
            timing_avg_ms[key] = round(total / count, 2) if count else 0.0

        return {
            "started_at_epoch": _started_at,
            "counters": counters,
            "timing_avg_ms": timing_avg_ms,
            "timing_samples": dict(_timing_counts),
        }

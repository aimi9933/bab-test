from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequestMetrics:
    """In-memory metrics tracking for API requests."""

    total_requests: int = 0
    total_errors: int = 0
    total_duration_ms: float = 0.0
    status_codes: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    endpoints: dict[str, dict[str, Any]] = field(default_factory=dict)
    recent_requests: list[dict[str, Any]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.status_codes:
            self.status_codes = defaultdict(int)
        if not self.endpoints:
            self.endpoints = {}
        if not self.recent_requests:
            self.recent_requests = []

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Record a request."""
        self.total_requests += 1
        self.total_duration_ms += duration_ms

        if status_code >= 400:
            self.total_errors += 1

        self.status_codes[status_code] += 1

        # Track per-endpoint stats
        endpoint = f"{method} {path}"
        if endpoint not in self.endpoints:
            self.endpoints[endpoint] = {
                "count": 0,
                "total_duration_ms": 0.0,
                "error_count": 0,
                "avg_duration_ms": 0.0,
            }

        endpoint_data = self.endpoints[endpoint]
        endpoint_data["count"] += 1
        endpoint_data["total_duration_ms"] += duration_ms
        endpoint_data["avg_duration_ms"] = (
            endpoint_data["total_duration_ms"] / endpoint_data["count"]
        )

        if status_code >= 400:
            endpoint_data["error_count"] += 1

        # Keep recent requests (last 100)
        self.recent_requests.append(
            {
                "timestamp": time.time(),
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }
        )
        if len(self.recent_requests) > 100:
            self.recent_requests = self.recent_requests[-100:]

    def get_stats(self) -> dict[str, Any]:
        """Get formatted statistics."""
        uptime_seconds = time.time() - self.start_time
        avg_duration_ms = (
            self.total_duration_ms / self.total_requests
            if self.total_requests > 0
            else 0.0
        )

        return {
            "uptime_seconds": uptime_seconds,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": (
                (self.total_errors / self.total_requests * 100)
                if self.total_requests > 0
                else 0.0
            ),
            "average_duration_ms": avg_duration_ms,
            "status_codes": dict(self.status_codes),
            "endpoints": self.endpoints,
            "recent_requests": self.recent_requests[-10:],  # Last 10 requests
        }

    def reset(self) -> None:
        """Reset metrics."""
        self.total_requests = 0
        self.total_errors = 0
        self.total_duration_ms = 0.0
        self.status_codes = defaultdict(int)
        self.endpoints = {}
        self.recent_requests = []
        self.start_time = time.time()


_metrics_instance: RequestMetrics | None = None


def get_metrics() -> RequestMetrics:
    """Get the global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = RequestMetrics()
    return _metrics_instance


def reset_metrics() -> None:
    """Reset the global metrics instance."""
    global _metrics_instance
    _metrics_instance = RequestMetrics()

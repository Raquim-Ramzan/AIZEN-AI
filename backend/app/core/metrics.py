"""
Metrics & Observability for AIZEN
==================================
Prometheus-compatible metrics for monitoring performance.
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects application metrics for observability.
    Compatible with Prometheus format for easy integration.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # Counters
        self._counters: dict[str, int] = defaultdict(int)

        # Gauges (current values)
        self._gauges: dict[str, float] = {}

        # Histograms (latency distributions)
        self._histograms: dict[str, list] = defaultdict(list)

        # Histogram buckets (in seconds)
        self._buckets = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

        # Start time for uptime calculation
        self._start_time = datetime.now(UTC)

    def increment(self, name: str, value: int = 1, labels: dict[str, str] | None = None):
        """Increment a counter"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Set a gauge value"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Observe a value for histogram"""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            # Keep only last 1000 observations
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def timer(self, name: str, labels: dict[str, str] | None = None):
        """Context manager for timing operations"""
        return MetricsTimer(self, name, labels)

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> int:
        """Get counter value"""
        key = self._make_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0)

    def get_histogram_stats(
        self, name: str, labels: dict[str, str] | None = None
    ) -> dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        with self._lock:
            values = self._histograms.get(key, [])
            if not values:
                return {"count": 0, "sum": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}

            sorted_vals = sorted(values)
            count = len(sorted_vals)

            return {
                "count": count,
                "sum": sum(sorted_vals),
                "avg": sum(sorted_vals) / count,
                "min": sorted_vals[0],
                "max": sorted_vals[-1],
                "p50": sorted_vals[int(count * 0.5)],
                "p95": sorted_vals[int(count * 0.95)] if count > 1 else sorted_vals[-1],
                "p99": sorted_vals[int(count * 0.99)] if count > 1 else sorted_vals[-1],
            }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics"""
        with self._lock:
            uptime = (datetime.now(UTC) - self._start_time).total_seconds()

            return {
                "uptime_seconds": uptime,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name) for name in self._histograms.keys()
                },
            }

    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        lines = []

        # Counters
        for key, value in self._counters.items():
            lines.append(f"aizen_{key} {value}")

        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"aizen_{key} {value}")

        # Collect Histograms (stat summary)
        for key, values in self._histograms.items():
            if values:
                stats = self.get_histogram_stats(key)
                lines.append(f"aizen_{key}_count {stats['count']}")
                lines.append(f"aizen_{key}_sum {stats['sum']}")
                lines.append(f"aizen_{key}_avg {stats['avg']}")

        return "\n".join(lines)


class MetricsTimer:
    """Context manager for timing operations"""

    def __init__(
        self, collector: MetricsCollector, name: str, labels: dict[str, str] | None = None
    ):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed = time.perf_counter() - self.start_time
        self.collector.observe(self.name, elapsed, self.labels)


# Singleton instance
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector"""
    return _metrics


# Predefined metric names
class Metrics:
    """Predefined metric names for consistency"""

    # Request metrics
    REQUESTS_TOTAL = "requests_total"
    REQUEST_DURATION = "request_duration_seconds"
    WEBSOCKET_CONNECTIONS = "websocket_connections"

    # AI metrics
    LLM_REQUESTS = "llm_requests_total"
    LLM_LATENCY = "llm_latency_seconds"
    LLM_TOKENS = "llm_tokens_total"

    # Memory metrics
    RAG_RETRIEVALS = "rag_retrievals_total"
    RAG_LATENCY = "rag_latency_seconds"
    FACTS_EXTRACTED = "facts_extracted_total"
    MEMORY_SIZE = "memory_size_bytes"

    # Cache metrics
    CACHE_HITS = "cache_hits_total"
    CACHE_MISSES = "cache_misses_total"

    # Tool metrics
    TOOL_EXECUTIONS = "tool_executions_total"
    TOOL_APPROVALS = "tool_approvals_total"

    # Error metrics
    ERRORS_TOTAL = "errors_total"


# Decorator for timing functions
def timed(metric_name: str, labels: dict[str, str] | None = None):
    """Decorator to time function execution"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with get_metrics().timer(metric_name, labels):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with get_metrics().timer(metric_name, labels):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# asyncio is imported at the top level

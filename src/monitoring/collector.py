"""
Thread-safe in-memory Metrics Collector for Lakers in 5.
Implements lightweight Prometheus-compatible metric collection without heavy external dependencies.
Tracks HTTP requests, latencies, errors, prediction operations, shadow inference, and data quality.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Tuple


class MetricCollector:
    """
    Thread-safe Prometheus-compatible in-memory metric store.
    """
    _instance: Optional["MetricCollector"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricCollector, cls).__new__(cls)
                cls._instance._init_metrics()
            return cls._instance

    def _init_metrics(self):
        self._counters: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {
            "http_requests_total": {},
            "http_errors_total": {},
            "prediction_requests_total": {},
            "shadow_prediction_requests_total": {},
            "data_quality_failures_total": {},
            "model_load_events_total": {}
        }
        self._gauges: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {
            "application_healthy": {(): 1.0},
            "models_loaded": {(): 1.0},
            "shadow_model_available": {(): 1.0}
        }
        self._histograms: Dict[str, Dict[Tuple[Tuple[str, str], ...], List[float]]] = {
            "http_request_duration_seconds": {},
            "prediction_duration_seconds": {}
        }
        self._descriptions = {
            "http_requests_total": "Total count of HTTP requests received",
            "http_errors_total": "Total count of HTTP request errors",
            "prediction_requests_total": "Total count of prediction requests processed",
            "shadow_prediction_requests_total": "Total count of shadow prediction requests",
            "data_quality_failures_total": "Total count of data quality validation failures",
            "model_load_events_total": "Total count of model loading events",
            "application_healthy": "Current application health status (1 = healthy, 0 = unhealthy)",
            "models_loaded": "Current production models loaded status (1 = loaded, 0 = missing)",
            "shadow_model_available": "Current shadow model status (1 = active, 0 = degraded/unavailable)",
            "http_request_duration_seconds": "HTTP request duration in seconds",
            "prediction_duration_seconds": "Prediction inference latency in seconds"
        }
        self._metric_lock = threading.Lock()

    def reset(self):
        """Resets all metrics back to initial state (useful in test suites)."""
        with self._metric_lock:
            self._init_metrics()

    def _make_key(self, labels: Optional[Dict[str, str]] = None) -> Tuple[Tuple[str, str], ...]:
        if not labels:
            return ()
        return tuple(sorted((str(k), str(v)) for k, v in labels.items()))

    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increments a counter metric with sanitized low-cardinality labels."""
        with self._metric_lock:
            if name not in self._counters:
                self._counters[name] = {}
            k = self._make_key(labels)
            self._counters[name][k] = self._counters[name].get(k, 0.0) + value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Sets a gauge metric value."""
        with self._metric_lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            k = self._make_key(labels)
            self._gauges[name][k] = float(value)

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Records an observation into a histogram metric."""
        with self._metric_lock:
            if name not in self._histograms:
                self._histograms[name] = {}
            k = self._make_key(labels)
            if k not in self._histograms[name]:
                self._histograms[name][k] = []
            # Keep rolling bounded list of recent observations to prevent unbounded memory growth
            if len(self._histograms[name][k]) >= 5000:
                self._histograms[name][k] = self._histograms[name][k][-2500:]
            self._histograms[name][k].append(float(value))

    def get_counter_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Retrieves current counter value for specified labels."""
        with self._metric_lock:
            k = self._make_key(labels)
            return self._counters.get(name, {}).get(k, 0.0)

    def get_gauge_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Retrieves current gauge value."""
        with self._metric_lock:
            k = self._make_key(labels)
            return self._gauges.get(name, {}).get(k, 0.0)

    def export_prometheus_text(self) -> str:
        """
        Exports all registered metrics formatted in standard Prometheus exposition format.
        """
        lines: List[str] = []
        with self._metric_lock:
            # Counters
            for name, records in self._counters.items():
                desc = self._descriptions.get(name, name)
                lines.append(f"# HELP {name} {desc}")
                lines.append(f"# TYPE {name} counter")
                if not records:
                    lines.append(f"{name} 0.0")
                for labels, val in records.items():
                    if labels:
                        lbl_str = ",".join(f'{k}="{v}"' for k, v in labels)
                        lines.append(f"{name}{{{lbl_str}}} {val}")
                    else:
                        lines.append(f"{name} {val}")

            # Gauges
            for name, records in self._gauges.items():
                desc = self._descriptions.get(name, name)
                lines.append(f"# HELP {name} {desc}")
                lines.append(f"# TYPE {name} gauge")
                if not records:
                    lines.append(f"{name} 0.0")
                for labels, val in records.items():
                    if labels:
                        lbl_str = ",".join(f'{k}="{v}"' for k, v in labels)
                        lines.append(f"{name}{{{lbl_str}}} {val}")
                    else:
                        lines.append(f"{name} {val}")

            # Histograms (Summary representation with count, sum, avg)
            for name, records in self._histograms.items():
                desc = self._descriptions.get(name, name)
                lines.append(f"# HELP {name} {desc}")
                lines.append(f"# TYPE {name} summary")
                for labels, vals in records.items():
                    cnt = len(vals)
                    tot = sum(vals) if cnt > 0 else 0.0
                    lbl_base = ",".join(f'{k}="{v}"' for k, v in labels)
                    prefix = f"{{{lbl_base}}}" if lbl_base else ""
                    lines.append(f"{name}_count{prefix} {cnt}")
                    lines.append(f"{name}_sum{prefix} {tot:.6f}")

        return "\n".join(lines) + "\n"

    def export_json(self) -> Dict[str, Any]:
        """Exports metrics as a clean dictionary for JSON APIs and status dashboards."""
        with self._metric_lock:
            data: Dict[str, Any] = {
                "counters": {},
                "gauges": {},
                "histograms": {}
            }
            for name, records in self._counters.items():
                data["counters"][name] = {str(dict(k)): v for k, v in records.items()}
            for name, records in self._gauges.items():
                data["gauges"][name] = {str(dict(k)): v for k, v in records.items()}
            for name, records in self._histograms.items():
                data["histograms"][name] = {}
                for k, vals in records.items():
                    cnt = len(vals)
                    tot = sum(vals) if cnt > 0 else 0.0
                    avg = (tot / cnt) if cnt > 0 else 0.0
                    data["histograms"][name][str(dict(k))] = {
                        "count": cnt,
                        "sum_seconds": round(tot, 4),
                        "avg_seconds": round(avg, 4),
                        "p95_seconds": round(sorted(vals)[int(cnt * 0.95)], 4) if cnt >= 20 else round(avg, 4)
                    }
            return data


metrics_collector = MetricCollector()

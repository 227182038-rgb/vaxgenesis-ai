"""Prometheus metrics."""
from prometheus_client import Counter, Gauge, Histogram, Info

APP_INFO = Info("vaxgenesis", "VaxGenesis AI backend")
APP_INFO.info({"version": "2.0.0"})

HTTP_REQUESTS = Counter("vaxgenesis_http_requests_total", "HTTP requests", ["method", "endpoint", "status"])
MODULE_EXECUTIONS = Counter("vaxgenesis_module_executions_total", "Module executions", ["module", "status"])
ACTIVE_LEARNING_ITEMS = Gauge("vaxgenesis_active_learning_queue_size", "Active learning queue size")

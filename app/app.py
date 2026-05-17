from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import random
import platform
import datetime
import logging

app = Flask(__name__)

# ---------------------------------------------------------------------------
# PROMETHEUS METRICS
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

ACTIVE_REQUESTS = Gauge("http_active_requests", "Currently active HTTP requests")

APP_INFO = Gauge(
    "app_info",
    "Application information",
    ["version", "python_version"],
)
APP_INFO.labels(version="1.0.0", python_version=platform.python_version()).set(1)


# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------
@app.before_request
def before_request():
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()


@app.after_request
def after_request(response):
    latency = time.time() - request.start_time
    ACTIVE_REQUESTS.dec()
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code,
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.path,
    ).observe(latency)
    return response


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return jsonify(
        {
            "service": "DevOps Monitoring Demo",
            "status": "running",
            "server": platform.node(),
            "timestamp": str(datetime.datetime.now()),
            "version": "1.0.0",
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/slow")
def slow():
    """Simulates variable latency for testing latency dashboards."""
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
    return jsonify({"response_time": round(delay, 3), "status": "ok"})


@app.route("/error")
def error():
    """50% chance of returning a 500 error for testing error rate alerts."""
    if random.random() < 0.5:
        return jsonify({"error": "Internal Server Error (simulated)"}), 500
    return jsonify({"status": "ok"})


@app.route("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    return generate_latest(), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/webhook/alert", methods=["POST"])
def alert_webhook():
    """Receives alerts from AlertManager."""
    data = request.get_json(silent=True)
    if data:
        for alert in data.get("alerts", []):
            logging.warning(
                "ALERT [%s] %s: %s",
                alert.get("status", "unknown"),
                alert.get("labels", {}).get("alertname", "unknown"),
                alert.get("annotations", {}).get("description", "no description"),
            )
    return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5000, debug=False)

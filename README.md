# Production-Grade Observability Stack

> **Prometheus + Grafana + Loki + AlertManager + cAdvisor + Node Exporter** — complete monitoring from metrics to logs to alerting, all running locally via Docker Compose.

![Docker Compose](https://img.shields.io/badge/Docker_Compose-v3.8-2496ED?style=flat&logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-v2.51-E6522C?style=flat&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-v10.4-F46800?style=flat&logo=grafana&logoColor=white)
![Last Commit](https://img.shields.io/github/last-commit/MedArkidDev-wq/linux-monitoring-stack)

## What This Project Does

A complete monitoring system that watches server CPU, memory, disk, network, container health, and application logs — all visible in real-time Grafana dashboards. Includes incident simulation scripts that generate post-mortem documentation automatically. This mirrors exactly what NOC engineers and SREs use in production daily.

## Architecture

```
                    +-------------+
                    |   Grafana   | :3000
                    | Dashboards  |
                    +------+------+
                           | queries
              +------------+------------+
              |            |            |
              v            v            v
     +------------+ +-----------+ +----------+
     | Prometheus | |   Loki    | |AlertMgr  |
     |  Metrics   | |   Logs    | |  Alerts  |
     |   :9090    | |   :3100   | |   :9093  |
     +-----+------+ +-----+-----+ +----------+
           |              |
     +-----+-----+        |
     |     |     |        |
     v     v     v        v
  +----++-----++---+  +--------+
  |Node||cAdv ||App|  |Promtail|
  |Exp ||isor ||   |  |  Logs  |
  +----++-----++---+  +--------+
  :9100  :8080  :5000
```

## Stack Components

| Service | Image | Port | Purpose |
|---|---|---|---|
| **Nginx** | nginx:1.25-alpine | 80 | Reverse proxy with rate limiting |
| **Flask App** | Custom build | 5000 | Sample app with Prometheus metrics |
| **Prometheus** | prom/prometheus:v2.51.0 | 9090 | Metrics collection (15-day retention) |
| **Node Exporter** | prom/node-exporter:v1.7.0 | 9100 | Linux system metrics |
| **cAdvisor** | gcr.io/cadvisor/cadvisor:v0.49.1 | 8080 | Per-container CPU/RAM metrics |
| **Grafana** | grafana/grafana:10.4.0 | 3000 | Dashboards and visualization |
| **AlertManager** | prom/alertmanager:v0.27.0 | 9093 | Alert routing |
| **Loki** | grafana/loki:2.9.6 | 3100 | Log aggregation |
| **Promtail** | grafana/promtail:2.9.6 | 9080 | Log collector |

## Project Structure

```
linux-monitoring-stack/
├── docker-compose.yml              # 9-service orchestration
├── prometheus/
│   ├── prometheus.yml              # Scrape targets
│   └── rules/
│       └── alerts.yml              # CPU, memory, disk, container alerts
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml     # Auto-connect Prometheus + Loki
│       └── dashboards/
│           └── dashboards.yml
├── alertmanager/
│   └── alertmanager.yml            # Webhook, email, Slack routing
├── loki/
│   └── loki-config.yml
├── promtail/
│   └── promtail-config.yml         # Docker + system log shipping
├── nginx/
│   └── nginx.conf                  # Rate limiting reverse proxy
├── app/
│   ├── app.py                      # Flask with Prometheus metrics
│   ├── requirements.txt
│   └── Dockerfile
├── scripts/
│   ├── simulate_load.sh            # CPU stress + HTTP traffic
│   └── simulate_incident.sh        # Kill services, auto-generate post-mortem
└── docs/
    └── incident-*.md               # Auto-generated post-mortem documents
```

## Flask App With Built-In Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests',
                        ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds',
                            'HTTP request latency', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('http_active_requests', 'Active HTTP requests')
```

| Endpoint | Purpose |
|---|---|
| `GET /` | Service info and status |
| `GET /health` | Health check for load balancers |
| `GET /slow` | Simulates 0.5-2s latency (tests dashboards) |
| `GET /error` | 50% chance 500 error (tests alert rules) |
| `GET /metrics` | Prometheus scrape endpoint |

## Alert Rules

| Alert | Condition | Severity | Duration |
|---|---|---|---|
| **HighCPUUsage** | CPU > 80% | Warning | 2 min |
| **HighMemoryUsage** | Memory > 85% | Warning | 2 min |
| **DiskSpaceLow** | Disk > 90% | Critical | 5 min |
| **ContainerDown** | flask-app missing | Critical | 1 min |
| **NginxDown** | Nginx unresponsive | Critical | 1 min |
| **HighErrorRate** | 5xx > 0.05 req/s | Warning | 2 min |

## Incident Simulation

### Load Test

```bash
./scripts/simulate_load.sh
# Generates CPU stress + 1000 HTTP requests
# Watch Grafana CPU dashboard spike in real time
```

### Incident Test

```bash
./scripts/simulate_incident.sh
# 1. Stops flask-app container
# 2. Prometheus detects outage within 15s
# 3. ContainerDown alert fires at 60s
# 4. AlertManager sends notification
# 5. Auto-restarts container
# 6. Generates post-mortem document
```

### Auto-Generated Post-Mortem

```markdown
# Incident Post-Mortem
**Date:** 2026-05-16 14:23:00
**Severity:** P2 — Service Degraded

## Timeline
| Time | Event |
|------|-------|
| 14:23:00 | flask-app container stopped |
| 14:23:15 | Prometheus detects missing metric |
| 14:24:00 | ContainerDown alert fires |
| 14:28:00 | Service recovered |
```

## Quick Start

```bash
git clone https://github.com/MedArkidDev-wq/linux-monitoring-stack.git
cd linux-monitoring-stack
docker compose up -d
docker compose ps   # All services should be "Up"
```

**Access your stack:**
- Grafana: `http://localhost:3000` (admin / devops123)
- Prometheus: `http://localhost:9090`
- AlertManager: `http://localhost:9093`
- Application: `http://localhost`

### Import Pre-Built Dashboards

1. Grafana > **+** > Import > ID **1860** (Node Exporter Full)
2. Grafana > **+** > Import > ID **13659** (Docker Containers)
3. Grafana > **+** > Import > ID **12708** (Nginx)

## Cost

**$0** — Everything runs locally via Docker Compose.

## Author

**Mohamed Arkid** — DevOps Engineer and Cloud Consultant

- [moarkid.com](https://moarkid.com)
- [LinkedIn](https://www.linkedin.com/in/mohamed-arkid)

## License

MIT

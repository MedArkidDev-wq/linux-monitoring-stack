# Linux Monitoring Stack

Nine containers. One `docker compose up`. You get metrics, logs, dashboards, and alerting running in about 30 seconds.

This is the same stack (Prometheus, Grafana, Loki) that most companies use in production, just packaged so you can run it on your laptop and actually understand how all the pieces connect. I also added scripts that simulate real incidents so you can practice debugging and write post-mortems like you would on the job.

## What's running

| Service | Port | What it does |
|---|---|---|
| Nginx | 80 | Reverse proxy with rate limiting in front of the app |
| Flask App | 5000 | Sample API with Prometheus metrics baked in |
| Prometheus | 9090 | Scrapes metrics every 15 seconds, stores for 15 days |
| Node Exporter | 9100 | Exposes host CPU, memory, disk, network metrics |
| cAdvisor | 8080 | Per-container resource usage |
| Grafana | 3000 | Dashboards (login: admin / devops123) |
| AlertManager | 9093 | Routes alerts to webhook, Slack, email |
| Loki | 3100 | Log aggregation (think ELK but way lighter) |
| Promtail | 9080 | Ships Docker and system logs to Loki |

## What's in here

```
linux-monitoring-stack/
├── docker-compose.yml           # All 9 services, networks, and volumes
├── prometheus/
│   ├── prometheus.yml           # What to scrape and how often
│   └── rules/alerts.yml         # When to fire alerts
├── grafana/provisioning/        # Auto-configures datasources on startup
├── alertmanager/alertmanager.yml # Where alerts get sent
├── loki/loki-config.yml         # Log storage and retention
├── promtail/promtail-config.yml # What logs to collect
├── nginx/nginx.conf             # Rate limiting + proxy to Flask
├── app/
│   ├── app.py                   # Flask with custom Prometheus counters/histograms
│   ├── requirements.txt
│   └── Dockerfile
└── scripts/
    ├── simulate_load.sh         # Blasts the app with traffic
    └── simulate_incident.sh     # Kills the app, waits for alerts, writes a post-mortem
```

## The app has Prometheus metrics built in

Not just a hello-world. The Flask app tracks every request with counters, histograms, and gauges:

```python
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Latency', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('http_active_requests', 'Currently active requests')
```

There are also endpoints specifically designed to test your monitoring:
- `/slow` adds random 0.5-2s delay so you can watch latency graphs spike
- `/error` returns a 500 half the time so you can test error rate alerts
- `/metrics` is the Prometheus scrape endpoint

## Alert rules

These fire automatically when something goes wrong:

| Alert | When it fires | Severity |
|---|---|---|
| HighCPUUsage | CPU over 80% for 2 min | Warning |
| HighMemoryUsage | Memory over 85% for 2 min | Warning |
| DiskSpaceLow | Disk over 90% for 5 min | Critical |
| ContainerDown | flask-app container gone for 1 min | Critical |
| NginxDown | Nginx not responding for 1 min | Critical |
| HighErrorRate | 5xx rate above 0.05/s for 2 min | Warning |

## Incident simulation

This is the part that makes the project interesting. Run the incident script and it:

1. Kills the flask-app container
2. Waits for Prometheus to notice (about 60 seconds)
3. Checks if AlertManager actually fired the alert
4. Restarts the container
5. Writes a full post-mortem markdown file with timestamps

```bash
./scripts/simulate_incident.sh
# Creates docs/incident-2026-05-17_14-23-00.md with the full timeline
```

You end up with a real post-mortem document you can show in interviews.

## Get it running

```bash
git clone https://github.com/MedArkidDev-wq/linux-monitoring-stack.git
cd linux-monitoring-stack
docker compose up -d
```

Then open:
- Grafana at `localhost:3000` (admin / devops123)
- Prometheus at `localhost:9090`
- AlertManager at `localhost:9093`

Import these dashboard IDs in Grafana for instant visibility:
- **1860** for Node Exporter (system metrics)
- **13659** for Docker containers
- **12708** for Nginx

## Generate some traffic

```bash
# Hit the app 50 times
for i in {1..50}; do curl -s http://localhost/ > /dev/null; done

# Test slow responses
for i in {1..10}; do curl -s http://localhost/slow > /dev/null; done

# Test error rates
for i in {1..10}; do curl -s http://localhost/error > /dev/null; done
```

## Cost

$0. Everything runs locally on Docker.

## About

Built by [Mohamed Arkid](https://moarkid.com). DevOps engineer focused on building things that actually work in production.

MIT License

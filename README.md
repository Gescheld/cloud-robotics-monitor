# cloud-robotics-monitor

> A cloud-ready monitoring and analytics platform for industrial robots — telemetry streaming, time-series storage, live dashboards, and alerts.

**Status:** Personal learning project · early scaffolding  
**Why this exists:** I wanted to learn the modern industrial-AI backend stack (FastAPI, Docker, MQTT, Postgres, Grafana, AWS) end-to-end, in a robotics context I care about.

## Overview

`cloud-robotics-monitor` simulates an industrial robot, streams its telemetry through an MQTT broker, ingests it via a FastAPI service into a Postgres database, and visualizes everything in Grafana. Everything runs locally with one `docker compose up` — and is designed to migrate to AWS without changing the codebase.

It's intentionally **small but full-stack**: instead of one impressive component, it shows that all the pieces fit together cleanly.

## Architecture (MVP)

```text
   ┌──────────────┐    MQTT    ┌─────────────┐    SQL     ┌──────────────┐
   │  Simulator   │ ─────────▶ │  Ingest API │ ─────────▶ │  PostgreSQL  │
   │  (Python)    │            │  (FastAPI)  │            │              │
   └──────────────┘            └─────────────┘            └──────────────┘
                                                                 │
                                                                 ▼
                                                          ┌──────────────┐
                                                          │   Grafana    │
                                                          │  dashboards  │
                                                          └──────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for a detailed diagram and design decisions.

## Features

- Simulated robot publishing realistic joint positions, currents, temperatures, and error states
- MQTT broker (Eclipse Mosquitto) for telemetry
- FastAPI ingest service with Pydantic-validated messages
- PostgreSQL time-series schema (optionally TimescaleDB)
- Pre-provisioned Grafana dashboard
- Single-command `docker compose up` for the full stack

## Roadmap

- [x] Repo scaffolding, architecture & feature spec
- [x] Simulator service publishing to MQTT (F1)
- [x] Ingest service writing to Postgres (F2)
- [x] Grafana dashboard — joint plots, currents, temperature, faults (F3)
- [ ] Rolling-window anomaly detection (statistical, no ML yet)
- [ ] Alerting (Grafana → file/webhook)
- [ ] AWS Free Tier deployment guide
- [ ] Multi-robot fleet view
- [ ] Optional ROS2 publisher (WSL2)

## Tech stack

| Layer | Tool |
|-------|------|
| Language | Python 3.11+ |
| Broker | Eclipse Mosquitto (MQTT) |
| API | FastAPI + Pydantic |
| Database | PostgreSQL (optionally TimescaleDB) |
| Dashboard | Grafana |
| Orchestration | Docker Compose |
| CI | GitHub Actions |
| Cloud target | AWS Free Tier (App Runner, RDS, IoT Core) |

## Getting started

> **Note:** F1 (simulator → MQTT) and F2 (MQTT → Postgres ingest) are implemented. Grafana dashboards are next.

### Prerequisites

- Docker Desktop (Windows / macOS) or Docker Engine + Compose plugin (Linux)
- Python 3.11+ for running services natively (optional)

### Quick start

```bash
git clone https://github.com/Gescheld/cloud-robotics-monitor.git
cd cloud-robotics-monitor
docker compose -f infra/docker-compose.yml up --build
```

| Service | URL |
|---------|-----|
| Grafana | http://localhost:3000 (admin / admin) — dashboard: http://localhost:3000/d/robot-telemetry |
| Ingest API | http://localhost:8000/stats — http://localhost:8000/docs |
| MQTT | `localhost:1883` |
| Postgres | `localhost:5432` — user `robotics`, password `robotics`, db `telemetry` |

Verify MQTT messages (optional, from repo root with Python + `paho-mqtt`):

```bash
pip install paho-mqtt
python scripts/verify_mqtt.py
```

## Project structure

```text
cloud-robotics-monitor/
├── docs/                       ← architecture, feature spec, data model
├── services/
│   ├── simulator/              ← Python service that publishes fake robot telemetry to MQTT
│   ├── ingest/                 ← FastAPI consumer writing to Postgres
│   └── api/                    ← FastAPI query API
├── infra/
│   ├── docker-compose.yml      ← runs simulator, broker, ingest, db, grafana
│   ├── grafana/                ← provisioning + dashboard JSON
│   └── postgres/               ← init.sql
├── tests/
└── .github/workflows/ci.yml
```

## Design principles

- **Local first.** The whole stack runs offline on a developer laptop.
- **Cloud ready.** Service boundaries are clean so each container can move to AWS without code changes.
- **Honest about scope.** This is a learning project, not a production SaaS.
- **Specification first.** Each feature has a short spec in `docs/feature-spec.md` before it's implemented — a habit borrowed from the AI-feature-lifecycle world.

## Related

- [Profile README](https://github.com/Gescheld/Gescheld)
- [LinkedIn](https://www.linkedin.com/in/gesche-held-b49947248/)

## License

MIT — see [LICENSE](LICENSE).

# Feature specifications

> Borrowed habit from AI-feature lifecycle: write a small spec for each feature *before* coding it. Keeps scope honest.

Each feature follows this skeleton:

```text
Title
Problem
User story
Success criteria
Non-goals
Notes
```

---

## F1 — Simulated robot telemetry stream (MVP)

**Problem:** No real robot available. Need a believable signal to build everything else around.

**User story:**
> As a developer, I want a Python service that emits realistic-looking robot telemetry to MQTT, so I can build downstream services without a real robot.

**Success criteria:**
- Publishes `RobotTelemetry` messages to `robots/<id>/telemetry` at 20 Hz
- Produces sinusoidal joint trajectories with bounded velocity
- Emits an `error_code != 0` on a configurable fault schedule (e.g. every 60 s, lasting 2 s)
- Configurable via env vars: `ROBOT_ID`, `MQTT_HOST`, `PUBLISH_HZ`, `FAULT_PROBABILITY`
- One Dockerfile, one `requirements.txt`, < 50 LOC of actual logic

**Non-goals:**
- Physically accurate dynamics
- Multiple robot models

---

## F2 — MQTT ingest to Postgres

**Problem:** Telemetry on a broker is volatile. We need a queryable history.

**User story:**
> As a developer, I want a FastAPI service that subscribes to MQTT and writes validated telemetry into Postgres, so downstream consumers can query historical data.

**Success criteria:**
- Subscribes to `robots/+/telemetry`
- Validates each message with Pydantic; drops malformed ones with a counter
- Batches writes every 200 ms or 100 messages, whichever first
- Insert latency p95 < 100 ms under 200 msg/s load
- Exposes `/health` and `/metrics` (Prometheus text)

**Non-goals:**
- Backpressure / dead-letter queue
- Schema migration tooling (use init SQL for now)

---

## F3 — Grafana dashboard

**Problem:** Numbers in a DB are not informative on their own.

**User story:**
> As a recruiter / developer, I want to open Grafana and immediately see live joint plots and an error counter, so I can understand what the platform does in under 60 seconds.

**Success criteria:**
- One dashboard provisioned via JSON in `infra/grafana/`
- Panels: live joint position lines, current heatmap, error-events table, telemetry-rate stat
- Refresh ≤ 5 s
- Imports without manual setup after `docker compose up`

---

## F4 — Anomaly detection (Scope B)

**Problem:** A dashboard alone doesn't tell us when something is off.

**User story:**
> As a developer, I want a rolling statistical anomaly check on joint currents that marks suspicious points and writes events to an `anomalies` table.

**Success criteria:**
- Rolling z-score over a 60-s window per joint
- Threshold configurable (default |z| > 3)
- Anomalies persisted with timestamp, joint, value, score
- Surfaced as a Grafana annotation on the joint plot

**Non-goals (yet):**
- ML model — IsolationForest etc. come in a separate spec (F6)

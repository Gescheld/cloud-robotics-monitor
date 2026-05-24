# Ingest service (F2)

FastAPI service that subscribes to MQTT topic `robots/+/telemetry`, validates payloads with Pydantic, and batch-inserts them into PostgreSQL.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness probe |
| GET | `/stats` | Counters: received / inserted / dropped / buffer size / last insert |

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_HOST` | `mosquitto` | Broker hostname |
| `MQTT_PORT` | `1883` | Broker port |
| `MQTT_TOPIC` | `robots/+/telemetry` | Topic filter |
| `POSTGRES_URL` | `postgresql://robotics:robotics@postgres:5432/telemetry` | DB connection string |
| `BATCH_INTERVAL_S` | `0.5` | Flush every N seconds |
| `BATCH_SIZE` | `100` | Or after N buffered messages |

## How it works

1. Subscribes to MQTT and validates each incoming message via Pydantic (`models.RobotTelemetry`)
2. Appends a row to an in-memory buffer
3. Every `BATCH_INTERVAL_S` (or when buffer hits `BATCH_SIZE`) flushes the batch with `executemany`
4. Tracks counters for observability via `/stats`

Spec: [`docs/feature-spec.md`](../../docs/feature-spec.md) (F2).

# Simulator service (F1)

Publishes simulated robot telemetry to MQTT topic `robots/<robot_id>/telemetry`.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `ROBOT_ID` | `robot-01` | Robot identifier |
| `MQTT_HOST` | `localhost` | Broker hostname |
| `MQTT_PORT` | `1883` | Broker port |
| `PUBLISH_HZ` | `20` | Publish rate |
| `FAULT_INTERVAL_S` | `60` | Fault repeats every N seconds |
| `FAULT_DURATION_S` | `2` | Fault window length |

## Run locally

```bash
pip install -r requirements.txt
# Start Mosquitto first (e.g. via docker compose from infra/)
MQTT_HOST=localhost python main.py
```

## Payload (JSON)

```json
{
  "robot_id": "robot-01",
  "time": "2026-05-24T12:00:00+00:00",
  "joint_positions": [0.1, -0.2, ...],
  "joint_currents": [0.5, 0.6, ...],
  "temperature_c": 42.1,
  "error_code": 0
}
```

Spec: [`docs/feature-spec.md`](../../docs/feature-spec.md) (F1).

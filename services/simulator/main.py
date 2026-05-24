"""Simulated industrial robot publishing telemetry to MQTT (F1)."""

from __future__ import annotations

import json
import math
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

NUM_JOINTS = 6
DEFAULT_JOINT_AMPLITUDE = 0.8
DEFAULT_JOINT_FREQUENCY_HZ = 0.15


@dataclass(frozen=True)
class Config:
    robot_id: str
    mqtt_host: str
    mqtt_port: int
    publish_hz: float
    fault_interval_s: float
    fault_duration_s: float

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            robot_id=os.getenv("ROBOT_ID", "robot-01"),
            mqtt_host=os.getenv("MQTT_HOST", "localhost"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            publish_hz=float(os.getenv("PUBLISH_HZ", "20")),
            fault_interval_s=float(os.getenv("FAULT_INTERVAL_S", "60")),
            fault_duration_s=float(os.getenv("FAULT_DURATION_S", "2")),
        )


def joint_positions(t: float) -> list[float]:
    """Sinusoidal joint trajectories with phase offsets."""
    return [
        DEFAULT_JOINT_AMPLITUDE
        * math.sin(2 * math.pi * DEFAULT_JOINT_FREQUENCY_HZ * t + i * 0.9)
        for i in range(NUM_JOINTS)
    ]


def joint_currents(positions: list[float], error_active: bool) -> list[float]:
    """Rough proxy: higher |position| and faults increase current draw."""
    scale = 2.5 if error_active else 1.0
    return [round(abs(p) * 1.2 * scale + 0.15, 3) for p in positions]


def error_code(t: float, interval_s: float, duration_s: float) -> int:
    """Periodic fault window (e.g. every 60 s for 2 s)."""
    phase = t % interval_s
    return 1001 if phase < duration_s else 0


def build_payload(robot_id: str, t: float, cfg: Config) -> dict:
    err = error_code(t, cfg.fault_interval_s, cfg.fault_duration_s)
    positions = joint_positions(t)
    return {
        "robot_id": robot_id,
        "time": datetime.now(timezone.utc).isoformat(),
        "joint_positions": positions,
        "joint_currents": joint_currents(positions, err != 0),
        "temperature_c": round(38.0 + 4.0 * math.sin(t / 30.0) + (8.0 if err else 0.0), 2),
        "error_code": err,
    }


def main() -> None:
    cfg = Config.from_env()
    topic = f"robots/{cfg.robot_id}/telemetry"
    period_s = 1.0 / cfg.publish_hz

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(cfg.mqtt_host, cfg.mqtt_port, keepalive=30)

    start = time.monotonic()
    running = True

    def shutdown(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"Publishing to mqtt://{cfg.mqtt_host}:{cfg.mqtt_port}/{topic} at {cfg.publish_hz} Hz")
    messages = 0

    try:
        while running:
            t = time.monotonic() - start
            payload = build_payload(cfg.robot_id, t, cfg)
            client.publish(topic, json.dumps(payload), qos=0)
            messages += 1
            if messages % int(cfg.publish_hz * 5) == 0:
                print(f"[{cfg.robot_id}] msgs={messages} error_code={payload['error_code']}")
            time.sleep(period_s)
    finally:
        client.disconnect()
        print("Simulator stopped.")


if __name__ == "__main__":
    main()
    sys.exit(0)

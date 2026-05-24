"""FastAPI ingest service: MQTT -> Postgres (F2).

- Subscribes to robots/+/telemetry
- Validates payloads with Pydantic
- Batches inserts to keep load low (every BATCH_INTERVAL_S or BATCH_SIZE messages)
- Exposes /health and /stats for observability
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

from models import RobotTelemetry

LOG = logging.getLogger("ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "robots/+/telemetry")
POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://robotics:robotics@postgres:5432/telemetry",
)
BATCH_INTERVAL_S = float(os.getenv("BATCH_INTERVAL_S", "0.5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

INSERT_SQL = """
INSERT INTO telemetry
  (time, robot_id, joint_positions, joint_currents, temperature_c, error_code, payload_raw)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


class Stats:
    received: int = 0
    inserted: int = 0
    dropped: int = 0
    last_insert: datetime | None = None


stats = Stats()
buffer: list[tuple] = []
buffer_lock = asyncio.Lock()


async def flush_loop(pool: AsyncConnectionPool, stop: asyncio.Event) -> None:
    """Periodically drain the buffer into Postgres."""
    while not stop.is_set():
        await asyncio.sleep(BATCH_INTERVAL_S)
        async with buffer_lock:
            if not buffer:
                continue
            batch = buffer[:]
            buffer.clear()
        try:
            async with pool.connection() as conn, conn.cursor() as cur:
                await cur.executemany(INSERT_SQL, batch)
                await conn.commit()
            stats.inserted += len(batch)
            stats.last_insert = datetime.utcnow()
            LOG.info("inserted batch size=%d total=%d", len(batch), stats.inserted)
        except Exception:
            stats.dropped += len(batch)
            LOG.exception("insert failed, dropped %d rows", len(batch))


def make_mqtt_client(loop: asyncio.AbstractEventLoop) -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(c, _ud, _flags, reason_code, _props):
        LOG.info("MQTT connected rc=%s, subscribing to %s", reason_code, MQTT_TOPIC)
        c.subscribe(MQTT_TOPIC)

    def on_message(_c, _ud, msg):
        stats.received += 1
        try:
            data = json.loads(msg.payload.decode())
            telem = RobotTelemetry.model_validate(data)
        except Exception:
            stats.dropped += 1
            return

        row = (
            telem.time,
            telem.robot_id,
            telem.joint_positions,
            telem.joint_currents,
            telem.temperature_c,
            telem.error_code,
            json.dumps(data),
        )
        # paho callback runs on its own thread -> schedule append on the loop
        asyncio.run_coroutine_threadsafe(_append(row), loop)

    client.on_connect = on_connect
    client.on_message = on_message
    return client


async def _append(row: tuple) -> None:
    async with buffer_lock:
        buffer.append(row)
        if len(buffer) >= BATCH_SIZE:
            LOG.debug("buffer reached BATCH_SIZE=%d", BATCH_SIZE)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    LOG.info("Starting ingest: mqtt=%s:%s pg=%s", MQTT_HOST, MQTT_PORT, POSTGRES_URL)
    stop = asyncio.Event()

    pool = AsyncConnectionPool(POSTGRES_URL, min_size=1, max_size=4, open=False)
    await pool.open()

    loop = asyncio.get_running_loop()
    client = make_mqtt_client(loop)
    client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()

    flusher = asyncio.create_task(flush_loop(pool, stop))

    try:
        yield
    finally:
        LOG.info("Stopping ingest")
        stop.set()
        flusher.cancel()
        client.loop_stop()
        client.disconnect()
        await pool.close()


app = FastAPI(title="cloud-robotics-monitor ingest", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/stats")
async def get_stats() -> dict:
    return {
        "received": stats.received,
        "inserted": stats.inserted,
        "dropped": stats.dropped,
        "buffer_size": len(buffer),
        "last_insert": stats.last_insert.isoformat() if stats.last_insert else None,
    }

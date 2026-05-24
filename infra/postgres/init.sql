-- Initial schema for cloud-robotics-monitor
-- Plain Postgres for now; TimescaleDB hypertable conversion comes later.

CREATE TABLE IF NOT EXISTS telemetry (
    time            TIMESTAMPTZ      NOT NULL,
    robot_id        TEXT             NOT NULL,
    joint_positions DOUBLE PRECISION[] NOT NULL,
    joint_currents  DOUBLE PRECISION[] NOT NULL,
    temperature_c   DOUBLE PRECISION,
    error_code      INTEGER          NOT NULL DEFAULT 0,
    payload_raw     JSONB
);

CREATE INDEX IF NOT EXISTS telemetry_robot_time_idx
    ON telemetry (robot_id, time DESC);

CREATE TABLE IF NOT EXISTS anomalies (
    time      TIMESTAMPTZ NOT NULL,
    robot_id  TEXT        NOT NULL,
    joint     INTEGER     NOT NULL,
    value     DOUBLE PRECISION NOT NULL,
    z_score   DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS anomalies_robot_time_idx
    ON anomalies (robot_id, time DESC);

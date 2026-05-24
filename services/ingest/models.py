"""Pydantic models for telemetry messages."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RobotTelemetry(BaseModel):
    """One telemetry sample emitted by the simulator (see F1)."""

    robot_id: str
    time: datetime
    joint_positions: list[float] = Field(min_length=1)
    joint_currents: list[float] = Field(min_length=1)
    temperature_c: float
    error_code: int = 0

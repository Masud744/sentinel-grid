from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SensorDataPayload(BaseModel):
    fire_signal: int = Field(..., ge=0, le=1, description="Binary fire signal (0 or 1)")
    gas_level_raw: float = Field(..., ge=0.0, le=5000.0, description="Raw gas sensor PPM reading")
    water_level_raw: float = Field(..., ge=0.0, le=100.0, description="Raw water level sensor depth in cm")
    occupancy_raw: int = Field(..., ge=0, le=1, description="Binary PIR occupancy sensor reading")

    @field_validator("fire_signal", "occupancy_raw")
    @classmethod
    def validate_binary_signals(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("Binary sensor signals must be strictly 0 or 1")
        return v


class IngestionRequest(BaseModel):
    sequence_id: int = Field(..., gt=0, description="Monotonically increasing sequence ID per zone")
    timestamp: Optional[int] = Field(None, description="Unix timestamp of sampling")
    sensors: SensorDataPayload


class ActuationCommand(BaseModel):
    buzzer: bool
    led: str  # 'GREEN', 'YELLOW', 'RED'
    relay_power_cut: bool


class IngestionResponse(BaseModel):
    status: str = "success"
    zone_id: str
    zone_name: str
    risk_score: float
    state: str  # 'SAFE', 'WARNING', 'CRITICAL'
    actuation: ActuationCommand

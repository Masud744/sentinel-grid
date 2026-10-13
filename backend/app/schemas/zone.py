from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class SensorStatus(BaseModel):
    sensor_type: str
    unit: str


class ZoneStatusResponse(BaseModel):
    id: str
    name: str
    lab_type: str
    is_active: bool
    connection_status: str  # 'ONLINE', 'OFFLINE'
    current_risk_score: float
    current_state: str  # 'SAFE', 'WARNING', 'CRITICAL'
    occupancy_status: str  # 'OCCUPIED', 'VACANT'
    is_trending_up: Optional[bool] = False  # Bonus 2 trend indicator
    trend_slope: Optional[float] = 0.0
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


class PriorityQueueItem(BaseModel):
    rank: int
    zone_id: str
    zone_name: str
    risk_score: float
    state: str
    occupancy_factor: float
    duration_critical_seconds: float
    reason: str

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ManualOverrideRequest(BaseModel):
    zone_id: str
    forced_state: str = Field(..., description="'SAFE', 'WARNING', 'CRITICAL'")
    reason: str = Field(..., min_length=5, description="Reason for override")


class SystemHealthResponse(BaseModel):
    status: str
    database_connected: bool
    active_zones_count: int
    online_nodes_count: int
    open_critical_incidents_count: int
    websocket_connections_count: int
    uptime_seconds: float
    details: Dict[str, Any]

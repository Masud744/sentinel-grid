from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class IncidentAcknowledgementResponse(BaseModel):
    acknowledged_by: str
    acknowledged_at: datetime


class IncidentResponse(BaseModel):
    id: str
    zone_id: str
    zone_name: str
    risk_score: float
    state: str
    cause: str
    opened_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledgement: Optional[IncidentAcknowledgementResponse] = None

    class Config:
        from_attributes = True


class IncidentAckResponse(BaseModel):
    message: str = "Incident acknowledged successfully"
    incident_id: str
    acknowledged_by: str
    acknowledged_at: datetime

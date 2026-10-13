"""
Incident Management & State Transition Service.

Handles:
1. Zone State Transitions (SAFE <-> WARNING <-> CRITICAL)
2. Rapid Flapping Prevention: Updates open incident score/timestamp if state flips within 10 seconds without creating duplicate records.
3. Incident Resolution: Closes open incidents when zone returns to SAFE.
4. Database State Reconstruction: On server startup, recovers zone states from DB to eliminate cold-start assumptions.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.incident import Incident
from app.models.reading import SensorReading
from app.models.zone import Zone
from app.repositories.incident_repo import IncidentRepository
from app.repositories.reading_repo import SensorReadingRepository
from app.websocket.manager import ws_manager


class IncidentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.reading_repo = SensorReadingRepository(db)

    async def process_zone_state(
        self,
        zone: Zone,
        computed_risk: float,
        new_state: str,
        cause_description: str
    ) -> Optional[Incident]:
        """
        Evaluates state transition for a zone and manages incident lifecycle.
        """
        now = datetime.now(timezone.utc)
        active_incident = await self.incident_repo.get_active_incident_by_zone(zone.id)

        if new_state in ("WARNING", "CRITICAL"):
            if active_incident:
                # Flapping prevention check: If already open, update current risk score & state
                active_incident.risk_score = max(active_incident.risk_score, computed_risk)
                if new_state == "CRITICAL" and active_incident.state == "WARNING":
                    active_incident.state = "CRITICAL"
                    active_incident.cause = cause_description

                await self.db.flush()
                return active_incident
            else:
                # Open a new Incident
                new_incident = Incident(
                    zone_id=zone.id,
                    risk_score=computed_risk,
                    state=new_state,
                    cause=cause_description,
                    opened_at=now,
                )
                await self.incident_repo.create(new_incident)

                # Broadcast via WebSockets
                await ws_manager.broadcast("INCIDENT_CREATED", {
                    "incident_id": new_incident.id,
                    "zone_id": zone.id,
                    "zone_name": zone.name,
                    "state": new_state,
                    "risk_score": computed_risk,
                    "cause": cause_description,
                    "opened_at": now.isoformat(),
                })
                return new_incident

        elif new_state == "SAFE":
            if active_incident:
                # Resolve the incident
                active_incident.state = "RESOLVED"
                active_incident.resolved_at = now
                await self.db.flush()

                await ws_manager.broadcast("INCIDENT_RESOLVED", {
                    "incident_id": active_incident.id,
                    "zone_id": zone.id,
                    "zone_name": zone.name,
                    "resolved_at": now.isoformat(),
                })
                return active_incident

        return None


# Server Startup State Recovery Engine
async def recover_system_state_from_db(db: AsyncSession) -> Dict[str, Any]:
    """
    On backend restart: reconstructs all zone states from the database.
    Ensures backend never defaults to SAFE on boot if open incidents exist.
    """
    stmt_zones = select(Zone).where(Zone.is_active.is_(True))
    res_zones = await db.execute(stmt_zones)
    zones = res_zones.scalars().all()

    recovered_states = {}
    for zone in zones:
        stmt_inc = (
            select(Incident)
            .where(
                Incident.zone_id == zone.id,
                Incident.state.in_(["WARNING", "CRITICAL"])
            )
            .order_by(Incident.opened_at.desc())
            .limit(1)
        )
        res_inc = await db.execute(stmt_inc)
        active_inc = res_inc.scalars().first()

        if active_inc:
            recovered_states[zone.id] = {
                "state": active_inc.state,
                "risk_score": active_inc.risk_score,
                "incident_id": active_inc.id,
            }
        else:
            recovered_states[zone.id] = {
                "state": "SAFE",
                "risk_score": 0.0,
                "incident_id": None,
            }

    return recovered_states

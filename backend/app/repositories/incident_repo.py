from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.models.incident import Incident
from app.models.acknowledgement import Acknowledgement
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, db: AsyncSession):
        super().__init__(Incident, db)

    async def get_active_incident_by_zone(self, zone_id: str) -> Optional[Incident]:
        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.zone),
                selectinload(Incident.acknowledgement).selectinload(Acknowledgement.user)
            )
            .where(
                Incident.zone_id == zone_id,
                Incident.state.in_(["WARNING", "CRITICAL"])
            )
            .order_by(Incident.opened_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_incidents(
        self,
        zone_id: Optional[str] = None,
        state: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Incident]:
        filters = []
        if zone_id:
            filters.append(Incident.zone_id == zone_id)
        if state:
            filters.append(Incident.state == state)
        if from_date:
            filters.append(Incident.opened_at >= from_date)
        if to_date:
            filters.append(Incident.opened_at <= to_date)

        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.zone),
                selectinload(Incident.acknowledgement).selectinload(Acknowledgement.user)
            )
        )
        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Incident.opened_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_acknowledgement(self, incident_id: str, user_id: str) -> Acknowledgement:
        """
        Creates an acknowledgement record.
        Enforces atomic single-write via DB UniqueConstraint on `incident_id`.
        Raises IntegrityError if already acknowledged (409 Conflict).
        """
        ack = Acknowledgement(incident_id=incident_id, user_id=user_id)
        self.db.add(ack)
        await self.db.flush()
        return ack

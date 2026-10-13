from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reading import SensorReading
from app.repositories.base import BaseRepository


class SensorReadingRepository(BaseRepository[SensorReading]):
    def __init__(self, db: AsyncSession):
        super().__init__(SensorReading, db)

    async def get_by_sequence(self, zone_id: str, sequence_id: int) -> Optional[SensorReading]:
        """Checks if sequence_id has already been processed for this zone (de-duplication)."""
        stmt = (
            select(SensorReading)
            .where(
                SensorReading.zone_id == zone_id,
                SensorReading.sequence_id == sequence_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_latest_reading(self, zone_id: str) -> Optional[SensorReading]:
        stmt = (
            select(SensorReading)
            .where(SensorReading.zone_id == zone_id)
            .order_by(SensorReading.received_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

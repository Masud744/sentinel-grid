from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.zone import Zone
from app.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[Zone]):
    def __init__(self, db: AsyncSession):
        super().__init__(Zone, db)

    async def get_by_api_key(self, api_key: str) -> Optional[Zone]:
        stmt = (
            select(Zone)
            .options(selectinload(Zone.sensors))
            .where(Zone.api_key == api_key)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_active_zones(self) -> List[Zone]:
        stmt = (
            select(Zone)
            .options(selectinload(Zone.sensors))
            .where(Zone.is_active.is_(True))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

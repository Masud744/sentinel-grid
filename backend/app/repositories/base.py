from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id_val: Any) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id_val)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_all(self) -> List[ModelType]:
        stmt = select(self.model)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.flush()
        return obj

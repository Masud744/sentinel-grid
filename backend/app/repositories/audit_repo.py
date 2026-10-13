from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(AuditLog, db)

    async def log_action(
        self,
        action: str,
        target_type: str,
        target_id: str,
        actor_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        audit = AuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
        self.db.add(audit)
        await self.db.flush()
        return audit

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.bonus.trend.service import get_zone_trend_analysis

router = APIRouter(prefix="/zones", tags=["Bonus Trend Module"])


@router.get("/{zone_id}/trend")
async def get_zone_trend(zone_id: str, db: AsyncSession = Depends(get_db)):
    """
    Read-only endpoint exposing isolated short-term risk trend analysis.
    Controlled by BONUS_TREND_ENABLED feature flag.
    """
    return await get_zone_trend_analysis(zone_id, db)

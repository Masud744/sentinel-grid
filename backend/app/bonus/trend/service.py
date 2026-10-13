"""
Bonus Module 2: Isolated Trend Service.

Provides trend analysis for zones when feature flag BONUS_TREND_ENABLED is True.
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.reading import SensorReading
from app.bonus.trend.calculator import calculate_risk_trend


async def get_zone_trend_analysis(zone_id: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Fetches the last 15 readings for a zone and calculates trend metrics.
    If feature flag BONUS_TREND_ENABLED is False, returns disabled status gracefully.
    """
    if not settings.BONUS_TREND_ENABLED:
        return {
            "enabled": False,
            "is_trending_up": False,
            "slope": 0.0,
            "moving_avg": 0.0,
            "message": "Bonus trend module is disabled via configuration."
        }

    stmt = (
        select(SensorReading.computed_risk_score)
        .where(SensorReading.zone_id == zone_id)
        .order_by(SensorReading.received_at.desc())
        .limit(15)
    )
    result = await db.execute(stmt)
    scores = list(reversed([row[0] for row in result.fetchall()]))

    trend_metrics = calculate_risk_trend(scores)
    trend_metrics["enabled"] = True
    return trend_metrics

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories.zone_repo import ZoneRepository
from app.repositories.reading_repo import SensorReadingRepository
from app.repositories.incident_repo import IncidentRepository
from app.schemas.zone import ZoneStatusResponse, PriorityQueueItem
from app.services.debounce import get_zone_debouncer
from app.services.priority_ranking import rank_critical_incidents
from app.bonus.trend.service import get_zone_trend_analysis

router = APIRouter(prefix="/zones", tags=["Zones Management"])


@router.get("")
@router.get("/status")
async def get_all_zones_status(db: AsyncSession = Depends(get_db)):
    """
    Returns current live state, risk scores, sensor connectivity, and priority queue for all active zones.
    """
    zone_repo = ZoneRepository(db)
    reading_repo = SensorReadingRepository(db)
    incident_repo = IncidentRepository(db)

    zones = await zone_repo.list_active_zones()

    zone_responses: List[ZoneStatusResponse] = []
    critical_zones_for_ranking: List[Dict[str, Any]] = []

    for zone in zones:
        latest_reading = await reading_repo.get_latest_reading(zone.id)
        active_inc = await incident_repo.get_active_incident_by_zone(zone.id)

        debouncer = get_zone_debouncer(zone.id)
        is_online = debouncer.is_online()

        if active_inc:
            curr_state = active_inc.state
            curr_score = active_inc.risk_score
        elif latest_reading:
            curr_score = latest_reading.computed_risk_score
            curr_state = "CRITICAL" if curr_score >= 65 else ("WARNING" if curr_score >= 30 else "SAFE")
        else:
            curr_score = 0.0
            curr_state = "SAFE"

        occupancy_str = "OCCUPIED" if (latest_reading and latest_reading.occupancy_raw == 1) else "VACANT"

        # Fetch Bonus 2 trend metrics
        trend_info = await get_zone_trend_analysis(zone.id, db)

        z_resp = ZoneStatusResponse(
            id=zone.id,
            name=zone.name,
            lab_type=zone.lab_type,
            is_active=zone.is_active,
            connection_status="ONLINE" if is_online else "OFFLINE",
            current_risk_score=curr_score,
            current_state=curr_state,
            occupancy_status=occupancy_str,
            is_trending_up=trend_info.get("is_trending_up", False),
            trend_slope=trend_info.get("slope", 0.0),
            last_updated=latest_reading.received_at if latest_reading else None
        )
        zone_responses.append(z_resp)

        if curr_state == "CRITICAL":
            critical_zones_for_ranking.append({
                "zone_id": zone.id,
                "zone_name": zone.name,
                "risk_score": curr_score,
                "state": curr_state,
                "occupancy_factor": 1.0 if occupancy_str == "OCCUPIED" else 0.3,
                "critical_since": active_inc.opened_at if active_inc else None,
            })

    priority_queue = rank_critical_incidents(critical_zones_for_ranking)

    return {
        "zones": zone_responses,
        "priority_queue": priority_queue
    }

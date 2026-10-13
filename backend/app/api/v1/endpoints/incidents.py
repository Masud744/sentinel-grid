from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.repositories.incident_repo import IncidentRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.incident import IncidentResponse, IncidentAckResponse, IncidentAcknowledgementResponse
from app.models.user import User
from app.auth.rbac import get_current_user, require_staff_or_admin
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/incidents", tags=["Incidents & Alerts"])


@router.get("", response_model=List[IncidentResponse])
async def get_incidents(
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    state: Optional[str] = Query(None, description="Filter by state (WARNING, CRITICAL, RESOLVED)"),
    from_date: Optional[datetime] = Query(None, description="Filter from timestamp"),
    to_date: Optional[datetime] = Query(None, description="Filter to timestamp"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns historical incident records, filterable by date range, zone, and state.
    """
    repo = IncidentRepository(db)
    incidents = await repo.list_incidents(
        zone_id=zone_id,
        state=state,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )

    responses = []
    for inc in incidents:
        ack_resp = None
        if inc.acknowledgement:
            ack_resp = IncidentAcknowledgementResponse(
                acknowledged_by=inc.acknowledgement.user.username if inc.acknowledgement.user else "Unknown",
                acknowledged_at=inc.acknowledgement.acknowledged_at,
            )

        responses.append(IncidentResponse(
            id=inc.id,
            zone_id=inc.zone_id,
            zone_name=inc.zone.name if inc.zone else "Unknown",
            risk_score=inc.risk_score,
            state=inc.state,
            cause=inc.cause,
            opened_at=inc.opened_at,
            resolved_at=inc.resolved_at,
            acknowledgement=ack_resp,
        ))

    return responses


@router.post("/{incident_id}/ack", response_model=IncidentAckResponse)
@router.post("/{incident_id}/acknowledge", response_model=IncidentAckResponse)
async def acknowledge_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin)
):
    """
    Acknowledges an active alert.
    Enforces atomic single-acknowledgement using DB-level unique constraint (409 Conflict if race occurs).
    """
    incident_repo = IncidentRepository(db)
    audit_repo = AuditRepository(db)

    incident = await incident_repo.get_by_id(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )

    try:
        ack = await incident_repo.add_acknowledgement(incident.id, current_user.id)
        
        # Log Audit Trail
        await audit_repo.log_action(
            action="ACKNOWLEDGE_INCIDENT",
            target_type="INCIDENT",
            target_id=incident.id,
            actor_id=current_user.id,
            details={"username": current_user.username, "role": current_user.role.name if current_user.role else "staff"}
        )

        await db.commit()

        # Broadcast via WebSocket
        await ws_manager.broadcast("INCIDENT_ACKNOWLEDGED", {
            "incident_id": incident.id,
            "acknowledged_by": current_user.username,
            "acknowledged_at": ack.acknowledged_at.isoformat(),
        })

        return IncidentAckResponse(
            message="Incident acknowledged successfully",
            incident_id=incident.id,
            acknowledged_by=current_user.username,
            acknowledged_at=ack.acknowledged_at,
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident has already been acknowledged by another responder"
        )

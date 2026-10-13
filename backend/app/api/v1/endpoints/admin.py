import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.schemas.admin import ManualOverrideRequest, SystemHealthResponse
from app.models.user import User
from app.models.zone import Zone
from app.models.incident import Incident
from app.models.reading import SensorReading
from app.models.audit import AuditLog
from app.repositories.zone_repo import ZoneRepository
from app.repositories.incident_repo import IncidentRepository
from app.repositories.audit_repo import AuditRepository
from app.auth.rbac import require_admin
from app.services.debounce import _debounce_registry
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

SERVER_START_TIME = time.time()


@router.post("/override")
async def manual_zone_override(
    payload: ManualOverrideRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Admin-only manual override endpoint.
    Forces a zone into a specified state ('SAFE', 'WARNING', 'CRITICAL') with audit logging.
    Enforces service-level RBAC (rejects staff tokens with 403 Forbidden).
    """
    if payload.forced_state not in ("SAFE", "WARNING", "CRITICAL"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid forced state. Must be 'SAFE', 'WARNING', or 'CRITICAL'."
        )

    zone_repo = ZoneRepository(db)
    zone = await zone_repo.get_by_id(payload.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    incident_repo = IncidentRepository(db)
    audit_repo = AuditRepository(db)

    now = datetime.now(timezone.utc)
    active_inc = await incident_repo.get_active_incident_by_zone(zone.id)

    if payload.forced_state in ("WARNING", "CRITICAL"):
        if active_inc:
            active_inc.state = payload.forced_state
            active_inc.cause = f"MANUAL OVERRIDE BY ADMIN ({admin_user.username}): {payload.reason}"
        else:
            new_inc = Incident(
                zone_id=zone.id,
                risk_score=payload.forced_state == "CRITICAL" and 90.0 or 45.0,
                state=payload.forced_state,
                cause=f"MANUAL OVERRIDE BY ADMIN ({admin_user.username}): {payload.reason}",
                opened_at=now,
            )
            await incident_repo.create(new_inc)

    elif payload.forced_state == "SAFE":
        if active_inc:
            active_inc.state = "RESOLVED"
            active_inc.resolved_at = now

    # Log Audit Trail
    await audit_repo.log_action(
        action="MANUAL_OVERRIDE",
        target_type="ZONE",
        target_id=zone.id,
        actor_id=admin_user.id,
        details={
            "forced_state": payload.forced_state,
            "reason": payload.reason,
            "admin_username": admin_user.username
        }
    )

    await db.commit()

    # Broadcast WebSocket Event
    await ws_manager.broadcast("MANUAL_OVERRIDE_EXECUTED", {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "forced_state": payload.forced_state,
        "admin_username": admin_user.username,
        "reason": payload.reason,
    })

    return {
        "status": "success",
        "message": f"Zone '{zone.name}' state manually overridden to {payload.forced_state}",
        "zone_id": zone.id,
        "forced_state": payload.forced_state,
        "executed_by": admin_user.username,
    }


@router.get("/health", response_model=SystemHealthResponse)
async def system_health(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Admin-only system health diagnostic view.
    """
    # Count active zones
    stmt_zones = select(func.count(Zone.id)).where(Zone.is_active.is_(True))
    res_zones = await db.execute(stmt_zones)
    active_zones_count = res_zones.scalar_one()

    # Count open critical incidents
    stmt_inc = select(func.count(Incident.id)).where(Incident.state == "CRITICAL")
    res_inc = await db.execute(stmt_inc)
    open_critical_count = res_inc.scalar_one()

    # Count online nodes based on debouncer heartbeat
    online_count = sum(1 for debouncer in _debounce_registry.values() if debouncer.is_online())

    uptime = time.time() - SERVER_START_TIME

    return SystemHealthResponse(
        status="HEALTHY",
        database_connected=True,
        active_zones_count=active_zones_count,
        online_nodes_count=online_count,
        open_critical_incidents_count=open_critical_count,
        websocket_connections_count=len(ws_manager.active_connections),
        uptime_seconds=round(uptime, 2),
        details={
            "python_version": "3.10+",
            "server_time": datetime.now(timezone.utc).isoformat(),
        }
    )


class ZoneToggleRequest(BaseModel):
    is_active: bool


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Returns recent system audit logs with actor info for admin dashboard.
    """
    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [
        {
            "id": log.id,
            "actor": log.actor.username if log.actor else "System",
            "action": log.action,
            "details": str(log.details) if log.details else "",
            "timestamp": log.created_at.isoformat() if log.created_at else "",
        }
        for log in logs
    ]


@router.patch("/zones/{zone_id}")
async def toggle_zone(
    zone_id: str,
    payload: ZoneToggleRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Enables or disables telemetry collection for a specific zone.
    """
    zone_repo = ZoneRepository(db)
    zone = await zone_repo.get_by_id(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone.is_active = payload.is_active
    audit_repo = AuditRepository(db)
    await audit_repo.log_action(
        action="TOGGLE_ZONE_STATUS",
        target_type="ZONE",
        target_id=zone.id,
        actor_id=admin_user.id,
        details={"zone_name": zone.name, "is_active": payload.is_active}
    )
    await db.commit()
    return {"status": "success", "zone_id": zone.id, "is_active": zone.is_active}


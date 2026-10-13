from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.ingest import IngestionRequest, IngestionResponse
from app.repositories.zone_repo import ZoneRepository
from app.repositories.reading_repo import SensorReadingRepository
from app.models.reading import SensorReading
from app.services.debounce import get_zone_debouncer
from app.services.risk_fusion import compute_risk_score
from app.services.actuation import evaluate_actuation
from app.services.incident_service import IncidentService
from app.websocket.manager import ws_manager

router = APIRouter(tags=["Telemetry Ingestion"])


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_telemetry(
    payload: IngestionRequest,
    x_zone_api_key: Optional[str] = Header(None, alias="X-Zone-API-Key"),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests raw sensor readings from zone node.
    Enforces per-zone API key authentication, payload bounds validation,
    sequence deduplication, and server-side risk score calculation.
    """
    if not x_zone_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Zone-API-Key header"
        )

    zone_repo = ZoneRepository(db)
    zone = await zone_repo.get_by_api_key(x_zone_api_key)
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unregistered or invalid zone API key"
        )

    reading_repo = SensorReadingRepository(db)

    # De-duplication check by sequence_id
    existing_seq = await reading_repo.get_by_sequence(zone.id, payload.sequence_id)
    if existing_seq:
        # Return previous computed response without double-counting
        actuation = evaluate_actuation(existing_seq.computed_risk_score >= 65 and "CRITICAL" or "SAFE")
        return IngestionResponse(
            status="duplicate_ignored",
            zone_id=zone.id,
            zone_name=zone.name,
            risk_score=existing_seq.computed_risk_score,
            state="CRITICAL" if existing_seq.computed_risk_score >= 65 else ("WARNING" if existing_seq.computed_risk_score >= 30 else "SAFE"),
            actuation=actuation
        )

    # Debounce signals
    debouncer = get_zone_debouncer(zone.id)
    debounced_fire = debouncer.update_fire(payload.sensors.fire_signal)
    debounced_occ = debouncer.update_occupancy(payload.sensors.occupancy_raw)
    valid_gas, valid_water = debouncer.filter_gas_water(
        payload.sensors.gas_level_raw,
        payload.sensors.water_level_raw
    )

    # Compute server-side risk score & state
    risk_score, state, breakdown = compute_risk_score(
        fire_debounced=debounced_fire,
        gas_raw=valid_gas,
        water_raw=valid_water,
        occupancy_raw=debounced_occ
    )

    # Determine cause string for incidents
    causes = []
    if debounced_fire == 1:
        causes.append("Debounced Fire Alarm")
    if valid_gas > 300.0:
        causes.append(f"High Gas ({valid_gas:.1f} PPM)")
    if valid_water > 10.0:
        causes.append(f"Water Leakage ({valid_water:.1f} cm)")
    cause_desc = " + ".join(causes) if causes else "Normal Environment Readings"

    # Save Sensor Reading
    reading = SensorReading(
        zone_id=zone.id,
        sequence_id=payload.sequence_id,
        fire_signal=payload.sensors.fire_signal,
        gas_level_raw=payload.sensors.gas_level_raw,
        water_level_raw=payload.sensors.water_level_raw,
        occupancy_raw=payload.sensors.occupancy_raw,
        computed_risk_score=risk_score,
    )
    await reading_repo.create(reading)

    # Process State Transition & Incident Lifecycle
    incident_service = IncidentService(db)
    await incident_service.process_zone_state(zone, risk_score, state, cause_desc)

    await db.commit()

    # Hardware Actuation Command Evaluation
    actuation = evaluate_actuation(state)

    # Broadcast Live Telemetry to WebSockets
    await ws_manager.broadcast("ZONE_TELEMETRY_UPDATED", {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "risk_score": risk_score,
        "state": state,
        "occupancy": "OCCUPIED" if debounced_occ == 1 else "VACANT",
        "actuation": actuation.model_dump(),
        "breakdown": breakdown,
    })

    return IngestionResponse(
        status="success",
        zone_id=zone.id,
        zone_name=zone.name,
        risk_score=risk_score,
        state=state,
        actuation=actuation,
    )

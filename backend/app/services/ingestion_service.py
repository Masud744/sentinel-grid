import uuid
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

from app.models.zone import Zone
from app.models.sensor import Sensor
from app.models.reading import SensorReading
from app.models.incident import Incident
from app.repositories.zone_repo import ZoneRepository
from app.repositories.sensor_repo import SensorRepository
from app.repositories.reading_repo import SensorReadingRepository
from app.repositories.incident_repo import IncidentRepository
from app.services.risk_fusion import compute_risk_score

class IngestionService:
    """Orchestrates sensor payload ingestion, de‑duplication, risk calculation and incident logging."""

    def __init__(self, db_session):
        self.zone_repo = ZoneRepository(db_session)
        self.sensor_repo = SensorRepository(db_session)
        self.reading_repo = SensorReadingRepository(db_session)
        self.incident_repo = IncidentRepository(db_session)
        self.db = db_session

    async def ingest(self, zone_id: str, sequence_id: int, sensor_payload: Dict[str, Any]) -> Tuple[float, str, Dict[str, Any]]:
        # 1️⃣ Ensure zone exists
        zone: Zone = await self.zone_repo.get_by_id(zone_id)
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")

        # 2️⃣ De‑duplication: has this sequence been processed?
        existing = await self.reading_repo.get_by_sequence(zone_id, sequence_id)
        if existing:
            # Return previously calculated risk – idempotent behaviour
            return existing.risk_score, existing.state, {}

        # 3️⃣ Persist raw sensor reading
        reading = SensorReading(
            id=str(uuid.uuid4()),
            zone_id=zone_id,
            sequence_id=sequence_id,
            fire_signal=sensor_payload["fire_signal"],
            gas_level_raw=sensor_payload["gas_level_raw"],
            water_level_raw=sensor_payload["water_level_raw"],
            occupancy_raw=sensor_payload["occupancy_raw"],
            received_at=datetime.now(timezone.utc),
        )
        await self.reading_repo.create(reading)

        # 4️⃣ Compute risk using the shared fusion engine
        risk_score, state, breakdown = compute_risk_score(
            fire_debounced=reading.fire_signal,
            gas_raw=reading.gas_level_raw,
            water_raw=reading.water_level_raw,
            occupancy_raw=reading.occupancy_raw,
        )

        # 5️⃣ Store Incident (audit trail) – linking to the reading
        incident = Incident(
            id=str(uuid.uuid4()),
            zone_id=zone_id,
            reading_id=reading.id,
            risk_score=risk_score,
            state=state,
            occurred_at=reading.received_at,
        )
        await self.incident_repo.create(incident)

        # 6️⃣ Commit transaction – caller will handle commit/rollback
        return risk_score, state, breakdown

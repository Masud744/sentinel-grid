import sys
import os
import asyncio
import random
from datetime import datetime, timedelta, timezone

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))


from app.auth.password import get_password_hash
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.role import Role
from app.models.user import User
from app.models.zone import Zone
from app.models.sensor import Sensor
from app.models.reading import SensorReading
from app.models.incident import Incident
from app.models.acknowledgement import Acknowledgement
from app.models.audit import AuditLog


async def seed():
    db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "scs_rg.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print("Removed old database file.")
        except Exception:
            pass

    print("Initializing Database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select
        existing_roles = await db.execute(select(Role))
        if existing_roles.scalars().first():
            print("Database already contains data. Cleaning and re-seeding...")
            await db.execute(Base.metadata.tables["acknowledgements"].delete())
            await db.execute(Base.metadata.tables["incidents"].delete())
            await db.execute(Base.metadata.tables["audit_logs"].delete())
            await db.execute(Base.metadata.tables["sensor_readings"].delete())
            await db.execute(Base.metadata.tables["sensors"].delete())
            await db.execute(Base.metadata.tables["zones"].delete())
            await db.execute(Base.metadata.tables["refresh_tokens"].delete())
            await db.execute(Base.metadata.tables["users"].delete())
            await db.execute(Base.metadata.tables["roles"].delete())
            await db.commit()

        print("Seeding Roles...")
        role_admin = Role(id=1, name="admin")
        role_staff = Role(id=2, name="staff")
        db.add_all([role_admin, role_staff])
        await db.flush()

        print("Seeding Users...")
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role_id=role_admin.id,
        )
        staff_user = User(
            username="staff",
            password_hash=get_password_hash("staff123"),
            role_id=role_staff.id,
        )
        db.add_all([admin_user, staff_user])
        await db.flush()

        print("Seeding Zones...")
        zone_iot = Zone(
            name="IoT Lab",
            lab_type="iot_lab",
            api_key="zone-key-iot-lab-001",
        )
        zone_server = Zone(
            name="Server Room",
            lab_type="server_room",
            api_key="zone-key-server-room-002",
        )
        zone_ds = Zone(
            name="Data Science Lab",
            lab_type="ds_lab",
            api_key="zone-key-ds-lab-003",
        )
        db.add_all([zone_iot, zone_server, zone_ds])
        await db.flush()

        print("Seeding Sensors...")
        sensors = [
            Sensor(zone_id=zone_iot.id, sensor_type="fire", unit="binary"),
            Sensor(zone_id=zone_iot.id, sensor_type="gas", unit="ppm"),
            Sensor(zone_id=zone_iot.id, sensor_type="occupancy", unit="binary"),
            
            Sensor(zone_id=zone_server.id, sensor_type="fire", unit="binary"),
            Sensor(zone_id=zone_server.id, sensor_type="water", unit="cm"),
            Sensor(zone_id=zone_server.id, sensor_type="occupancy", unit="binary"),

            Sensor(zone_id=zone_ds.id, sensor_type="fire", unit="binary"),
            Sensor(zone_id=zone_ds.id, sensor_type="water", unit="cm"),
            Sensor(zone_id=zone_ds.id, sensor_type="occupancy", unit="binary"),
        ]
        db.add_all(sensors)
        await db.flush()

        print("Seeding 10,000+ historical sensor readings...")
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=15)
        step_seconds = 120  # Every 2 minutes for 15 days = ~10,800 total readings across 3 zones

        readings_batch = []
        seq_counters = {zone_iot.id: 1, zone_server.id: 1, zone_ds.id: 1}
        zones = [zone_iot, zone_server, zone_ds]

        total_readings = 0
        current_time = start_time

        while current_time < now:
            for zone in zones:
                seq_counters[zone.id] += 1

                # Mostly safe readings with occasional random warning/critical spikes
                spike = random.random() < 0.03

                if spike:
                    fire_sig = 1 if random.random() < 0.3 else 0
                    gas_val = random.uniform(300.0, 700.0) if zone.lab_type == "iot_lab" else 0.0
                    water_val = random.uniform(15.0, 45.0) if zone.lab_type != "iot_lab" else 0.0
                    occ_val = 1 if random.random() < 0.8 else 0
                else:
                    fire_sig = 0
                    gas_val = random.uniform(20.0, 120.0) if zone.lab_type == "iot_lab" else 0.0
                    water_val = random.uniform(0.0, 5.0) if zone.lab_type != "iot_lab" else 0.0
                    occ_val = 1 if random.random() < 0.4 else 0

                # Simple risk calculation for seed data
                gas_norm = min(1.0, gas_val / 1000.0)
                water_norm = min(1.0, water_val / 50.0)
                occ_factor = 1.0 if occ_val == 1 else 0.3
                risk = (40 * fire_sig) + (25 * gas_norm) + (20 * water_norm) + (15 * occ_factor)

                reading = SensorReading(
                    zone_id=zone.id,
                    sequence_id=seq_counters[zone.id],
                    fire_signal=fire_sig,
                    gas_level_raw=gas_val,
                    water_level_raw=water_val,
                    occupancy_raw=occ_val,
                    computed_risk_score=round(risk, 2),
                    received_at=current_time,
                )
                readings_batch.append(reading)
                total_readings += 1

                if len(readings_batch) >= 1000:
                    db.add_all(readings_batch)
                    await db.flush()
                    readings_batch = []

            current_time += timedelta(seconds=step_seconds)

        if readings_batch:
            db.add_all(readings_batch)
            await db.flush()

        print(f"Successfully inserted {total_readings} sensor readings.")

        print("Seeding sample historical incidents and acknowledgements...")
        incident_1 = Incident(
            zone_id=zone_iot.id,
            risk_score=72.5,
            state="RESOLVED",
            cause="Elevated gas levels (480 ppm) during soldering experiment",
            opened_at=now - timedelta(days=5, hours=3),
            resolved_at=now - timedelta(days=5, hours=2, minutes=15),
        )
        incident_2 = Incident(
            zone_id=zone_server.id,
            risk_score=81.0,
            state="RESOLVED",
            cause="Water leakage detected under rack 4 (28 cm level)",
            opened_at=now - timedelta(days=2, hours=6),
            resolved_at=now - timedelta(days=2, hours=5, minutes=40),
        )
        db.add_all([incident_1, incident_2])
        await db.flush()

        ack_1 = Acknowledgement(
            incident_id=incident_1.id,
            user_id=staff_user.id,
            acknowledged_at=now - timedelta(days=5, hours=2, minutes=50),
        )
        ack_2 = Acknowledgement(
            incident_id=incident_2.id,
            user_id=admin_user.id,
            acknowledged_at=now - timedelta(days=2, hours=5, minutes=55),
        )
        db.add_all([ack_1, ack_2])

        audit_1 = AuditLog(
            actor_id=admin_user.id,
            action="SYSTEM_INIT",
            target_type="SYSTEM",
            target_id="SCS-RG",
            details={"message": "System initialized and historical data seeded."},
        )
        db.add(audit_1)

        await db.commit()
        print("Database Seeding Completed Successfully!")


if __name__ == "__main__":
    asyncio.run(seed())

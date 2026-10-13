import asyncio
from sqlalchemy.future import select
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.role import Role
from app.models.user import User
from app.models.zone import Zone
from app.auth.password import get_password_hash
import app.models  # Register all models


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Seed Roles
        admin_role_res = await db.execute(select(Role).filter_by(id=1))
        admin_role = admin_role_res.scalars().first()
        if not admin_role:
            admin_role = Role(id=1, name="admin")
            db.add(admin_role)

        staff_role_res = await db.execute(select(Role).filter_by(id=2))
        staff_role = staff_role_res.scalars().first()
        if not staff_role:
            staff_role = Role(id=2, name="staff")
            db.add(staff_role)

        await db.commit()

        # 2. Seed Users
        admin_user_res = await db.execute(select(User).filter_by(username="admin"))
        if not admin_user_res.scalars().first():
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role_id=1
            )
            db.add(admin_user)

        staff_user_res = await db.execute(select(User).filter_by(username="staff"))
        if not staff_user_res.scalars().first():
            staff_user = User(
                username="staff",
                password_hash=get_password_hash("staff123"),
                role_id=2
            )
            db.add(staff_user)

        await db.commit()

        # 3. Seed Default Campus Zones
        zones_data = [
            {
                "id": "iot-lab-001",
                "name": "IoT & Sensor Fusion Lab",
                "lab_type": "iot_lab",
                "api_key": "zone-key-iot-lab-001"
            },
            {
                "id": "server-room-001",
                "name": "Central Data Center & Server Room",
                "lab_type": "server_room",
                "api_key": "zone-key-server-room-001"
            },
            {
                "id": "ds-lab-001",
                "name": "Data Science & AI Lab",
                "lab_type": "ds_lab",
                "api_key": "zone-key-ds-lab-001"
            }
        ]

        for zd in zones_data:
            z_res = await db.execute(select(Zone).filter_by(id=zd["id"]))
            if not z_res.scalars().first():
                z = Zone(
                    id=zd["id"],
                    name=zd["name"],
                    lab_type=zd["lab_type"],
                    api_key=zd["api_key"],
                    is_active=True
                )
                db.add(z)

        await db.commit()
        print("[SEED] Successfully seeded default roles, users, and campus zones.")


if __name__ == "__main__":
    asyncio.run(seed())

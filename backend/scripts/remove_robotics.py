import asyncio
from app.database.session import AsyncSessionLocal
from app.models.zone import Zone
from sqlalchemy.future import select

async def remove_robotics():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Zone).filter_by(id="robotics-lab-001"))
        z = res.scalars().first()
        if z:
            await db.delete(z)
            await db.commit()
            print("[CLEANUP] Successfully removed robotics-lab-001 from database.")
        else:
            print("[CLEANUP] robotics-lab-001 not found in database.")

if __name__ == "__main__":
    asyncio.run(remove_robotics())

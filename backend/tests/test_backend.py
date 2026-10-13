import sys
import os
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base
from scripts.seed_data import seed


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    await seed()
    yield


@pytest.mark.asyncio
async def test_health_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ONLINE"


@pytest.mark.asyncio
async def test_auth_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test valid admin login
        res = await ac.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"

        # Test invalid password
        res_bad = await ac.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
        assert res_bad.status_code == 401


@pytest.mark.asyncio
async def test_telemetry_ingest_and_risk_fusion():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Ingest high fire + gas telemetry for IoT Lab
        headers = {"X-Zone-API-Key": "zone-key-iot-lab-001"}
        payload = {
            "sequence_id": 9999,
            "timestamp": 1753489384,
            "sensors": {
                "fire_signal": 1,
                "gas_level_raw": 600.0,
                "water_level_raw": 0.0,
                "occupancy_raw": 1
            }
        }
        # Send 5 frames to trigger fire debouncer
        for seq in range(9990, 9995):
            payload["sequence_id"] = seq
            res = await ac.post("/api/v1/ingest", json=payload, headers=headers)
            assert res.status_code == 200

        data = res.json()
        assert data["state"] == "CRITICAL"
        assert data["risk_score"] >= 65.0
        assert data["actuation"]["buzzer"] is True
        assert data["actuation"]["led"] == "RED"


@pytest.mark.asyncio
async def test_rbac_admin_override_rejection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login as staff
        login_res = await ac.post("/api/v1/auth/login", json={"username": "staff", "password": "staff123"})
        staff_token = login_res.json()["access_token"]

        # Staff attempts admin manual override -> Must return 403 Forbidden
        headers = {"Authorization": f"Bearer {staff_token}"}
        override_res = await ac.post(
            "/api/v1/admin/override",
            json={"zone_id": "dummy", "forced_state": "SAFE", "reason": "Attempt by staff"},
            headers=headers
        )
        assert override_res.status_code == 403

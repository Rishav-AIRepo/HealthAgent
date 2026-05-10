"""Integration test — full HTTP stack: upload PDF → query insights."""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_non_pdf_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/upload/test-user-001",
            files={"file": ("report.txt", b"not a pdf", "text/plain")},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_chat_no_records_returns_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/chat/", json={
            "user_id": "nonexistent-user",
            "session_id": "session-001",
            "query": "What is my glucose level?",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "No health records found" in data["answer"]


@pytest.mark.asyncio
async def test_insights_no_records():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/insights/nonexistent-user-xyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] == "Low"
    assert data["risk_score"] == 0


@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/users/", json={
            "user_id": "test-user-profile",
            "age": 35,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 75,
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "test-user-profile"
    assert data["age"] == 35

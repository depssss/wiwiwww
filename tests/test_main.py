import pytest
import pytest_asyncio
import os
import asyncio
from httpx import AsyncClient
from src.main import app
from src.database import init_db

# Setup Database Test (Reset DB sebelum tes)
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    if os.path.exists("events.db"):
        os.remove("events.db")
    await init_db()

# TEST 1: Kirim 1 Event Valid
@pytest.mark.asyncio
async def test_publish_single_event():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        event = {
            "topic": "test.unit", "event_id": "id-1", 
            "timestamp": "2024-01-01", "source": "test", "payload": {}
        }
        resp = await ac.post("/publish", json=event)
        assert resp.status_code == 202
        
        # Tunggu consumer
        await asyncio.sleep(0.2)
        
        stats = (await ac.get("/stats")).json()
        assert stats["received"] == 1
        assert stats["unique_processed"] == 1

# TEST 2: Cek Deduplikasi (Idempotency)
@pytest.mark.asyncio
async def test_deduplication():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        event = {
            "topic": "test.dedup", "event_id": "same-id", 
            "timestamp": "2024-01-01", "source": "test", "payload": {}
        }
        # Kirim 3x event SAMA
        for _ in range(3):
            await ac.post("/publish", json=event)
        
        await asyncio.sleep(0.5)
        
        stats = (await ac.get("/stats")).json()
        assert stats["received"] == 3        # Diterima 3x
        assert stats["unique_processed"] == 1 # Disimpan cuma 1
        assert stats["duplicate_dropped"] == 2 # Dibuang 2

# TEST 3: Validasi Schema (Harus Error)
@pytest.mark.asyncio
async def test_invalid_schema():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Event tanpa event_id
        await ac.post("/publish", json={"topic": "fail"}) 
        # Harusnya 422 Unprocessable Entity
        # Note: httpx client mungkin raise error atau return 422 tergantung config,
        # kita cek response code dari call terakhir jika possible, 
        # tapi di sini ekspektasi simple call.
        resp = await ac.post("/publish", json={"topic": "fail"})
        assert resp.status_code == 422

# TEST 4: Batch Publish
@pytest.mark.asyncio
async def test_batch_publish():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        batch = [
            {"topic": "batch", "event_id": "b1", "timestamp": "", "source": "", "payload": {}},
            {"topic": "batch", "event_id": "b2", "timestamp": "", "source": "", "payload": {}}
        ]
        await ac.post("/publish", json=batch)
        await asyncio.sleep(0.2)
        stats = (await ac.get("/stats")).json()
        assert stats["unique_processed"] == 2

# TEST 5: Filter GET /events
@pytest.mark.asyncio
async def test_get_events_filter():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        e1 = {"topic": "A", "event_id": "1", "timestamp": "", "source": "", "payload": {}}
        e2 = {"topic": "B", "event_id": "2", "timestamp": "", "source": "", "payload": {}}
        await ac.post("/publish", json=[e1, e2])
        await asyncio.sleep(0.2)
        
        resp = await ac.get("/events?topic=A")
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["event_id"] == "1"
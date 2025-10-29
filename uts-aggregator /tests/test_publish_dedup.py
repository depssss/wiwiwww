import pytest
import time
from fastapi.testclient import TestClient
from src.app import create_app

@pytest.fixture
def client(tmp_path):
    # use temp dedup db for tests
    app = create_app()
    app.state.dedup = app.state.dedup.__class__(db_path=str(tmp_path/"dedup.db"))
    client = TestClient(app)
    return client

def test_publish_and_dedup(client):
    e = {
        "topic": "t1",
        "event_id": "eid-1",
        "timestamp": "2024-01-01T00:00:00Z",
        "source": "test",
        "payload": {}
    }
    r1 = client.post("/publish", json=e)
    assert r1.status_code == 200
    assert r1.json()["received"] == 1

    # publish duplicate
    r2 = client.post("/publish", json=e)
    assert r2.status_code == 200
    assert r2.json()["received"] == 1

    # wait processing
    time.sleep(0.1)
    stats = client.get("/stats").json()
    assert stats["received"] >= 2
    assert stats["duplicate_dropped"] >= 1

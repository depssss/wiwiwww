import time
from fastapi.testclient import TestClient
from src.app import create_app

def test_stats_events_consistency():
    app = create_app()
    client = TestClient(app)
    client.post("/publish", json={"topic":"t3","event_id":"e1","timestamp":"2024-01-01T00:00:00Z","source":"s","payload":{}})
    client.post("/publish", json={"topic":"t3","event_id":"e2","timestamp":"2024-01-01T00:00:01Z","source":"s","payload":{}})
    time.sleep(0.1)
    stats = client.get("/stats").json()
    events = client.get("/events?topic=t3").json()["events"]
    assert stats["unique_processed"] == len(events)

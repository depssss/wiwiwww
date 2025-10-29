import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.app import create_app

def test_small_stress():
    app = create_app()
    client = TestClient(app)
    n = 200
    events = []
    for i in range(n):
        events.append({"topic":"perf","event_id":f"id-{i}","timestamp":"2024-01-01T00:00:00Z","source":"s","payload":{}})
    start = time.time()
    r = client.post("/publish", json=events)
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 2.0  # publishing should be quick (enqueue only)

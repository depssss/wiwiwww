import pytest
from fastapi.testclient import TestClient
from src.app import create_app
import os
import time

def test_persist(tmp_path):
    db_file = tmp_path/"dedup.db"
    app = create_app()
    app.state.dedup = app.state.dedup.__class__(db_path=str(db_file))
    client = TestClient(app)

    e = {"topic":"t2","event_id":"eid-x","timestamp":"2024-01-01T00:00:00Z","source":"t","payload":{}}
    client.post("/publish", json=e)
    time.sleep(0.1)
    # simulate restart by creating new DedupStore instance pointing to same file
    new_store = app.state.dedup.__class__(db_path=str(db_file))
    assert new_store.is_seen("t2","eid-x") is True

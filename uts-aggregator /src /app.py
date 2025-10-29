from fastapi import FastAPI
from routers import router
from consumer import start_consumer_background
from dedup_store import DedupStore
import os
import time

_start_time = time.time()

def create_app():
    app = FastAPI(title="UTS Aggregator")

    # init persistent dedup store (SQLite file local)
    db_path = os.environ.get("DEDUP_DB", "dedup.db")
    dedup = DedupStore(db_path=db_path)
    app.state.dedup = dedup

    # stats counters
    app.state.stats = {
        "received": 0,
        "unique_processed": 0,
        "duplicate_dropped": 0,
        "topics": set(),
        "start_time": _start_time
    }

    # queue and background consumer
    queue = start_consumer_background(app, dedup)
    app.state.queue = queue

    app.include_router(router)

    return app

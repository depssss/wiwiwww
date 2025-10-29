from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from models import Event
from typing import List, Dict, Any
import time
import asyncio

router = APIRouter()

@router.post("/publish")
async def publish(request: Request):
    """
    Accept single event JSON or list of events.
    Validate schema via pydantic.
    Enqueue events to internal queue.
    """
    app = request.app
    body = await request.json()

    events = []
    if isinstance(body, list):
        events = body
    elif isinstance(body, dict):
        events = [body]
    else:
        raise HTTPException(status_code=400, detail="Invalid body")

    validated = []
    for item in events:
        try:
            ev = Event(**item)
            validated.append(ev.dict())
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Schema error: {e}")

    # enqueue
    q: asyncio.Queue = app.state.queue
    count = 0
    for ev in validated:
        await q.put(ev)
        count += 1
        app.state.stats["received"] += 1

    return JSONResponse({"received": count})

@router.get("/events")
async def get_events(request: Request, topic: str = None):
    """
    Return list of unique processed events (topic filter optional).
    For simplicity, we read dedup table rows as 'processed events'.
    """
    dedup = request.app.state.dedup
    conn = dedup._get_conn()
    cur = conn.cursor()
    if topic:
        cur.execute("SELECT topic,event_id,timestamp FROM dedup WHERE topic = ? ORDER BY timestamp ASC", (topic,))
    else:
        cur.execute("SELECT topic,event_id,timestamp FROM dedup ORDER BY timestamp ASC")
    rows = cur.fetchall()
    conn.close()
    events = [{"topic": r[0], "event_id": r[1], "timestamp": r[2]} for r in rows]
    return {"events": events}

@router.get("/stats")
async def get_stats(request: Request):
    s = request.app.state.stats
    uptime = time.time() - s["start_time"]
    return {
        "received": s["received"],
        "unique_processed": s["unique_processed"],
        "duplicate_dropped": s["duplicate_dropped"],
        "topics": list(s["topics"]),
        "uptime_seconds": uptime
    }

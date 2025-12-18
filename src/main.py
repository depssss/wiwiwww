import asyncio
import time
import logging
import sys
import random
import uuid
import httpx
from typing import List, Union
from datetime import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.models import Event, Stats
from src.database import (
    init_db, insert_event, get_events_by_topic, 
    increment_stat, get_stats_counter, get_unique_count, get_distinct_topics
)

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aggregator")

# In-memory Queue untuk buffer processing
event_queue = asyncio.Queue()
start_time = time.time()

async def event_consumer():
    """Worker background yang memproses antrian ke database."""
    logger.info("Consumer worker started...")
    while True:
        event = await event_queue.get()
        
        # Coba insert ke DB (Deduplikasi terjadi di sini)
        is_unique = await insert_event(event.model_dump())
        
        if is_unique:
            # Sukses insert (Data Baru)
            pass 
        else:
            # Gagal insert (Duplikat)
            await increment_stat('duplicate_dropped')
            logger.warning(f"Dropped DUPLICATE: {event.topic} - {event.event_id}")
        
        event_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init DB dan jalankan consumer
    await init_db()
    consumer_task = asyncio.create_task(event_consumer())
    yield
    # Shutdown
    consumer_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/publish", status_code=202)
async def publish_event(event_data: Union[Event, List[Event]]):
    """Menerima event (single/batch) dan memasukkan ke antrian."""
    events = event_data if isinstance(event_data, list) else [event_data]
    
    for event in events:
        await event_queue.put(event)
        await increment_stat('received')
    
    return {"message": f"{len(events)} event(s) queued."}

@app.get("/events")
async def get_events(topic: str):
    data = await get_events_by_topic(topic)
    return {"data": data}

@app.get("/stats", response_model=Stats)
async def get_stats():
    received = await get_stats_counter('received')
    dropped = await get_stats_counter('duplicate_dropped')
    unique = await get_unique_count()
    topics = await get_distinct_topics()
    
    return Stats(
        received=received,
        unique_processed=unique,
        duplicate_dropped=dropped,
        topics=topics,
        uptime_seconds=time.time() - start_time
    )

# --- PUBLISHER SIMULATOR (Loop Cepat untuk Demo) ---
async def run_publisher():
    # Tunggu sebentar agar Aggregator siap
    await asyncio.sleep(3)
    target_url = "http://aggregator:8080/publish"
    topics = ["user.login", "payment.success", "order.created"]
    
    logger.info("🚀 Publisher Simulator Started...")
    logger.info("🎯 Target: Sending 5500 events (Rubric Requirement >= 5000)...")

    async with httpx.AsyncClient() as client:
        # Loop 5500 kali (Memenuhi syarat > 5000)
        for i in range(5500):
            event_id = str(uuid.uuid4())
            topic = random.choice(topics)
            payload = {
                "topic": topic,
                "event_id": event_id,
                "timestamp": datetime.now().isoformat(),
                "source": "publisher-sim",
                "payload": {"seq": i, "val": random.randint(1, 100)}
            }
            
            try:
                # 1. Kirim Event Asli
                # Sesekali kirim via Batch (tiap kelipatan 100)
                if i % 100 == 0:
                    await client.post(target_url, json=[payload])
                else:
                    await client.post(target_url, json=payload)

                # Log progress
                if i % 500 == 0:
                    logger.info(f"📤 Progress: Sent {i} events...")

                # 2. Simulasi DUPLIKAT (At-Least-Once Delivery)
                # Syarat Rubrik: >= 20% duplikasi. Kita set 25%.
                if random.random() < 0.25:
                    try:
                        # Kirim payload yang SAMA persis
                        await client.post(target_url, json=payload)
                    except: pass
            
            except Exception as e:
                logger.error(f"Error sending: {e}")

            # Sleep sangat singkat (0.005s) agar selesai < 1 menit
            await asyncio.sleep(0.005)

    logger.info("✅ DONE: 5500+ events sent successfully.")
    # Keep container alive
    while True: await asyncio.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "publisher":
        asyncio.run(run_publisher())
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8080)
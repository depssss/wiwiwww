import asyncio
import logging
from fastapi import FastAPI
from models import Event
import time

logger = logging.getLogger("aggregator")
logging.basicConfig(level=logging.INFO)

def start_consumer_background(app: FastAPI, dedup):
    queue = asyncio.Queue()

    async def consumer_loop():
        # consumer coroutine: process items from queue
        while True:
            event_dict = await queue.get()
            try:
                await process_event(app, dedup, event_dict)
            except Exception as e:
                logger.exception("Error processing event: %s", e)
            finally:
                queue.task_done()

    loop = asyncio.get_event_loop()
    # schedule consumer tasks
    loop.create_task(consumer_loop())
    return queue

async def process_event(app: FastAPI, dedup, event_dict):
    """
    Process single event dict. Dedup by (topic,event_id).
    """
    # basic extract
    topic = event_dict.get("topic")
    event_id = event_dict.get("event_id")
    timestamp = event_dict.get("timestamp")

    # update received stat (thread-safe-ish)
    app.state.stats["topics"].add(topic)
    # dedup check and mark
    already = dedup.is_seen(topic, event_id)
    if already:
        app.state.stats["duplicate_dropped"] += 1
        logger.info("Duplicate dropped for (%s,%s)", topic, event_id)
        return

    inserted = dedup.mark_seen(topic, event_id, timestamp)
    if not inserted:
        app.state.stats["duplicate_dropped"] += 1
        logger.info("Duplicate dropped on insert for (%s,%s)", topic, event_id)
        return

    # simulate processing work
    await asyncio.sleep(0)  # if you have CPU IO-bound, you might offload instead
    app.state.stats["unique_processed"] += 1
    logger.info("Processed event (%s,%s)", topic, event_id)

import requests
import uuid
from datetime import datetime
import time

def publish_batch(url, topic, n, duplicate_rate=0.2):
    events = []
    for i in range(n):
        ev_id = str(uuid.uuid4())
        ev = {
            "topic": topic,
            "event_id": ev_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulator",
            "payload": {"i": i}
        }
        events.append(ev)
        # Add duplicates randomly: replicate ev_id for some previous event
        if duplicate_rate > 0 and i % int(1/duplicate_rate) == 0 and i > 0:
            dup = ev.copy()
            dup["event_id"] = events[max(0, i-1)]["event_id"]
            events.append(dup)
    resp = requests.post(url + "/publish", json=events)
    return resp.json()

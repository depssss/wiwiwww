import sqlite3
import threading
from typing import Optional

class DedupStore:
    def __init__(self, db_path: str = "dedup.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self):
        # check_same_thread False to allow usage across threads
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dedup (
                topic TEXT NOT NULL,
                event_id TEXT NOT NULL,
                timestamp TEXT,
                PRIMARY KEY(topic, event_id)
            )
        """)
        conn.commit()
        conn.close()

    def is_seen(self, topic: str, event_id: str) -> bool:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dedup WHERE topic = ? AND event_id = ? LIMIT 1", (topic, event_id))
        row = cur.fetchone()
        conn.close()
        return row is not None

    def mark_seen(self, topic: str, event_id: str, timestamp: Optional[str] = None) -> bool:
        """
        Try to insert a (topic,event_id). If already exists, return False.
        Return True when inserted (i.e. was unseen).
        """
        with self._lock:
            conn = self._get_conn()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO dedup(topic,event_id,timestamp) VALUES (?,?,?)", (topic, event_id, timestamp))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()

import aiosqlite
import logging

DB_NAME = "events.db"
logger = logging.getLogger("uvicorn")

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Tabel Events dengan CONSTRAINT UNIQUE untuk Idempotency
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                event_id TEXT NOT NULL,
                timestamp TEXT,
                source TEXT,
                payload TEXT,
                UNIQUE(topic, event_id)
            )
        """)
        
        # Tabel Stats untuk menyimpan counter agar tahan restart
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        """)
        # Inisialisasi nilai awal 0 jika belum ada
        await db.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('received', 0)")
        await db.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('duplicate_dropped', 0)")
        await db.commit()

async def get_stats_counter(key: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM stats WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def increment_stat(key: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE stats SET value = value + 1 WHERE key = ?", (key,))
        await db.commit()

async def insert_event(event_data: dict) -> bool:
    """
    Return True jika sukses (Unik).
    Return False jika gagal (Duplikat).
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO events (topic, event_id, timestamp, source, payload)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_data['topic'], 
                event_data['event_id'], 
                event_data['timestamp'], 
                event_data['source'], 
                str(event_data['payload'])
            ))
            await db.commit()
        return True
    except aiosqlite.IntegrityError:
        # Menangkap error jika (topic, event_id) sudah ada
        return False

async def get_events_by_topic(topic: str):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT topic, event_id, timestamp, source FROM events WHERE topic = ?", (topic,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_unique_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM events") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def get_distinct_topics() -> list:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT DISTINCT topic FROM events") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
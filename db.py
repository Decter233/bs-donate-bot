import aiosqlite
from contextlib import asynccontextmanager
from config import DB_PATH

@asynccontextmanager
async def get_db():
    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        await conn.commit()
    finally:
        await conn.close()

async def migrate():
    from pathlib import Path
    schema_path = Path(__file__).with_name("schema.sql")
    async with get_db() as db:
        await db.executescript(schema_path.read_text(encoding="utf-8"))

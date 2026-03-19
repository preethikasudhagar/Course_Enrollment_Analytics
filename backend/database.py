from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from urllib.parse import quote_plus
import os

# MySQL Connection String: mysql+aiomysql://user:password@host:port/dbname
password = quote_plus("Preethika_13#")
MYSQL_URL = os.getenv("DATABASE_URL", f"mysql+aiomysql://root:{password}@localhost:3306/course_analytics_db")

engine = create_async_engine(MYSQL_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight runtime migration for seat-management fields on existing databases.
        migration_sql = [
            "ALTER TABLE users ADD COLUMN department VARCHAR(100)",
            "ALTER TABLE users ADD COLUMN year INT",
            "ALTER TABLE courses ADD COLUMN remaining_seats INT DEFAULT 40",
            "ALTER TABLE courses ADD COLUMN waitlist_count INT DEFAULT 0",
            "ALTER TABLE courses ADD COLUMN auto_expand_enabled BOOLEAN DEFAULT TRUE",
            "ALTER TABLE courses ADD COLUMN max_seat_limit INT DEFAULT 200",
            "ALTER TABLE courses ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        ]
        for sql in migration_sql:
            try:
                await conn.execute(text(sql))
            except Exception:
                # Column may already exist; ignore and continue.
                pass

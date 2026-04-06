from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from urllib.parse import quote_plus
import os
import ssl

import logging

import time
import ssl

# Set up logging for Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL Connection String: mysql+aiomysql://user:password@host:port/dbname
password = quote_plus("Preethika_13#")
# Railway often uses MYSQL_URL instead of DATABASE_URL
db_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
if not db_url:
    logger.warning("Neither DATABASE_URL nor MYSQL_URL found in environment! Defaulting to localhost.")
    db_url = f"mysql+aiomysql://root:{password}@localhost:3306/course_analytics_db"

# Automatically fix dialect if the user provides standard mysql:// or pymysql
if db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+aiomysql://", 1)
elif db_url.startswith("mysql+pymysql://"):
    db_url = db_url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)

# Ensure SSL is handled for cloud hosts (Aiven etc)
# Railway internal connections (e.g. mysql-something.railway.internal) usually don't need SSL
connect_args = {}
if "aivencloud.com" in db_url:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context
    logger.info("SSL context configured for Aiven Cloud.")

MYSQL_URL = db_url
# Log connection host safely
host_info = "localhost"
if "@" in MYSQL_URL:
    try:
        host_info = MYSQL_URL.split("@")[-1].split("/")[0]
    except:
        host_info = "unknown"
logger.info(f"Database dialect resolved. Connecting to: {host_info}")

# Configure the database engine with robust settings for production Railway/Render
engine = create_async_engine(
    MYSQL_URL, 
    echo=False, 
    pool_size=10, 
    max_overflow=5, 
    pool_recycle=1800,
    pool_pre_ping=True,      # Check connection health before using
    pool_timeout=30,      # Give it plenty of time for cold starts
    connect_args={
        **connect_args,
        "connect_timeout": 10,       # Connection timeout for aiomysql
        "program_name": "FastAPI_CourseEnrollment"
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

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

async def close_db():
    await engine.dispose()

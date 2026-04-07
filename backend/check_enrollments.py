import asyncio
import os
import sys

# Ensure the parent directory is in sys.path to import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT count(*) FROM enrollments"))
        print(f"TOTAL_ENROLLMENTS={r.scalar()}")

if __name__ == "__main__":
    asyncio.run(check())

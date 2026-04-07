import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from database import init_db, AsyncSessionLocal

async def test_startup_logic():
    print("Testing startup logic...")
    try:
        await init_db()
        async with AsyncSessionLocal() as db:
            # Test the exact query used in main.py
            result = await db.execute(text("SELECT count(*) FROM courses"))
            count = result.scalar()
            print(f"Course count found: {count}")
            
            if count == 0:
                print("Seeding would be triggered.")
            else:
                print("Seeding not required.")
        print("Startup logic TEST PASSED.")
    except Exception as e:
        print(f"Startup logic TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_startup_logic())

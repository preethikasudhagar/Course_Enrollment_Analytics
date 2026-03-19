import asyncio
import sys
from sqlalchemy import text
from database import engine

async def migrate():
    try:
        async with engine.begin() as conn:
            print("Starting departmental migration...")
            sys.stdout.flush()
            
            # Add department column if not exists
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(100) DEFAULT 'ALL'"))
                print("Added 'department' column to 'users' table.")
            except Exception as e:
                print(f"Column 'department' might already exist or error: {e}")
            sys.stdout.flush()
                
            # Add year column if not exists
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN year INT DEFAULT 1"))
                print("Added 'year' column to 'users' table.")
            except Exception as e:
                print(f"Column 'year' might already exist or error: {e}")
            sys.stdout.flush()

            # Seed some data for departments
            await conn.execute(text("UPDATE users SET department = 'CSE' WHERE role = 'student' AND (id % 2 = 0)"))
            await conn.execute(text("UPDATE users SET department = 'IT' WHERE role = 'student' AND (id % 2 != 0)"))
            await conn.execute(text("UPDATE users SET department = 'ALL' WHERE role != 'student'"))
            
            await conn.execute(text("UPDATE courses SET department = 'CSE' WHERE id % 3 = 0"))
            await conn.execute(text("UPDATE courses SET department = 'IT' WHERE id % 3 = 1"))
            await conn.execute(text("UPDATE courses SET department = 'ALL' WHERE id % 3 = 2"))

            print("Migration and seeding completed successfully.")
            sys.stdout.flush()
    except Exception as general_e:
        print(f"General Migration Error: {general_e}")
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(migrate())

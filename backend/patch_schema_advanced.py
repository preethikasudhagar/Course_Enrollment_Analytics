import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from urllib.parse import quote_plus

# Database configuration
password = quote_plus("Preethika_13#")
MYSQL_URL = os.getenv("DATABASE_URL", f"mysql+aiomysql://root:{password}@localhost:3306/course_analytics_db")

engine = create_async_engine(MYSQL_URL, echo=True)

async def patch():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE courses ADD COLUMN course_code VARCHAR(50) DEFAULT NULL;"))
        except Exception as e: print("Already added course_code")

        try:
            await conn.execute(text("ALTER TABLE courses ADD COLUMN faculty_assigned VARCHAR(100) DEFAULT NULL;"))
        except Exception as e: print("Already added faculty_assigned")
        
        try:
            await conn.execute(text("ALTER TABLE courses ADD COLUMN enrolled_students INT DEFAULT 0;"))
        except Exception as e: print("Already added enrolled_students")
        
        try:
            await conn.execute(text("ALTER TABLE courses ADD COLUMN course_description TEXT DEFAULT NULL;"))
        except Exception as e: print("Already added course_description")

        try:
            await conn.execute(text("ALTER TABLE courses ADD COLUMN course_duration VARCHAR(50) DEFAULT NULL;"))
        except Exception as e: print("Already added course_duration")

        try:
            await conn.execute(text("ALTER TABLE courses ADD COLUMN credits INT DEFAULT 3;"))
        except Exception as e: print("Already added credits")

        try:
            await conn.execute(text("ALTER TABLE notifications CHANGE COLUMN role target_role VARCHAR(50) DEFAULT NULL;"))
        except Exception as e:
            try:
                await conn.execute(text("ALTER TABLE notifications ADD COLUMN target_role VARCHAR(50) DEFAULT NULL;"))
            except Exception as e2: print("Already have target_role")

        try:
            await conn.execute(text("ALTER TABLE notifications ADD COLUMN course_id INT DEFAULT NULL;"))
        except Exception as e: print("Already added course_id")

        # User Table Updates
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT NULL;"))
        except Exception as e: print("Already added phone")

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN profile_photo TEXT DEFAULT NULL;"))
        except Exception as e: print("Already added profile_photo")

if __name__ == "__main__":
    asyncio.run(patch())

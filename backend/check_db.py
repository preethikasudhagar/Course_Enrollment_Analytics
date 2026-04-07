import asyncio
import os
import sys

# Ensure the parent directory is in sys.path to import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from database import engine
from sqlalchemy import text

async def check():
    print("--- Database Verification ---")
    async with engine.connect() as conn:
        # Check Courses
        r = await conn.execute(text("SELECT count(*) FROM courses"))
        count = r.scalar()
        print(f"Courses Total: {count}")
        
        # Check Course details
        r = await conn.execute(text("SELECT course_name, enrolled_students, seat_limit FROM courses LIMIT 6"))
        print("\nCourse Sample (Core 6):")
        for row in r.all():
            print(f"- {row[0]}: {row[1]}/{row[2]}")
            
        # Check Enrollments
        r = await conn.execute(text("SELECT count(*) FROM enrollments"))
        enr_count = r.scalar()
        print(f"\nEnrollments Total: {enr_count}")
        
        # Check for Mismatches
        r = await conn.execute(text("SELECT course_name, enrolled_students FROM courses WHERE enrolled_students = 0"))
        mismatches = r.all()
        if mismatches:
            print("\nWARNING: Found courses with 0 enrolled_students field:")
            for m in mismatches:
                print(f"- {m[0]}")
        else:
            print("\nSUCCESS: All courses have non-zero enrolled_students field.")

if __name__ == "__main__":
    asyncio.run(check())

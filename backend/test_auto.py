import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import NullPool

from models.models import Course, Enrollment, Notification, User
from database import MYSQL_URL
from routes.enrollments import _enroll_with_seat_logic

engine = create_async_engine(MYSQL_URL, echo=False, poolclass=NullPool)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def run_test():
    async with AsyncSessionLocal() as db:
        users = await db.execute(select(User))
        user_list = users.scalars().all()
        student = next((u for u in user_list if u.role.value == "student"), None)
        
        # Manually create a new constrained course
        c = Course(
            course_code="TEST-999",
            course_name="Stress Test Automation",
            department="QA",
            seat_limit=1,
            enrolled_students=1,
            remaining_seats=0
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        
        print("--- BEFORE ENROLLMENT ---")
        print(f"Seat Limit: {c.seat_limit}, Enrolled: {c.enrolled_students}")
        old_id = c.id
        
        # Execute the HTTP endpoint logic directly
        print("\n--- TRIGGERING ENROLLMENT ---")
        res = await _enroll_with_seat_logic(course_id=c.id, db=db, current_user=student)
        print(res)
        
        # Verify outcomes
        await db.refresh(c)
        print("\n--- AFTER ENROLLMENT ---")
        print(f"Seat Limit: {c.seat_limit}, Enrolled: {c.enrolled_students}, Status: {'OPEN' if c.seat_limit > c.enrolled_students else 'FULL'}")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_test())

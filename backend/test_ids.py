import asyncio
from database import AsyncSessionLocal
from models.models import Course

async def test_insert():
    async with AsyncSessionLocal() as db:
        c1 = Course(course_code="TEST1", course_name="Test One", department="CSE", seat_limit=50)
        c2 = Course(course_code="TEST2", course_name="Test Two", department="CSE", seat_limit=50)
        db.add_all([c1, c2])
        await db.commit()
        await db.refresh(c1)
        await db.refresh(c2)
        print(f"Course 1 ID: {c1.id}")
        print(f"Course 2 ID: {c2.id}")

asyncio.run(test_insert())

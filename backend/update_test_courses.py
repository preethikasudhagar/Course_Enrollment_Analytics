import asyncio
from sqlalchemy.future import select
from sqlalchemy import or_
from database import AsyncSessionLocal, engine
from models.models import Course

async def up():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Course).where(
            or_(
                Course.course_name.ilike('%Data Structures%'),
                Course.course_name.ilike('%3D%Modelling%'),
                Course.course_name.ilike('%3D%modelling%')
            )
        ))
        courses = res.scalars().all()
        if not courses:
            print("No matching courses found!")
        for c in courses:
            c.enrolled_students = 44
            c.seat_limit = 45
            c.remaining_seats = 1
            print(f"Updated '{c.course_name}' -> Enrolled: {c.enrolled_students}, Seat Limit: {c.seat_limit}")
        
        await db.commit()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(up())

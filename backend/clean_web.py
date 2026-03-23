import asyncio
from database import AsyncSessionLocal
from models.models import Course, Enrollment
from sqlalchemy import select, delete

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Course).where(Course.course_name == 'Web Development'))
        course = res.scalars().first()
        if course:
            await db.execute(delete(Enrollment).where(Enrollment.course_id == course.id))
            await db.execute(delete(Course).where(Course.id == course.id))
            await db.commit()
            print('Deleted Web Development course.')
        else:
            print('Not found in DB.')

asyncio.run(main())

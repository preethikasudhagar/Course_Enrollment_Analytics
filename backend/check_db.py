import asyncio
from database import AsyncSessionLocal
from models.models import Course
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Course.course_name))
        courses = res.scalars().all()
        for c in courses:
            print(c)

asyncio.run(main())

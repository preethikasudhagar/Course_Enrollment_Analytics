import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models.models import Enrollment, User, Course

async def main():
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == "student@test.com"))).scalars().first()
        course = (await db.execute(select(Course).where(Course.course_name.ilike('%web%')))).scalars().first()
        e = (await db.execute(select(Enrollment).where(Enrollment.student_id == user.id, Enrollment.course_id == course.id))).scalars().first()
        print(f"Is test student enrolled in Web Dev? {'YES' if e else 'NO'}")

if __name__ == '__main__':
    asyncio.run(main())

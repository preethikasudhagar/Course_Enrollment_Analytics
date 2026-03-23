import asyncio
from sqlalchemy import func
from sqlalchemy.future import select
from database import AsyncSessionLocal
from models.models import User, Course, Enrollment

async def verify():
    from database import close_db
    try:
        async with AsyncSessionLocal() as db:
            u_count = (await db.execute(select(func.count()).select_from(User))).scalar()
            c_count = (await db.execute(select(func.count()).select_from(Course))).scalar()
            e_count = (await db.execute(select(func.count()).select_from(Enrollment))).scalar()
            
            print(f"Users: {u_count}")
            print(f"Courses: {c_count}")
            print(f"Enrollments: {e_count}")
            
            # Check specific courses
            res = await db.execute(select(Course).where(Course.course_name.in_(["Software Engineering", "Cyber Security"])))
            for c in res.scalars().all():
                e_res = await db.execute(select(func.count()).select_from(Enrollment).where(Enrollment.course_id == c.id))
                print(f"Course {c.course_name}: {e_res.scalar()}/{c.seat_limit}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(verify())

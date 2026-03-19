import asyncio
from database import get_db
from models.models import Course

async def main():
    async for db in get_db():
        course6 = await db.get(Course, 6)
        if course6:
            old_name = course6.course_name
            course6.course_name = "3D Modelling"
            await db.commit()
            print(f"Renamed course_id=6 from '{old_name}' to '3D Modelling'")
        else:
            print("Course 6 not found")

if __name__ == "__main__":
    asyncio.run(main())


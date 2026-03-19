import asyncio
import os
os.chdir('course-enrollment-analytics/backend')
import sys
sys.path.append('.')

from database import get_db
from models.models import Course

async def update_data_structures():
    async for db in get_db():
        course6 = await db.get(Course, 6)
        if course6 and course6.course_name == "Data Structures":
            course6.course_name = "3D Modelling"
            await db.commit()
            print("Updated course_id=6 to '3D Modelling'")
        else:
            print(f"Course 6: {course6.course_name if course6 else 'Not found'}")

asyncio.run(update_data_structures())


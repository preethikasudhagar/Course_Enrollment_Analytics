import asyncio
from sqlalchemy import select, delete, text
from database import AsyncSessionLocal
from models.models import Course, User, Enrollment, UserRole
from datetime import datetime
import random

async def seed_custom_data():
    try:
        async with AsyncSessionLocal() as db:
            print("Fetching students...")
            students_query = await db.execute(select(User).where(User.role == UserRole.STUDENT))
            students = students_query.scalars().all()
            if len(students) < 60:
                print(f"Not enough students (found {len(students)}), creating more...")
                for i in range(len(students), 60):
                    new_student = User(
                        name=f"Test Student {i}",
                        email=f"test.student{i}@university.edu",
                        password="hash",
                        role=UserRole.STUDENT
                    )
                    db.add(new_student)
                await db.commit()
                # Re-fetch after commit
                students_query = await db.execute(select(User).where(User.role == UserRole.STUDENT))
                students = students_query.scalars().all()
                
            print(f"Total students available: {len(students)}")
            
            print("Fetching courses...")
            courses_query = await db.execute(select(Course))
            all_courses = courses_query.scalars().all()
            
            targets = {
                "Deep Learning": {"limit": 50, "enrolled": 49},
                "Data Analytics": {"limit": 60, "enrolled": 59},
                "Cloud Computing": {"limit": 50, "enrolled": 45}
            }
            
            for course_name, config in targets.items():
                course = next((c for c in all_courses if c.course_name == course_name), None)
                if not course:
                    print(f"Course {course_name} not found, creating it.")
                    course = Course(
                        course_name=course_name,
                        course_code=f"CS{random.randint(500,999)}",
                        department="Computer Science",
                        seat_limit=config["limit"],
                        enrolled_students=0
                    )
                    db.add(course)
                    await db.commit()
                    await db.refresh(course)
                
                print(f"Updating {course_name}...")
                course.seat_limit = config["limit"]
                course.enrolled_students = config["enrolled"]
                course.remaining_seats = config["limit"] - config["enrolled"]
                course.max_seat_limit = config["limit"] + 50
                
                # Clear existing enrollments
                await db.execute(delete(Enrollment).where(Enrollment.course_id == course.id))
                await db.commit()
                
                # Add new enrollments
                chosen_students = random.sample(students, config["enrolled"])
                for s in chosen_students:
                    enrollment = Enrollment(
                        student_id=s.id,
                        course_id=course.id,
                        enrollment_date=datetime.utcnow()
                    )
                    db.add(enrollment)
                    
                print(f"Updated {course_name} to {config['enrolled']}/{config['limit']} seats.")
                await db.commit()
            
            print("Custom seed complete.")
            
            from routes.analytics import refresh_all_vitals
            await refresh_all_vitals()
            print("Vitals refreshed successfully.")
            
    except Exception as e:
        print(f"Error during seeding: {e}")

if __name__ == "__main__":
    asyncio.run(seed_custom_data())

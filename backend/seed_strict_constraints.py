import asyncio
from sqlalchemy import select, delete
from database import AsyncSessionLocal
from models.models import Course, User, Enrollment, UserRole
from datetime import datetime
import random

async def enforce_constraints():
    async with AsyncSessionLocal() as db:
        print("Cleaning up current data...")
        
        # We need to ensure we have exactly software engineering, cyber security and a few others
        await db.execute(delete(Enrollment))
        
        courses_query = await db.execute(select(Course))
        all_courses = courses_query.scalars().all()
        
        # Target constraints: Max 70 courses.
        if len(all_courses) > 70:
            to_delete = all_courses[70:]
            for c in to_delete:
                await db.delete(c)
            all_courses = all_courses[:70]
        
        # Enforce exact course limits for Software Engineering and Cyber Security
        targets = {
            "Software Engineering": {"limit": 30, "enrolled": 29, "department": "Software Engineering"},
            "Cyber Security": {"limit": 30, "enrolled": 29, "department": "Information Technology"}
        }
        
        for name, config in targets.items():
            c = next((c for c in all_courses if c.course_name == name), None)
            if not c:
                c = Course(course_name=name, department=config["department"], course_code=f"CS{random.randint(400,999)}")
                db.add(c)
                all_courses.append(c)
            c.seat_limit = config["limit"]
            c.enrolled_students = config["enrolled"]
            c.remaining_seats = config["limit"] - config["enrolled"]
        
        # For the remaining courses, set their enrollments to 0 to keep total enrollments <= 60 (29+29 = 58)
        # We will add 2 more enrollments somewhere so the total is exactly 60.
        ai_course = next((c for c in all_courses if c.course_name not in list(targets.keys()) and c.department == "Artificial Intelligence"), None)
        if not ai_course:
            ai_course = Course(course_name="Machine Learning Intro", department="Artificial Intelligence", course_code="CS101", seat_limit=30)
            db.add(ai_course)
            all_courses.append(ai_course)
            
        ai_course.enrolled_students = 2
        ai_course.remaining_seats = (ai_course.seat_limit or 30) - 2
        
        for c in all_courses:
            if c.course_name not in ["Software Engineering", "Cyber Security", ai_course.course_name]:
                c.enrolled_students = 0
                c.remaining_seats = c.seat_limit
        
        await db.commit()
        
        # Now create actually 60 students and 60 enrollments
        users_result = await db.execute(select(User).where(User.role == UserRole.STUDENT))
        students = users_result.scalars().all()
        
        # Ensure we have at least 60 students
        while len(students) < 60:
            new_s = User(name=f"Demo Student {len(students)}", email=f"demo{len(students)}@example.com", password="hash", role=UserRole.STUDENT)
            db.add(new_s)
            students.append(new_s)
        await db.commit()
        
        # Refresh everything
        for c in all_courses:
            await db.refresh(c)
            
        se_course = next((c for c in all_courses if c.course_name == "Software Engineering"))
        cs_course = next((c for c in all_courses if c.course_name == "Cyber Security"))
        
        # Generate exactly 29 unique enrollments for Soft Eng
        se_students = random.sample(students, 29)
        for s in se_students:
            db.add(Enrollment(student_id=s.id, course_id=se_course.id))
            
        # Generate exactly 29 unique enrollments for Cyber Sec
        cs_students = random.sample([st for st in students if st not in se_students], 29)
        for s in cs_students:
            db.add(Enrollment(student_id=s.id, course_id=cs_course.id))
            
        # Generate 2 enrollments for AI course
        remaining_st = [st for st in students if st not in se_students and st not in cs_students]
        ai_students = random.sample(remaining_st, 2)
        for s in ai_students:
            db.add(Enrollment(student_id=s.id, course_id=ai_course.id))
            
        await db.commit()
        print("Setup complete! Total enrolled: 60")
        
        from routes.analytics import refresh_all_vitals
        await refresh_all_vitals()

if __name__ == "__main__":
    asyncio.run(enforce_constraints())

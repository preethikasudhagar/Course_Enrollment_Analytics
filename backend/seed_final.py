import asyncio
import random
from datetime import datetime
from sqlalchemy import text, select, delete
from database import AsyncSessionLocal, init_db
from models.models import User, Course, Enrollment, Notification, Analytics, UserRole, SeatExpansionLog
from utils.auth import get_password_hash

async def seed_fixed_data():
    print("Starting Final Seeding Process...")
    await init_db()
    async with AsyncSessionLocal() as db:
        # Disable foreign keys for truncate
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for table in ["enrollments", "notifications", "analytics", "courses", "users", "seat_expansion_logs"]:
            try:
                await db.execute(text(f"TRUNCATE TABLE {table};"))
            except:
                pass 
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        await db.commit()
        print("Database cleared.")

        # 1. Create Essential Users (Admin & Faculty)
        admin = User(name="System Admin", email="admin@example.com", password=get_password_hash("admin123"), role=UserRole.ADMIN)
        faculty = User(name="Lead Faculty", email="faculty@example.com", password=get_password_hash("faculty123"), role=UserRole.FACULTY)
        db.add_all([admin, faculty])
        await db.commit()
        print("Admin/Faculty users created.")

        # 2. Create exact student count (60 students)
        students = []
        for i in range(1, 61):
            s = User(name=f"Demo Student {i}", email=f"student{i}@example.com", password=get_password_hash("student123"), role=UserRole.STUDENT)
            db.add(s)
            students.append(s)
        await db.commit()
        for s in students: await db.refresh(s)
        print(f"60 students created.")

        # 3. Seed Courses (70 exactly)
        course_configs = [
            ("SE101", "Software Engineering", "Software Engineering", 30),
            ("CS101", "Cyber Security", "Information Technology", 30),
            ("AI101", "Deep Learning", "Artificial Intelligence", 50),
        ]
        
        courses = []
        # Create mandatory courses first
        for code, name, dept, limit in course_configs:
            c = Course(course_code=code, course_name=name, department=dept, seat_limit=limit, auto_expand_enabled=True)
            db.add(c)
            courses.append(c)
        
        # Add 67 more courses to hit exactly 70
        depts = ["Computer Science", "Information Technology", "Artificial Intelligence", "Data Science", "Software Engineering"]
        for i in range(4, 71):
            name = f"General Course {i}"
            dept = random.choice(depts)
            c = Course(course_code=f"GEN{i}", course_name=name, department=dept, seat_limit=40, auto_expand_enabled=True)
            db.add(c)
            courses.append(c)
            
        await db.commit()
        for c in courses: await db.refresh(c)
        print(f"70 courses created.")

        # 4. Mandatory Enrollments (exactly 60 total)
        # SE: 29
        # CS: 29
        # AI: 2
        se_course = courses[0]
        cs_course = courses[1]
        dl_course = courses[2]

        all_students = list(students)
        random.shuffle(all_students)

        se_students = all_students[:29]
        cs_students = all_students[29:58]
        dl_students = all_students[58:60]

        for s in se_students:
            db.add(Enrollment(student_id=s.id, course_id=se_course.id, enrollment_date=datetime.now()))
        for s in cs_students:
            db.add(Enrollment(student_id=s.id, course_id=cs_course.id, enrollment_date=datetime.now()))
        for s in dl_students:
            db.add(Enrollment(student_id=s.id, course_id=dl_course.id, enrollment_date=datetime.now()))

        # Update cached counts for mandatory courses
        se_course.enrolled_students = 29
        se_course.remaining_seats = 1
        cs_course.enrolled_students = 29
        cs_course.remaining_seats = 1
        dl_course.enrolled_students = 2
        dl_course.remaining_seats = 48

        await db.commit()
        print("Mandatory enrollments seeded (Total: 60). Software Engineering & Cyber Security @ 29.")

        # 5. Trigger sequential Cache Refresh
        from routes.analytics import refresh_admin_vitals, refresh_faculty_vitals_cache, refresh_student_vitals
        await refresh_admin_vitals(db)
        await refresh_faculty_vitals_cache(db)
        await refresh_student_vitals(db)
        print("Analytics cache refreshed.")

    print("--- SEEDING COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(seed_fixed_data())

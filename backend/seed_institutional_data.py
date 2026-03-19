import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import text
from database import AsyncSessionLocal, init_db
from models.models import User, Course, Enrollment, Notification, Analytics, UserRole
from utils.auth import get_password_hash

async def seed_data():
    print("Initializing Institutional Data Synthesis...")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Clear existing data
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for table in ["enrollments", "notifications", "analytics", "courses", "users"]:
            await db.execute(text(f"TRUNCATE TABLE {table};"))
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        await db.commit()

        # 1. Seed Core Personnel
        admin = User(
            name="Institutional Admin",
            email="admin@example.com",
            password=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        faculty = User(
            name="Lead Faculty",
            email="faculty@example.com",
            password=get_password_hash("faculty123"),
            role=UserRole.FACULTY
        )
        db.add_all([admin, faculty])
        await db.commit()

        # 2. Seed Students (50)
        departments = ["Computer Science", "Information Technology", "Artificial Intelligence", "Data Science", "Electronics"]
        first_names = ["Rahul", "Priya", "Arjun", "Sneha", "Kavya", "Nikhil", "Ananya", "Rohit", "Divya", "Aditya", "Vikram", "Ishita", "Siddharth", "Meera", "Yash", "Tanvi", "Rohan", "Sonal", "Varun", "Riya"]
        last_names = ["Sharma", "Patel", "Mehta", "Reddy", "Iyer", "Verma", "Gupta", "Nair", "Menon", "Singh", "Joshi", "Kapoor", "Malhotra", "Chopra", "Das", "Bose", "Kulkarni", "Deshmukh", "Pande", "Rao"]
        
        students = []
        for i in range(50):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            email = f"{fname.lower()}.{lname.lower()}{i}@university.edu"
            dept = random.choice(departments)
            student = User(
                name=f"{fname} {lname}",
                email=email,
                password=get_password_hash("student123"),
                role=UserRole.STUDENT
            )
            db.add(student)
            students.append(student)
        
        await db.commit()
        for s in students: await db.refresh(s)

        # 3. Seed Courses (12)
        course_configs = [
            ("CS201", "Data Structures", "Computer Science", 45),
            ("CS220", "Web Development", "Information Technology", 50),
            ("CS210", "Database Systems", "Software Engineering", 40),
            ("CS305", "Machine Learning", "Artificial Intelligence", 35),
            ("CS330", "Cloud Computing", "Computer Science", 30),
            ("CS301", "Operating Systems", "Computer Science", 40),
            ("CS401", "Artificial Intelligence", "Artificial Intelligence", 30),
            ("CS320", "Computer Networks", "Information Technology", 35),
            ("CS350", "Cyber Security", "Information Technology", 25),
            ("CS360", "Data Analytics", "Data Science", 40),
            ("CS370", "Software Engineering", "Software Engineering", 45),
            ("CS450", "Deep Learning", "Artificial Intelligence", 20)
        ]
        
        courses = []
        for code, name, dept, limit in course_configs:
            course = Course(course_code=code, course_name=name, department=dept, seat_limit=limit)
            db.add(course)
            courses.append(course)
        
        await db.commit()
        for c in courses: await db.refresh(c)

        # 4. Seed Enrollments (100)
        high_demand = ["Machine Learning", "Data Analytics", "Web Development"]
        medium_demand = ["Data Structures", "Database Systems", "Cloud Computing"]
        
        enrollments_count = 0
        used_pairs = set()
        
        while enrollments_count < 100:
            s = random.choice(students)
            c = random.choice(courses)
            if (s.id, c.id) in used_pairs: continue
            
            if c.course_name in high_demand: prob = 0.9
            elif c.course_name in medium_demand: prob = 0.6
            else: prob = 0.3
            
            if random.random() < prob:
                month = random.randint(1, 4)
                day = random.randint(1, 28)
                enroll_date = datetime(2024, month, day)
                enrollment = Enrollment(student_id=s.id, course_id=c.id, enrollment_date=enroll_date)
                db.add(enrollment)
                used_pairs.add((s.id, c.id))
                enrollments_count += 1
        
        await db.commit()

        # 5. Seed Analytics & Notifications
        notif_samples = [
            ("Machine Learning seats almost full. Protocol optimization suggested.", "admin"),
            ("New course 'Deep Learning' added to catalog.", "student"),
            ("Cloud Computing enrollment increased by 20% this session.", "faculty"),
            ("Successful registration protocol completed.", "student"),
            ("Identity registry updated for Lead Faculty.", "admin")
        ]
        
        for msg, role in notif_samples:
            n = Notification(message=msg, role=role, status="unread")
            db.add(n)
        
        for c in courses:
            count = len([e for e in used_pairs if e[1] == c.id])
            score = (count / c.seat_limit) * 10
            a = Analytics(course_id=c.id, demand_score=score, trend_data=f"Growth index: {random.uniform(1.1, 1.5):.2f}")
            db.add(a)

        await db.commit()
        print(f"Synthesis Complete: 50 Students, 12 Courses, {enrollments_count} Enrollments generated.")

if __name__ == "__main__":
    asyncio.run(seed_data())

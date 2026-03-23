import asyncio
import random
from sqlalchemy import select, delete
from database import AsyncSessionLocal, engine
from models.models import Course, User, Enrollment, UserRole, Waitlist, SeatExpansionLog, Notification, SystemActivity
from datetime import datetime

async def seed_strict_17():
    async with AsyncSessionLocal() as db:
        print("Cleaning up existing data...")
        await db.execute(delete(Enrollment))
        await db.execute(delete(Waitlist))
        await db.execute(delete(SeatExpansionLog))
        await db.execute(delete(Notification))
        await db.execute(delete(SystemActivity))
        await db.execute(delete(Course))
        
        # Step 1: Clean users and create test student
        from utils.auth import get_password_hash
        print("Cleaning up ALL students and specific admin...")
        # Delete all students to ensure strict 30-student limit
        await db.execute(delete(User).where(User.role == UserRole.STUDENT))
        await db.execute(delete(User).where(User.email == "admin@university.edu"))
        
        admin_user = User(
            name="Project Admin",
            email="admin@university.edu",
            password=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        
        # Test student
        test_student = User(
            name="Test Student",
            email="student@test.com",
            password=get_password_hash("password123"),
            role=UserRole.STUDENT,
            department="Computer Science"
        )
        db.add(test_student)

        # Preethika Sudhagar
        preethika = User(
            name="Preethika Sudhagar",
            email="preethika@university.edu",
            password=get_password_hash("student123"),
            role=UserRole.STUDENT,
            department="Software Engineering"
        )
        db.add(preethika)
        
        # Add 28 more students to reach exactly 30
        print("Adding 28 more background students for a total of 30...")
        for i in range(28):
            new_user = User(
                name=f"Student {i+1}",
                email=f"student{i+1}@university.edu",
                password=get_password_hash("student123"),
                role=UserRole.STUDENT,
                department=random.choice(["Computer Science", "Information Technology", "Data Science", "Software Engineering"])
            )
            db.add(new_user)
            
        await db.commit()
        
        # Refresh student list
        users_result = await db.execute(select(User).where(User.role == UserRole.STUDENT))
        students = users_result.scalars().all()
        print(f"Total students in DB: {len(students)}")

        print("Seeding 17 strict courses...")
        
        mandatory_8 = [
            {"name": "Software Engineering", "dept": "Software Engineering", "code": "SE-401"},
            {"name": "Artificial Intelligence", "dept": "Computer Science", "code": "AI-601"},
            {"name": "Data Science", "dept": "Data Science", "code": "DS-201"},
            {"name": "Cloud Computing", "dept": "Computer Science", "code": "CC-501"},
            {"name": "Database Management", "dept": "Computer Science", "code": "DB-202"},
            {"name": "Mobile App Development", "dept": "Software Engineering", "code": "MA-303"},
            {"name": "Data Analytics", "dept": "Data Science", "code": "DA-302"},
            {"name": "Machine Learning", "dept": "Data Science", "code": "ML-505"},
        ]
        
        other_8 = [
            {"name": "Cyber Security", "dept": "Information Technology", "code": "CS-404"},
            {"name": "Networking", "dept": "Computer Science", "code": "NW-202"},
            {"name": "DevOps Practices", "dept": "Software Engineering", "code": "DO-402"},
            {"name": "Quantum Computing", "dept": "Computer Science", "code": "QC-801"},
            {"name": "UI/UX Design", "dept": "Software Engineering", "code": "UI-201"},
            {"name": "Discrete Mathematics", "dept": "Computer Science", "code": "DM-101"},
            {"name": "Operating Systems", "dept": "Computer Science", "code": "OS-301"},
            {"name": "Blockchain Technology", "dept": "Information Technology", "code": "BT-701"},
        ]
        
        all_course_configs = mandatory_8 + other_8
        created_courses = []
        
        for i, config in enumerate(all_course_configs):
            is_mandatory = i < 8
            # Use fixed limits but always respect student count for starting enrollment
            limit = 30 if is_mandatory else random.choice([40, 50, 60])
            
            # Enrolled count cannot exceed total students
            max_enrolled = len(students)
            if is_mandatory:
                enrolled = min(29, max_enrolled)
            else:
                enrolled = random.randint(5, min(limit - 5, max_enrolled))
            
            course = Course(
                course_name=config["name"],
                department=config["dept"],
                course_code=config["code"],
                seat_limit=limit,
                enrolled_students=enrolled,
                auto_expand_enabled=True,
                max_seat_limit=120,
                faculty_assigned=f"Prof. {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'])}"
            )
            db.add(course)
            created_courses.append((course, enrolled))
            
        await db.commit()
        
        print("Generating exact enrollments...")
        used_students = set()
        for i, (course, enrolled_count) in enumerate(created_courses):
            # Refresh to get ID
            await db.refresh(course)
            
            # Select unique students for this course
            if i < 8: # All mandatory courses (29/30)
                # Exclude test_student so we can test enrollment on ANY of them
                eligible_for_sample = [s for s in students if s.email != "student@test.com"]
                sampled_students = random.sample(eligible_for_sample, enrolled_count)
            else:
                sampled_students = random.sample(students, enrolled_count)
            
            for student in sampled_students:
                db.add(Enrollment(student_id=student.id, course_id=course.id))
        
        await db.commit()
        print(f"Seeding complete! Exactly {len(all_course_configs)} courses created.")
        
async def main():
    try:
        await seed_strict_17()
    finally:
        from database import close_db
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())

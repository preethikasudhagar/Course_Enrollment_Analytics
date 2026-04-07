import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import User, Course, Enrollment, Notification, Analytics, SystemSetting, UserRole
from utils.auth import get_password_hash
from database import AsyncSessionLocal

async def seed_all_data(db: AsyncSession):
    import traceback
    print("Starting comprehensive data seeding...")
    
    try:
        # 1. Clear existing data
        print("Step 1: Clearing existing tables...")
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for table in ["enrollments", "notifications", "analytics", "courses", "users", "system_settings", "system_activities", "waitlist", "faculty_performance", "suggestions", "seat_expansion_logs"]:
            await db.execute(text(f"DELETE FROM {table};"))
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        await db.commit()
        print("Database wiped clean.")

        # 2. Create Admin and Faculty
        print("Step 2: Creating Admin and Faculty accounts...")
        # Check if admin already exists (handling potential concurrency)
        res_admin = await db.execute(select(User).where(User.email == "admin@example.com"))
        if not res_admin.scalars().first():
            admin = User(
                name="System Admin",
                email="admin@example.com",
                password=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin)
        
        res_faculty = await db.execute(select(User).where(User.email == "faculty@example.com"))
        if not res_faculty.scalars().first():
            faculty = User(
                name="Main Faculty",
                email="faculty@example.com",
                password=get_password_hash("faculty123"),
                role=UserRole.FACULTY,
                department="Computer Science"
            )
            db.add(faculty)
            
        await db.commit()
        print("Admin and Faculty accounts handled.")

        # 3. Create 30 Students
        print("Step 3: Hashing student password...")
        student_password = get_password_hash("preethika")
        print("Step 3: Processing 30 student accounts...")
        
        student_data = [
            ("Preethika Sudhagar", "Information Science"), ("Arjun Kumar", "Computer Science"),
            ("Meena R", "Data Science"), ("Karthik S", "IT"), ("Priya N", "Software Engineering"),
            ("Rahul V", "Computer Science"), ("Divya M", "Data Science"), ("Naveen K", "IT"),
            ("Sanjay R", "Computer Science"), ("Anitha P", "Software Engineering"),
            ("Vignesh T", "IT"), ("Harini S", "Data Science"), ("Deepak K", "Computer Science"),
            ("Lavanya R", "IT"), ("Mohan S", "Software Engineering"), ("Keerthana V", "Data Science"),
            ("Ajay P", "Computer Science"), ("Reshma K", "IT"), ("Surya N", "Software Engineering"),
            ("Nithya R", "Data Science"), ("Praveen K", "Computer Science"), ("Aishwarya M", "IT"),
            ("Manoj S", "Software Engineering"), ("Gokul R", "Computer Science"),
            ("Pavithra N", "Data Science"), ("Rakesh V", "IT"), ("Kiran S", "Computer Science"),
            ("Swathi P", "Software Engineering"), ("Dinesh K", "Data Science"), ("Varsha R", "IT")
        ]
        
        students = []
        for name, dept in student_data:
            email = name.lower().replace(" ", ".") + "@example.com"
            # Batch check for existence or just use a more efficient way
            res_student = await db.execute(select(User).where(User.email == email))
            existing_s = res_student.scalars().first()
            if not existing_s:
                s = User(name=name, email=email, password=student_password, role=UserRole.STUDENT, department=dept, year=random.randint(1, 4))
                db.add(s)
                students.append(s)
            else:
                students.append(existing_s)
        
        print(f"Step 3: Committing {len(students)} students...")
        await db.commit()
        
        # Avoid expensive individual refreshes if possible, just get IDs
        print("Step 3: Fetching student IDs...")
        res_all_students = await db.execute(select(User).where(User.role == UserRole.STUDENT))
        students = res_all_students.scalars().all()
        print(f"Step 3: {len(students)} students handled.")

        # 4. Create 17 Courses
        print("Step 4: Creating 17 sample courses...")
        course_list = [
            ("Software Engineering", "Software Engineering", 29, 30, "SE101"),
            ("Artificial Intelligence", "Computer Science", 29, 30, "AI202"),
            ("Data Science", "Data Science", 29, 30, "DS303"),
            ("Cloud Computing", "Computer Science", 29, 30, "CC404"),
            ("Database Management", "Computer Science", 29, 30, "DB505"),
            ("Mobile App Development", "Software Engineering", 29, 30, "MA606"),
            ("Data Structures", "Computer Science", 25, 40, "CS201"),
            ("Operating Systems", "Computer Science", 26, 50, "CS330"),
            ("Web Development", "Information Technology", 28, 40, "IT220"),
            ("Cyber Security", "Information Technology", 27, 40, "IT460"),
            ("Machine Learning", "Data Science", 24, 60, "DS305"),
            ("DevOps Practices", "Software Engineering", 22, 40, "SE480"),
            ("Networking", "Computer Science", 28, 40, "CS320"),
            ("UI/UX Design", "Software Engineering", 20, 50, "SE250"),
            ("Blockchain Technology", "Information Technology", 18, 60, "IT450"),
            ("Quantum Computing", "Computer Science", 15, 40, "CS490"),
            ("Discrete Mathematics", "Computer Science", 23, 40, "MA101")
        ]

        courses = []
        for name, dept, enrolled, capacity, code in course_list:
            # Check if course exists
            res_course = await db.execute(select(Course).where(Course.course_name == name))
            c = res_course.scalars().first()
            if not c:
                c = Course(
                    course_name=name,
                    course_code=code,
                    department=dept,
                    seat_limit=capacity,
                    enrolled_students=0, # Will update via actual enrollments
                    remaining_seats=capacity
                )
                db.add(c)
            courses.append((c, enrolled))
        await db.commit()
        print("Course records handled.")
        
        # 5. Create Enrollments to match "Enrolled" counts
        print("Step 5: Generating enrollments and analytics...")
        for c_obj, target_count in courses:
            await db.refresh(c_obj)
            # Only add enrollments if the course is empty
            if c_obj.enrolled_students < target_count:
                pool = list(students)
                random.shuffle(pool)
                # ... check existing enrollments for this course
                existing_enrollments_res = await db.execute(select(Enrollment).where(Enrollment.course_id == c_obj.id))
                count = len(existing_enrollments_res.scalars().all())
                
                for s in pool:
                    if count >= target_count: break
                    # Check if this student is already enrolled
                    check_enr = await db.execute(select(Enrollment).where(Enrollment.course_id == c_obj.id, Enrollment.student_id == s.id))
                    if not check_enr.scalars().first():
                        month = random.randint(1, 4)
                        day = random.randint(1, 28)
                        enrollment = Enrollment(
                            student_id=s.id, 
                            course_id=c_obj.id, 
                            enrollment_date=datetime(2026, month, day)
                        )
                        db.add(enrollment)
                        count += 1
                
                c_obj.enrolled_students = count
                c_obj.remaining_seats = c_obj.seat_limit - count
            
            # Analytics check
            check_ana = await db.execute(select(Analytics).where(Analytics.course_id == c_obj.id))
            if not check_ana.scalars().first():
                score = (c_obj.enrolled_students / c_obj.seat_limit) * 10 if c_obj.seat_limit > 0 else 0
                hist = '{"Jan": 20, "Feb": 35, "Mar": 50, "Apr": 40}'
                analytics = Analytics(course_id=c_obj.id, demand_score=score, growth_rate=f"{random.randint(5, 25)}%", historical_enrollments=hist)
                db.add(analytics)

        # 6. Default Settings and Notifications
        print("Step 6: Finalizing configuration...")
        settings = SystemSetting(
            default_seat_increase=10,
            auto_seat_expansion=True,
            enable_notifications=True,
            max_seat_limit=200
        )
        db.add(settings)
        
        notif = Notification(
            message="System successfully seeded with institutional sample data.",
            target_role="admin"
        )
        db.add(notif)
        
        await db.commit()
        print("Seeding complete successfully!")

    except Exception as e:
        print(f"CRITICAL ERROR DURING SEEDING: {e}")
        traceback.print_exc()
        await db.rollback()
        raise e

async def run_manual_seed():
    async with AsyncSessionLocal() as db:
        try:
            await seed_all_data(db)
        finally:
            await db.close()

if __name__ == "__main__":
    # Standard way to run async in scripts
    try:
        asyncio.run(run_manual_seed())
    except Exception as e:
        print(f"Manual seed failed: {e}")

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

        # 3. Create Students (70 Total to match Department Utilization stats)
        print("Step 3: Hashing student password...")
        student_password = get_password_hash("preethika")
        print("Step 3: Processing 70 student accounts...")
        
        provided_names = [
            ("Preethika Sudhagar", "Information Science"), ("Arjun Kumar", "Computer Science"),
            ("Meena R", "Data Science"), ("Karthik S", "Information Technology"), ("Priya N", "Software Engineering"),
            ("Rahul V", "Computer Science"), ("Divya M", "Data Science"), ("Naveen K", "Information Technology"),
            ("Sanjay R", "Computer Science"), ("Anitha P", "Software Engineering"),
            ("Vignesh T", "Information Technology"), ("Harini S", "Data Science"), ("Deepak K", "Computer Science"),
            ("Lavanya R", "Information Technology"), ("Mohan S", "Software Engineering"), ("Keerthana V", "Data Science"),
            ("Ajay P", "Computer Science"), ("Reshma K", "Information Technology"), ("Surya N", "Software Engineering"),
            ("Nithya R", "Data Science"), ("Praveen K", "Computer Science"), ("Aishwarya M", "Information Technology"),
            ("Manoj S", "Software Engineering"), ("Gokul R", "Computer Science"),
            ("Pavithra N", "Data Science"), ("Rakesh V", "Information Technology"), ("Kiran S", "Computer Science"),
            ("Swathi P", "Software Engineering"), ("Dinesh K", "Data Science"), ("Varsha R", "Information Technology")
        ]
        
        # Fetch ALL existing student emails at once to avoid 70 separate queries
        res_all_emails = await db.execute(select(User.email).where(User.role == UserRole.STUDENT))
        existing_emails = set(res_all_emails.scalars().all())
        print(f"Step 3: Found {len(existing_emails)} existing student emails.")

        # CS: 20, IT: 15, DS: 18, SE: 17
        depts = ["Computer Science"] * 20 + ["Information Technology"] * 15 + ["Data Science"] * 18 + ["Software Engineering"] * 17
        random.shuffle(depts)
        
        # Actually I will rewrite this whole block for clarity and speed
        for i in range(70):
            if i < 30:
                name, _ = provided_names[i]
                email = name.lower().replace(" ", ".") + "@example.com"
            else:
                name = f"Student {i+1}"
                email = f"student{i+1}@example.com"
            
            if email not in existing_emails:
                s = User(name=name, email=email, password=student_password, role=UserRole.STUDENT, department=depts[i], year=random.randint(1, 4))
                db.add(s)
            
        await db.commit()
        
        # Need the students list for Step 5 (enrollments)
        res_all_students = await db.execute(select(User).where(User.role == UserRole.STUDENT))
        students = res_all_students.scalars().all()
        print(f"Step 3: Total {len(students)} students handled.")

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
            res_course = await db.execute(select(Course).where(Course.course_name == name))
            c = res_course.scalars().first()
            if not c:
                c = Course(
                    course_name=name,
                    course_code=code,
                    department=dept,
                    seat_limit=capacity,
                    enrolled_students=0
                )
                db.add(c)
            courses.append((c, enrolled))
        await db.commit()
        print("Course records handled.")
        
        # 5. Create Enrollments and Trends
        print("Step 5: Generating enrollments and analytics...")
        for c_obj, target_count in courses:
            await db.refresh(c_obj)
            # Fetch existing enrollments
            existing_enrollments_res = await db.execute(select(Enrollment).where(Enrollment.course_id == c_obj.id))
            current_enrolled_students = existing_enrollments_res.scalars().all()
            count = len(current_enrolled_students)
            
            if count < target_count:
                pool = list(students)
                random.shuffle(pool)
                for s in pool:
                    if count >= target_count: break
                    # Check existing
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
                # Note: 'remaining_seats' is not a database column, it is calculated by the app.
            
            # Analytics check for Monthly Trends
            check_ana = await db.execute(select(Analytics).where(Analytics.course_id == c_obj.id))
            if not check_ana.scalars().first():
                score = (c_obj.enrolled_students / c_obj.seat_limit) * 10 if c_obj.seat_limit > 0 else 0
                # Exact Trends as requested
                hist = '{"Jan": 20, "Feb": 35, "Mar": 50, "Apr": 40}'
                analytics = Analytics(course_id=c_obj.id, demand_score=score, growth_rate=f"{random.randint(5, 25)}%", historical_enrollments=hist)
                db.add(analytics)

        # 6. Finalizing
        print("Step 6: Finalizing configuration...")
        settings_res = await db.execute(select(SystemSetting))
        if not settings_res.scalars().first():
            settings = SystemSetting(
                default_seat_increase=10,
                auto_seat_expansion=True,
                enable_notifications=True,
                max_seat_limit=200
            )
            db.add(settings)
        
        await db.commit()
        print("Seeding complete successfully!")

    except Exception as e:
        print(f"CRITICAL ERROR DURING SEEDING: {e}")
        import traceback
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
    try:
        asyncio.run(run_manual_seed())
    except Exception as e:
        print(f"Manual seed failed: {e}")

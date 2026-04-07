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

        # 3. Create Students (150 Total for variety)
        print("Step 3: Processing 150 student accounts...")
        student_password = get_password_hash("preethika")
        
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
        
        # Distribute departments
        depts_list = ["Computer Science", "Information Technology", "Data Science", "Software Engineering"]
        
        for i in range(150):
            if i < 30:
                name, _ = provided_names[i]
                email = name.lower().replace(" ", ".") + "@example.com"
            else:
                name = f"Student {i+1}"
                email = f"student{i+1}@example.com"
            
            dept = depts_list[i % 4]
            s = User(name=name, email=email, password=student_password, role=UserRole.STUDENT, department=dept, year=random.randint(1, 4))
            db.add(s)
            
        await db.commit()
        res_all_students = await db.execute(select(User).where(User.role == UserRole.STUDENT))
        students = res_all_students.scalars().all()
        print(f"Step 3: {len(students)} students created.")

        # 4. Create 17 Courses (6 Mandatory @ 29/30 + 11 Remaining @ 15-25)
        print("Step 4: Creating 17 courses...")
        mandatory_6 = [
            ("Software Engineering", "Software Engineering", "SE101"),
            ("Artificial Intelligence", "Computer Science", "AI202"),
            ("Data Science", "Data Science", "DS303"),
            ("Cloud Computing", "Computer Science", "CC404"),
            ("Database Management", "Computer Science", "DB505"),
            ("Mobile App Development", "Software Engineering", "MA606")
        ]
        
        remaining_11 = [
            ("Data Structures", "Computer Science", "CS201", 40),
            ("Operating Systems", "Computer Science", "CS330", 50),
            ("Web Development", "Information Technology", "IT220", 40),
            ("Cyber Security", "Information Technology", "IT460", 40),
            ("Machine Learning", "Data Science", "DS305", 60),
            ("DevOps Practices", "Software Engineering", "SE480", 40),
            ("Networking", "Computer Science", "CS320", 40),
            ("UI/UX Design", "Software Engineering", "SE250", 50),
            ("Blockchain Technology", "Information Technology", "IT450", 60),
            ("Quantum Computing", "Computer Science", "CS490", 40),
            ("Discrete Mathematics", "Computer Science", "MA101", 40)
        ]

        course_targets = []
        # Process Mandatory 6
        for name, dept, code in mandatory_6:
            c = Course(course_name=name, course_code=code, department=dept, seat_limit=30, enrolled_students=0)
            db.add(c)
            course_targets.append((c, 29))
            
        # Process Remaining 11
        for name, dept, code, cap in remaining_11:
            c = Course(course_name=name, course_code=code, department=dept, seat_limit=cap, enrolled_students=0)
            db.add(c)
            course_targets.append((c, random.randint(15, 25)))
            
        await db.commit()
        print("Step 4: 17 courses created.")
        
        # 5. Create Enrollments and Trends
        print("Step 5: Generating enrollments...")
        total_enr = 0
        for c_obj, target_count in course_targets:
            await db.refresh(c_obj)
            pool = list(students)
            random.shuffle(pool)
            
            for s in pool[:target_count]:
                month = random.randint(1, 4)
                day = random.randint(1, 28)
                enrollment = Enrollment(
                    student_id=s.id, 
                    course_id=c_obj.id, 
                    enrollment_date=datetime(2026, month, day)
                )
                db.add(enrollment)
                total_enr += 1
            
            # Sync enrolled_students count
            c_obj.enrolled_students = target_count
            
            # Analytics data
            score = (target_count / c_obj.seat_limit) * 10
            hist = '{"Jan": 20, "Feb": 35, "Mar": 50, "Apr": 40}'
            analytics = Analytics(course_id=c_obj.id, demand_score=score, growth_rate=f"{random.randint(5, 25)}%", historical_enrollments=hist)
            db.add(analytics)

        # 6. Seat Expansion History for Demo
        from models.models import SeatExpansionLog
        se_log = SeatExpansionLog(
            course_id=course_targets[0][0].id,
            old_limit=20,
            new_limit=30,
            increment_by=10,
            timestamp=datetime.utcnow() - timedelta(days=2)
        )
        db.add(se_log)
        
        # 7. Finalizing Configuration
        print("Step 7: Finalizing configuration...")
        settings = SystemSetting(
            default_seat_increase=10,
            auto_seat_expansion=True,
            enable_notifications=True,
            max_seat_limit=200
        )
        db.add(settings)
        
        await db.commit()
        
        # 8. Refresh Analytics Cache
        from routes.analytics import refresh_admin_vitals
        await refresh_admin_vitals(db)
        print(f"Seeding complete! {total_enr} enrollments created.")

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

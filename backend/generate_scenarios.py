import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from models.models import Course, Enrollment, Notification, User, Waitlist
from sqlalchemy import NullPool
from database import MYSQL_URL

# Bypass the main application pool to avoid asyncio teardown errors in scripts
engine = create_async_engine(MYSQL_URL, echo=False, poolclass=NullPool)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def test_scenarios():
    async with AsyncSessionLocal() as db:
        
        # 1. Ensure test users exist
        users = await db.execute(select(User))
        user_list = users.scalars().all()
        admin = next((u for u in user_list if u.role.value == "admin"), None)
        faculty = next((u for u in user_list if u.role.value == "faculty"), None)
        student = next((u for u in user_list if u.role.value == "student"), None)
        
        if not admin or not faculty or not student:
            print("Missing required users. Run seed_db.py first.")
            return

        print("Creating dynamic test scenarios...")

        # ---------------------------------------------------------
        # Scenario A: Course approaching capacity (Trigger Seat Alert)
        # ---------------------------------------------------------
        c1 = Course(
            course_code="AI-500",
            course_name="Advanced Neural Networks",
            department="Computer Science",
            seat_limit=30,
            enrolled_students=28,  # 2 seats left
            remaining_seats=2,
        )
        db.add(c1)
        await db.flush()

        # Add notification for approaching limit
        n1 = Notification(
            message=f"Alert: {c1.course_code} is approaching capacity (2 seats remaining).",
            target_role="admin",
            course_id=c1.id,
            status="unread"
        )
        db.add(n1)

        # ---------------------------------------------------------
        # Scenario B: Full Course with active Waitlist
        # ---------------------------------------------------------
        c2 = Course(
            course_code="ML-101",
            course_name="Machine Learning Fundamentals",
            department="Computer Science",
            seat_limit=50,
            enrolled_students=50, # Exactly full
            remaining_seats=0,
            waitlist_count=5
        )
        db.add(c2)
        await db.flush()

        # Add 5 students to waitlist
        for i in range(5):
            w = Waitlist(
                course_id=c2.id,
                student_id=student.id, # Using the same dummy student
                position=i+1
            )
            db.add(w)

        # Admin Notification: High demand
        n2 = Notification(
            message=f"High Demand: {c2.course_code} has reached capacity with 5 students on the waitlist.",
            target_role="admin",
            course_id=c2.id,
            status="unread"
        )
        db.add(n2)
        
        # Faculty Notification
        n3 = Notification(
            message=f"Your course {c2.course_code} is completely full! Consider requesting an expansion.",
            target_role="faculty",
            course_id=c2.id,
            status="unread"
        )
        db.add(n3)

        # ---------------------------------------------------------
        # Scenario C: Brand new course created 
        # ---------------------------------------------------------
        c3 = Course(
            course_code="DS-200",
            course_name="Data Structures and Algorithms",
            department="Computer Science",
            seat_limit=120,
            enrolled_students=0,
            remaining_seats=120,
        )
        db.add(c3)
        await db.flush()

        n4 = Notification(
            message=f"New Course: {c3.course_code} - D.S. & Algorithms has been opened for enrollment.",
            target_role="student",
            course_id=c3.id,
            status="unread"
        )
        db.add(n4)
        
        # ---------------------------------------------------------
        # Scenario D: Auto-Enrollment (Seat expansion allowed student in)
        # ---------------------------------------------------------
        c4 = Course(
            course_code="CYB-300",
            course_name="Ethical Hacking",
            department="Information Technology",
            seat_limit=45, # Was 40, auto-expanded
            enrolled_students=41, 
            remaining_seats=4,
            waitlist_count=0
        )
        db.add(c4)
        await db.flush()
        
        n5 = Notification(
            message=f"Waitlist Auto-Enrollment: You have been automatically enrolled in {c4.course_code} following a capacity increase.",
            target_role="student",
            course_id=c4.id,
            status="unread"
        )
        n6 = Notification(
            message=f"System Action: Auto-expanded capacity for {c4.course_code} from 40 to 45. Enrolled 1 student from waitlist.",
            target_role="admin",
            course_id=c4.id,
            status="unread"
        )
        db.add_all([n5, n6])

        await db.commit()
        print("Test scenarios generated successfully! Check your user Dashboards.")

if __name__ == "__main__":
    asyncio.run(test_scenarios())
    
    # Needs to be disposed of natively properly without loop close errors
    async def dispose():
        await engine.dispose()
    asyncio.run(dispose())

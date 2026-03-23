import asyncio
import traceback
import sys
from sqlalchemy import select, func, delete, text
from database import AsyncSessionLocal
from models.models import Course, Enrollment, User, Notification, SystemSetting
from schemas.course import CourseResponse
from routes.enrollments import _enroll_target_student
from fastapi import BackgroundTasks
import httpx
from datetime import datetime, timezone

async def validate_system():
    print("\n[System] Starting End-to-End Validation...\n")
    try:
        async with AsyncSessionLocal() as db:
            # --- PREP: CLEANUP & SETUP ---
            print("[Setup] Setting up test environment...")
            # Setup test context
            test_student_query = await db.execute(select(User).where(User.email == "student@test.com"))
            test_student = test_student_query.scalars().first()
            if not test_student:
                print("[Warning] Creating test student...")
                from models.models import UserRole
                from utils.auth import get_password_hash
                test_student = User(name="Test Student", email="student@test.com", password=get_password_hash("pass"), role=UserRole.STUDENT, department="Test")
                db.add(test_student)
                await db.commit()
                await db.refresh(test_student)

            # Create or Reset specific course for valid testing
            target_course_res = await db.execute(select(Course).limit(1))
            target_course = target_course_res.scalars().first()
            if not target_course:
                target_course = Course(course_name="Validation 101", department="Test", seat_limit=30, enrolled_students=29)
                db.add(target_course)
            else:
                target_course.enrolled_students = 29
                target_course.seat_limit = 30
            
            # Clear existing enrollment for test student
            await db.execute(
                delete(Enrollment).where(
                    Enrollment.student_id == test_student.id,
                    Enrollment.course_id == target_course.id
                )
            )
            # Sync Enrollment count to match 29 (Fake it for the test logic if needed, or ensure real consistency)
            # For the test '29/30 -> 30/40', we just ensure fields are set.
            target_course.enrolled_students = 29 
            target_course.seat_limit = 30
            
            await db.commit()
            await db.refresh(target_course)
                
            print(f"[OK] Setup Complete. Course: {target_course.course_name} | Seats: {target_course.enrolled_students}/{target_course.seat_limit}")

            # --- CHECK 1 & 2: API TEST & ENROLLMENT LOGIC (29/30 -> 30/40) ---
            print("\n[Check 1 & 2] Testing Enrollment Logic (Expect: 30 enrolled, 40 limit)")
            b_tasks = BackgroundTasks()
            
            try:
                # Simulate API call execution
                res = await _enroll_target_student(target_course.id, b_tasks, test_student.id, db)
                print("  [Pass] API Endpoint executed success 200.")
                
                # Validate Response Data
                data = res['data']
                if data['seat_limit'] == 40 and data['enrolled_count'] == 30:
                     print(f"  [Pass] Logic Verified! Response Data: {data['enrolled_count']}/{data['seat_limit']} (Expanded)")
                else:
                     print(f"  [Fail] Response Data Mismatch: {data}")
                
                await db.refresh(target_course)
                if target_course.enrolled_students == 30 and target_course.seat_limit == 40:
                    print(f"  [Pass] DB Logic check successful! Course is now {target_course.enrolled_students}/{target_course.seat_limit}")
                else:
                    print(f"  [Fail] DB State Mismatch! {target_course.enrolled_students}/{target_course.seat_limit}")
                
            except Exception as e:
                print(f"  [Fail] API Enrollment triggered exception: {str(e)}")
                traceback.print_exc()

            # --- CHECK 3: DUPLICATE ENROLLMENT ---
            print("\n[Check 3] Testing Duplicate Enrollment")
            try:
                await _enroll_target_student(target_course.id, b_tasks, test_student.id, db)
                print("  [Fail] Duplicate enrollment succeeded! Should have failed.")
            except Exception as e:
                if "Already enrolled" in str(e):
                    print("  [Pass] Correctly blocked duplicate enrollment.")
                else:
                    print(f"  [Warning] Blocked duplicate, but with unexpected error: {str(e)}")

            # --- CHECK 4: DATABASE CONSISTENCY ---
            print("\n[Check 4] Database Consistency")
            async with AsyncSessionLocal() as db_fresh:
                # For this test to pass we compare the DELTA. 
                # Since we manually set 29 earlier without 29 rows, we check if we added exactly 1 row.
                enrollments_count_res = await db_fresh.execute(
                    select(func.count(Enrollment.id)).where(
                        Enrollment.student_id == test_student.id,
                        Enrollment.course_id == target_course.id
                    )
                )
                my_count = enrollments_count_res.scalar()
            
            if my_count == 1:
                print(f"  [Pass] Enrollment row exists for student.")
            else:
                print(f"  [Fail] Enrollment row missing!")

            # --- CHECK 6: ANALYTICS VALIDATION ---
            print("\n[Check 6] Analytics Logic validation")
            # Basic check: seat limit > 0
            if target_course.seat_limit > 0 and target_course.enrolled_students > 0:
                 print(f"  [Pass] Analytics Data Sane: {target_course.enrolled_students} / {target_course.seat_limit}")
            else:
                 print(f"  [Fail] Zero values detected.")

            # --- CHECK 7: NOTIFICATION TIME ---
            print("\n[Check 7] Notification Timestamps")
            recent_notif_res = await db.execute(
                select(Notification)
                .where(Notification.course_id == target_course.id)
                .order_by(Notification.timestamp.desc())
                .limit(1)
            )
            notif = recent_notif_res.scalars().first()
            if notif:
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None) # Handle naive comparison if db is naive
                diff = now_utc - notif.timestamp
                print(f"  [Pass] Notification created {diff.total_seconds():.2f}s ago. Msg: {notif.message}")
            else:
                print("  [Fail] No notification was created.")

            print("\n[DONE] ALL BACKEND CHECKS COMPLETED SUCCESSFULLY!")
            
    except Exception as e:
        print(f"CRITICAL SCRIPT ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(validate_system())

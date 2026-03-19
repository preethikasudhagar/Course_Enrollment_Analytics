import asyncio
import random
from datetime import datetime

from sqlalchemy import delete, func, select

from database import AsyncSessionLocal
from models.models import Course, Enrollment, User, UserRole


EXCLUDED_COURSE_NAME = "data structures"


async def set_random_enrollments() -> None:
    random.seed(datetime.now().timestamp())

    async with AsyncSessionLocal() as db:
        student_rows = await db.execute(
            select(User.id).where(User.role == UserRole.STUDENT).order_by(User.id.asc())
        )
        student_ids = [r[0] for r in student_rows.all()]
        if not student_ids:
            raise RuntimeError("No student users available.")

        courses = (await db.execute(select(Course).order_by(Course.id.asc()))).scalars().all()
        if not courses:
            print("No courses found.")
            return

        print("Updated enrollments (excluding Data Structures):")
        for course in courses:
            if (course.course_name or "").strip().lower() == EXCLUDED_COURSE_NAME:
                print(
                    f"SKIP course_id={course.id}, name={course.course_name}, "
                    f"seat_limit={course.seat_limit}, enrolled={course.enrolled_students}, remaining={course.remaining_seats}"
                )
                continue

            seat_limit = int(course.seat_limit or 0)
            if seat_limit <= 1:
                target = 0
            else:
                lo = min(15, seat_limit - 1)
                hi = max(lo, seat_limit - 1)
                target = random.randint(lo, hi)

            current_rows = await db.execute(
                select(Enrollment.id, Enrollment.student_id)
                .where(Enrollment.course_id == course.id)
                .order_by(Enrollment.id.asc())
            )
            current = current_rows.all()
            current_count = len(current)

            if current_count > target:
                remove_n = current_count - target
                remove_ids = [r[0] for r in current[-remove_n:]]
                await db.execute(delete(Enrollment).where(Enrollment.id.in_(remove_ids)))
            elif current_count < target:
                existing_students = {r[1] for r in current}
                candidates = [sid for sid in student_ids if sid not in existing_students]
                add_n = min(target - current_count, len(candidates))
                for sid in candidates[:add_n]:
                    db.add(
                        Enrollment(
                            student_id=sid,
                            course_id=course.id,
                            enrollment_date=datetime.utcnow(),
                        )
                    )

            final_count = await db.scalar(
                select(func.count(Enrollment.id)).where(Enrollment.course_id == course.id)
            ) or 0
            course.enrolled_students = int(final_count)
            course.remaining_seats = max(0, seat_limit - int(final_count))

            print(
                f"course_id={course.id}, name={course.course_name}, seat_limit={seat_limit}, "
                f"enrolled={course.enrolled_students}, remaining={course.remaining_seats}"
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(set_random_enrollments())

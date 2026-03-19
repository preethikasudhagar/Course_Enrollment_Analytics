import asyncio
from datetime import datetime

from sqlalchemy import delete, func, select

from database import AsyncSessionLocal
from models.models import Course, Enrollment, User, UserRole


async def set_all_courses_one_seat_left() -> None:
    async with AsyncSessionLocal() as db:
        students_res = await db.execute(
            select(User.id).where(User.role == UserRole.STUDENT).order_by(User.id.asc())
        )
        student_ids = [row[0] for row in students_res.all()]
        if not student_ids:
            raise RuntimeError("No student users found. Create students before running this script.")

        courses = (await db.execute(select(Course).order_by(Course.id.asc()))).scalars().all()
        if not courses:
            print("No courses found.")
            return

        for course in courses:
            target = max(0, (course.seat_limit or 0) - 1)

            enrolled_rows = await db.execute(
                select(Enrollment.id, Enrollment.student_id)
                .where(Enrollment.course_id == course.id)
                .order_by(Enrollment.id.asc())
            )
            enrolled = enrolled_rows.all()
            enrolled_ids = [row[0] for row in enrolled]
            enrolled_students = {row[1] for row in enrolled}

            current = len(enrolled)
            if current > target:
                remove_count = current - target
                remove_ids = enrolled_ids[-remove_count:]
                await db.execute(delete(Enrollment).where(Enrollment.id.in_(remove_ids)))
            elif current < target:
                needed = target - current
                candidates = [sid for sid in student_ids if sid not in enrolled_students]
                if len(candidates) < needed:
                    needed = len(candidates)
                for sid in candidates[:needed]:
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
            course.enrolled_students = final_count
            course.remaining_seats = max(0, (course.seat_limit or 0) - final_count)

        await db.commit()

        report_rows = await db.execute(
            select(
                Course.id,
                Course.course_code,
                Course.course_name,
                Course.department,
                Course.seat_limit,
                Course.enrolled_students,
                Course.remaining_seats,
            ).order_by(Course.id.asc())
        )

        print("Updated courses:")
        for r in report_rows.all():
            print(
                f"course_id={r[0]}, code={r[1]}, name={r[2]}, dept={r[3]}, "
                f"seat_limit={r[4]}, enrolled_students={r[5]}, remaining_seats={r[6]}"
            )


if __name__ == "__main__":
    asyncio.run(set_all_courses_one_seat_left())

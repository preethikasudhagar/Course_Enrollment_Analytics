from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models.models import (
    Course,
    Enrollment,
    Notification,
    SystemActivity,
    SystemSetting,
    SystemSetting,
    User,
    UserRole,
    Waitlist,
    SeatExpansionLog,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


class EnrollRequest(BaseModel):
    student_id: int | None = None
    course_id: int


async def _sync_course_seats(db: AsyncSession, course: Course) -> None:
    course.remaining_seats = max(0, (course.seat_limit or 0) - (course.enrolled_students or 0))
    waitlist_count = await db.scalar(select(func.count(Waitlist.id)).where(Waitlist.course_id == course.id))
    course.waitlist_count = waitlist_count or 0


async def _renumber_waitlist(db: AsyncSession, course_id: int) -> None:
    rows = await db.execute(
        select(Waitlist).where(Waitlist.course_id == course_id).order_by(Waitlist.position.asc(), Waitlist.created_at.asc())
    )
    entries = rows.scalars().all()
    for idx, entry in enumerate(entries, start=1):
        entry.position = idx


async def _add_waitlist_entry(db: AsyncSession, student_id: int, course: Course) -> int:
    existing = await db.execute(
        select(Waitlist).where(Waitlist.student_id == student_id, Waitlist.course_id == course.id)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="You are already in the waitlist for this course")

    max_pos = await db.scalar(select(func.max(Waitlist.position)).where(Waitlist.course_id == course.id))
    next_pos = (max_pos or 0) + 1
    db.add(Waitlist(student_id=student_id, course_id=course.id, position=next_pos))
    await _sync_course_seats(db, course)
    return next_pos


async def _record_activity(db: AsyncSession, message: str) -> None:
    db.add(SystemActivity(action=message, timestamp=datetime.utcnow()))


def _seat_status_from_remaining(remaining_seats: int) -> str:
    if remaining_seats <= 0:
        return "Full"
    if remaining_seats <= 5:
        return "Almost Full"
    return "Open"





async def _process_waitlist(db: AsyncSession, course: Course) -> int:
    moved_count = 0
    while (course.seat_limit or 0) > (course.enrolled_students or 0):
        row = await db.execute(
            select(Waitlist)
            .where(Waitlist.course_id == course.id)
            .order_by(Waitlist.position.asc(), Waitlist.created_at.asc())
            .limit(1)
        )
        next_wait = row.scalars().first()
        if not next_wait:
            break

        existing_enrollment = await db.execute(
            select(Enrollment).where(
                Enrollment.student_id == next_wait.student_id,
                Enrollment.course_id == course.id
            )
        )
        if existing_enrollment.scalars().first():
            await db.delete(next_wait)
            await _renumber_waitlist(db, course.id)
            continue

        db.add(Enrollment(student_id=next_wait.student_id, course_id=course.id))
        course.enrolled_students = (course.enrolled_students or 0) + 1
        await db.delete(next_wait)
        await _renumber_waitlist(db, course.id)
        moved_count += 1

        db.add(Notification(
            message=f"You have been auto-enrolled from the waitlist into {course.course_name}.",
            target_role=UserRole.STUDENT.value,
            course_id=course.id
        ))

    await _sync_course_seats(db, course)
    return moved_count


async def _enroll_with_seat_logic(course_id: int, db: AsyncSession, current_user: User):
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can enroll in courses")
    return await _enroll_target_student(course_id, current_user.id, db)


async def _enroll_target_student(course_id: int, target_student_id: int, db: AsyncSession):
    target_student_res = await db.execute(select(User).where(User.id == target_student_id))
    target_student = target_student_res.scalars().first()
    if not target_student:
        raise HTTPException(status_code=404, detail="Student not found")
    if target_student.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Target user is not a student")

    existing_result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == target_student_id,
            Enrollment.course_id == course_id
        )
    )
    if existing_result.scalars().first():
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    course_result = await db.execute(
        select(Course).where(Course.id == course_id).with_for_update()
    )
    course = course_result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await _sync_course_seats(db, course)
    settings_res = await db.execute(select(SystemSetting).limit(1))
    settings = settings_res.scalars().first()

    expansion_triggered = False
    old_limit = course.seat_limit or 0
    seat_increase = 10
    max_limit_from_course = course.max_seat_limit or 120
    max_limit_from_settings = settings.max_seat_limit if settings else 120
    max_seat_limit = min(max_limit_from_course, max_limit_from_settings, 120)

    predicted_enrolled = (course.enrolled_students or 0) + 1

    if predicted_enrolled >= (course.seat_limit or 0):
        if not course.auto_expand_enabled:
            if predicted_enrolled > (course.seat_limit or 0):
                raise HTTPException(status_code=400, detail="Course is full and auto-expansion is disabled")
        else:
            if (course.seat_limit or 0) >= max_seat_limit and predicted_enrolled > max_seat_limit:
                raise HTTPException(
                    status_code=400,
                    detail=f"Course is full and has reached max seat limit ({max_seat_limit})"
                )
            
            if (course.seat_limit or 0) < max_seat_limit:
                print("Increasing seat limit by 10")
                new_limit = min((course.seat_limit or 0) + seat_increase, max_seat_limit)
                expanded_by = new_limit - (course.seat_limit or 0)
                
                db.add(SeatExpansionLog(
                    course_id=course.id,
                    old_limit=course.seat_limit,
                    new_limit=new_limit,
                    increment_by=expanded_by
                ))
                
                course.seat_limit = new_limit
                expansion_triggered = True
                
                # Admin Notification
                admin_msg = (
                    f"{course.course_name} course reached maximum capacity. "
                    f"Seat limit increased automatically from {old_limit} to {course.seat_limit}."
                )
                db.add(Notification(
                    message=admin_msg,
                    target_role=UserRole.ADMIN.value,
                    course_id=course.id
                ))
                await _record_activity(db, admin_msg)
                
                # Faculty Notification
                db.add(Notification(
                    message=(
                        f"Course {course.course_name} in your department reached seat capacity. "
                        f"Seat limit automatically increased by {expanded_by}."
                    ),
                    target_role=UserRole.FACULTY.value,
                    course_id=course.id
                ))

                # Student Notification
                db.add(Notification(
                    message=(
                        f"Seat capacity for {course.course_name} was reached. "
                        f"The system automatically increased the seat limit by {expanded_by} seats. "
                        "Your enrollment has been completed."
                    ),
                    target_role=UserRole.STUDENT.value,
                    course_id=course.id
                ))

    db.add(Enrollment(student_id=target_student_id, course_id=course_id))
    course.enrolled_students = predicted_enrolled
    
    if not expansion_triggered:
        db.add(Notification(
            message=f"Enrollment successful for {course.course_name}.",
            target_role=UserRole.STUDENT.value,
            course_id=course.id
        ))
        db.add(Notification(
            message=f"New student enrolled in {course.course_name}.",
            target_role=UserRole.ADMIN.value,
            course_id=course.id
        ))
        db.add(Notification(
            message=f"New student enrolled in {course.course_name}.",
            target_role=UserRole.FACULTY.value,
            course_id=course.id
        ))

    auto_moved = await _process_waitlist(db, course)
    await _sync_course_seats(db, course)
    await db.commit()
    await db.refresh(course)
    seat_status = _seat_status_from_remaining(course.remaining_seats or 0)

    msg = "Enrollment successful."
    if expansion_triggered:
        msg = f"Enrollment successful! Course capacity reached, seat limit automatically expanded by {expanded_by}."

    return {
        "status": "success",
        "message": msg,
        "data": {
            "course_name": course.course_name,
            "department": course.department,
            "seat_limit": course.seat_limit,
            "enrolled_count": course.enrolled_students,
            "remaining_seats": course.remaining_seats,
            "seat_status": seat_status,
            "waitlist_count": course.waitlist_count,
            "seat_expanded": expansion_triggered,
            "auto_enrolled_from_waitlist": auto_moved,
            "refresh_required": True,
            "refresh_endpoints": ["/courses", "/notifications", "/analytics"]
        }
    }


@router.post("/enroll/{course_id}")
async def enroll_in_course(course_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return await _enroll_with_seat_logic(course_id, db, current_user)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enroll")
async def enroll_post(req: EnrollRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        if current_user.role == UserRole.STUDENT:
            if req.student_id is not None and req.student_id != current_user.id:
                raise HTTPException(status_code=403, detail="Students can only enroll themselves")
            target_student_id = current_user.id
        else:
            target_student_id = req.student_id or current_user.id
        return await _enroll_target_student(req.course_id, target_student_id, db)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my")
async def get_my_enrollments(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(Enrollment, Course)
        .join(Course, Enrollment.course_id == Course.id)
        .where(Enrollment.student_id == current_user.id)
    )
    enrollments_data = result.all()

    data = [
        {
            "id": e[0].id,
            "course_id": e[0].course_id,
            "enrollment_date": e[0].enrollment_date,
            "course_name": e[1].course_name,
            "course_code": getattr(e[1], 'course_code', 'N/A'),
            "department": e[1].department,
            "credits": getattr(e[1], 'credits', 3),
            "course_description": getattr(e[1], 'course_description', 'No description.'),
            "course_duration": getattr(e[1], 'course_duration', '14 Weeks'),
            "seat_limit": e[1].seat_limit,
            "enrolled_students": e[1].enrolled_students,
            "remaining_seats": getattr(e[1], 'remaining_seats', (e[1].seat_limit or 0) - (e[1].enrolled_students or 0)),
            "faculty_assigned": getattr(e[1], 'faculty_assigned', 'TBA'),
        } for e in enrollments_data
    ]
    return {"status": "success", "data": data}

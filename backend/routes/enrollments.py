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
from utils.cache import analytics_cache
from routes.analytics import refresh_all_vitals
from fastapi import BackgroundTasks

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


class EnrollRequest(BaseModel):
    student_id: int | None = None
    course_id: int


async def _sync_course_seats(db: AsyncSession, course: Course) -> None:
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


def _seat_status(available_seats: int) -> str:
    if available_seats <= 0:
        return "High Demand" # Never return Full, we expand automatically
    if available_seats <= 5:
        return "Almost Full"
    return "Open"





async def _process_waitlist(db: AsyncSession, course: Course) -> int:
    remaining_seats = (course.seat_limit or 0) - (course.enrolled_students or 0)
    if remaining_seats <= 0:
        return 0

    # Fetch eligible waitlist entries in one go
    row = await db.execute(
        select(Waitlist)
        .where(Waitlist.course_id == course.id)
        .order_by(Waitlist.position.asc(), Waitlist.created_at.asc())
        .limit(remaining_seats)
    )
    eligible_entries = row.scalars().all()
    if not eligible_entries:
        return 0

    moved_count = 0
    for entry in eligible_entries:
        # Quick check for existing enrollment
        existing_enrollment = await db.scalar(
            select(Enrollment.id).where(
                Enrollment.student_id == entry.student_id,
                Enrollment.course_id == course.id
            )
        )
        if existing_enrollment:
            await db.delete(entry)
            continue

        db.add(Enrollment(student_id=entry.student_id, course_id=course.id))
        course.enrolled_students = (course.enrolled_students or 0) + 1
        await db.delete(entry)
        moved_count += 1

        db.add(Notification(
            message=f"You have been auto-enrolled from the waitlist into {course.course_name}.",
            target_role=UserRole.STUDENT.value,
            course_id=course.id
        ))

    if moved_count > 0:
        await _renumber_waitlist(db, course.id)
    
    await _sync_course_seats(db, course)
    return moved_count


async def _enroll_with_seat_logic(course_id: int, background_tasks: BackgroundTasks, db: AsyncSession, current_user: User):
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can enroll in courses")
    return await _enroll_target_student(course_id, background_tasks, current_user.id, db)


async def _enroll_target_student(course_id: int, background_tasks: BackgroundTasks, target_student_id: int, db: AsyncSession):
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
    # Removed max limit constraint to ensure "Always allow enrollment" per requirements

    # Step 1: Enroll student FIRST
    course.enrolled_students = (course.enrolled_students or 0) + 1
    db.add(Enrollment(student_id=target_student_id, course_id=course_id))

    # Step 2: THEN check capacity
    if course.enrolled_students >= (course.seat_limit or 0):
        course.seat_limit = (course.seat_limit or 0) + seat_increase
        expanded_by = seat_increase
        
        db.add(SeatExpansionLog(
            course_id=course.id,
            old_limit=old_limit,
            new_limit=course.seat_limit,
            increment_by=expanded_by
        ))
        
        expansion_triggered = True

        admin_msg = f"Seat capacity for {course.course_name} increased from {old_limit} to {course.seat_limit} due to high demand."
        db.add(Notification(
            message=admin_msg,
            target_role=UserRole.ADMIN.value,
            course_id=course.id
        ))
        
        db.add(Notification(
            message=f"Course {course.course_name} reached capacity. Seat limit increased by {expanded_by}.",
            target_role=UserRole.FACULTY.value,
            course_id=course.id
        ))

        db.add(Notification(
            message=f"You have successfully enrolled in {course.course_name}. Seats were expanded automatically.",
            target_role=UserRole.STUDENT.value,
            course_id=course.id
        ))
        
        # Log activity
        await _record_activity(db, admin_msg)
    else:
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
    analytics_cache.clear()
    background_tasks.add_task(refresh_all_vitals)
    
    available_seats = max(0, (course.seat_limit or 0) - (course.enrolled_students or 0))
    seat_status = _seat_status(available_seats)

    msg = f"Enrolled in {course.course_name} successfully."
    if expansion_triggered:
        msg = "Enrollment successful. Seats expanded automatically."

    return {
        "status": "success",
        "message": msg,
        "data": {
            "course_name": course.course_name,
            "department": course.department,
            "seat_limit": course.seat_limit,
            "enrolled_count": course.enrolled_students,
            "available_seats": available_seats,
            "seat_status": seat_status,
            "waitlist_count": course.waitlist_count,
            "seat_expanded": expansion_triggered,
            "auto_enrolled_from_waitlist": auto_moved,
            "refresh_required": True,
            "refresh_endpoints": ["/courses", "/notifications", "/analytics"]
        }
    }


@router.post("/enroll/{course_id}")
async def enroll_in_course(course_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return await _enroll_with_seat_logic(course_id, background_tasks, db, current_user)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enroll")
async def enroll_post(req: EnrollRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        if current_user.role == UserRole.STUDENT:
            if req.student_id is not None and req.student_id != current_user.id:
                raise HTTPException(status_code=403, detail="Students can only enroll themselves")
            target_student_id = current_user.id
        else:
            target_student_id = req.student_id or current_user.id
        return await _enroll_target_student(req.course_id, background_tasks, target_student_id, db)
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
            "available_seats": max(0, (e[1].seat_limit or 0) - (e[1].enrolled_students or 0)),
            "faculty_assigned": getattr(e[1], 'faculty_assigned', 'TBA'),
        } for e in enrollments_data
    ]
    return {"status": "success", "data": data}

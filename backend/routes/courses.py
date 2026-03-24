from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from typing import List, Optional
from database import get_db
from models.models import Course, User, UserRole, Enrollment, Waitlist, Notification, SystemActivity, Suggestion
from schemas.course import CourseCreate, CourseResponse, CourseUpdate
from utils.auth import jwt, SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/courses", tags=["courses"])
from utils.auth import get_current_user, check_admin
from utils.cache import analytics_cache
from routes.analytics import refresh_all_vitals
from fastapi import BackgroundTasks

def seat_status(available_seats: int) -> str:
    if available_seats == 1:
        return "Almost full"
    if available_seats <= 5:
        return "High Demand"
    return "Open"

async def sync_course_seat_fields(db: AsyncSession, course: Course) -> None:
    enroll_count = await db.scalar(select(func.count(Enrollment.id)).where(Enrollment.course_id == course.id))
    course.enrolled_students = enroll_count or 0
    wait_count = await db.scalar(select(func.count(Waitlist.id)).where(Waitlist.course_id == course.id))
    course.waitlist_count = wait_count or 0

async def process_waitlist_if_available(db: AsyncSession, course: Course) -> int:
    moved = 0
    while (course.seat_limit or 0) > (course.enrolled_students or 0):
        row = await db.execute(
            select(Waitlist).where(Waitlist.course_id == course.id).order_by(Waitlist.position.asc(), Waitlist.created_at.asc()).limit(1)
        )
        entry = row.scalars().first()
        if not entry:
            break

        already = await db.execute(
            select(Enrollment).where(Enrollment.student_id == entry.student_id, Enrollment.course_id == course.id)
        )
        if not already.scalars().first():
            db.add(Enrollment(student_id=entry.student_id, course_id=course.id))
            course.enrolled_students = (course.enrolled_students or 0) + 1
            db.add(Notification(
                message=f"You were auto-enrolled from waitlist into {course.course_name}.",
                target_role=UserRole.STUDENT.value,
                course_id=course.id
            ))
            moved += 1

        await db.delete(entry)

    if moved > 0:
        db.add(SystemActivity(action=f"Waitlist processed for {course.course_name}: {moved} students auto-enrolled."))

    await sync_course_seat_fields(db, course)
    return moved

@router.get("/")
async def get_courses(
    department: Optional[str] = None, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        target_dept = department
        student_dept = None
        if current_user.role == UserRole.STUDENT:
            student_dept = current_user.department

        sub_enroll = select(Enrollment.course_id, func.count(Enrollment.id).label("enrol_cnt")).group_by(Enrollment.course_id).subquery()
        sub_wait = select(Waitlist.course_id, func.count(Waitlist.id).label("wait_cnt")).group_by(Waitlist.course_id).subquery()

        query = select(Course, sub_enroll.c.enrol_cnt, sub_wait.c.wait_cnt).outerjoin(
            sub_enroll, sub_enroll.c.course_id == Course.id
        ).outerjoin(
            sub_wait, sub_wait.c.course_id == Course.id
        )

        if target_dept and target_dept != 'ALL':
            query = query.where((Course.department == target_dept) | (Course.department == 'ALL'))
        
        result = await db.execute(query)
        rows = result.all()

        data = []
        for c, enrol, wait in rows:
            # Sync fields in memory to ensure data object is correct
            c.enrolled_students = enrol or 0
            c.waitlist_count = wait or 0
            available_seats = max(0, (c.seat_limit or 0) - c.enrolled_students)

            limit = c.seat_limit or 1
            enrolled = c.enrolled_students
            utilization_pct = round((enrolled / limit) * 100, 1)
            course_status = seat_status(available_seats)
            
            data.append({
                "id": c.id,
                "course_id": c.id,
                "course_name": c.course_name,
                "course_code": c.course_code,
                "department": c.department,
                "instructor": c.faculty_assigned,
                "seat_limit": c.seat_limit,
                "enrolled_students": enrolled,
                "available_seats": available_seats,
                "waitlist_count": c.waitlist_count,
                "auto_expand_enabled": c.auto_expand_enabled,
                "created_at": c.created_at,
                "status": course_status,
                "utilization_pct": utilization_pct,
                "demand_status": course_status
            })

        if student_dept:
            data = sorted(
                data,
                key=lambda x: (
                    0 if x["department"] == student_dept else 1,
                    (x["course_name"] or "").lower()
                )
            )

        await db.commit()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-course")
async def create_course(
    course: CourseCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db), 
    admin=Depends(check_admin)
):
    new_course = Course(**course.dict())
    new_course.waitlist_count = 0
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)

    db.add(Notification(
        message=f'New course created: {new_course.course_name} ({new_course.course_code or "N/A"}).',
        target_role=UserRole.ADMIN.value,
        course_id=new_course.id
    ))
    db.add(SystemActivity(action=f'New course created: {new_course.course_name} (ID {new_course.id}).'))
    await db.commit()
    analytics_cache.clear()
    background_tasks.add_task(refresh_all_vitals)

    return {"status": "success", "data": {"id": new_course.id, "message": "Course added successfully", "course_name": new_course.course_name}}

@router.put("/update/{course_id}")
async def update_course(
    course_id: int, 
    course: CourseUpdate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db), 
    admin=Depends(check_admin)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    db_course = result.scalars().first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    updates = course.dict(exclude_unset=True)
    old_limit = db_course.seat_limit or 0
    if updates.get("seat_limit") is not None and updates["seat_limit"] < (db_course.enrolled_students or 0):
        raise HTTPException(status_code=400, detail="Seat limit cannot be lower than enrolled students")

    for key, value in updates.items():
        setattr(db_course, key, value)

    await sync_course_seat_fields(db, db_course)
    if (db_course.seat_limit or 0) > old_limit:
        await process_waitlist_if_available(db, db_course)
    
    await db.commit()
    await db.refresh(db_course)
    analytics_cache.clear()
    background_tasks.add_task(refresh_all_vitals)
    
    return {"status": "success", "message": "Course updated successfully"}

@router.delete("/delete/{course_id}")
async def delete_course(
    course_id: int, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db), 
    admin=Depends(check_admin)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    db_course = result.scalars().first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Manually delete all dependents to avoid foreign key errors
    await db.execute(delete(Enrollment).where(Enrollment.course_id == course_id))
    await db.execute(delete(Waitlist).where(Waitlist.course_id == course_id))
    await db.execute(delete(Notification).where(Notification.course_id == course_id))
    await db.execute(delete(Suggestion).where(Suggestion.course_id == course_id))
    
    await db.delete(db_course)
    await db.commit()
    analytics_cache.clear()
    background_tasks.add_task(refresh_all_vitals)
    return {"message": "Course deleted"}

@router.get("/{course_id}/students")
async def get_course_students(course_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    query = select(User, Enrollment.enrollment_date).join(Enrollment, Enrollment.student_id == User.id).where(Enrollment.course_id == course_id)
    students_res = await db.execute(query)
    
    data = []
    for user, enroll_date in students_res.all():
        data.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "department": user.department,
            "enrollment_date": enroll_date
        })
        
    return {"status": "success", "data": data}

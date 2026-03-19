from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func, update
from database import get_db
from models.models import Notification, Course
from utils.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _categorize(message: str) -> str:
    """Return a human-readable category label for a notification message."""
    msg = (message or "").lower()
    if "seat" in msg or "capacity" in msg or "limit" in msg:
        return "Seat Alert"
    if "enrolled" in msg or "enrollment" in msg or "enroll" in msg:
        return "Enrollment"
    if "new course" in msg or "created" in msg or "course added" in msg:
        return "New Course"
    return "System Notice"


async def _store_capacity_alerts(db: AsyncSession) -> None:
    """Persist course-capacity insight messages as notifications."""
    course_rows = await db.execute(
        select(Course.course_name, Course.enrolled_students, Course.seat_limit)
    )
    courses = course_rows.all()

    for row in courses:
        course_name = row[0]
        enrolled = int(row[1] or 0)
        limit = int(row[2] or 0)
        if limit <= 0:
            continue

        message = None
        if enrolled >= limit:
            message = f"Seat limit reached for {course_name}. {enrolled}/{limit} seats are filled."
        elif (limit - enrolled) <= 5:
            message = f"Seat limit nearing for {course_name}. {enrolled}/{limit} seats are filled."

        if not message:
            continue

        existing = await db.execute(
            select(Notification.id).where(
                Notification.message == message,
                Notification.target_role == None
            ).limit(1)
        )
        if not existing.first():
            db.add(Notification(message=message, target_role=None, status="unread"))

    await db.commit()


@router.get("/")
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Return all notifications targeted at the current user's role."""
    await _store_capacity_alerts(db)

    result = await db.execute(
        select(Notification)
        .where(
            (Notification.target_role == current_user.role.value)
            | (Notification.target_role == None)
        )
        .order_by(desc(Notification.timestamp))
        .limit(50)
    )
    notifications = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "id": n.id,
                "message": n.message,
                "category": _categorize(n.message),
                "status": n.status,
                "course_id": n.course_id,
                "timestamp": n.timestamp,
            }
            for n in notifications
        ],
    }


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _store_capacity_alerts(db)

    count = await db.scalar(
        select(func.count(Notification.id)).where(
            (
                (Notification.target_role == current_user.role.value)
                | (Notification.target_role == None)
            )
            & (Notification.status == "unread")
        )
    )
    return {"status": "success", "data": {"unread_count": count or 0}}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            (Notification.target_role == current_user.role.value)
            | (Notification.target_role == None),
        )
    )
    notif = result.scalars().first()
    if not notif:
        return {"status": "success", "message": "Notification not found or not accessible"}
    notif.status = "read"
    await db.commit()
    return {"status": "success", "message": "Notification marked as read"}


@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Mark every unread notification for the current user's role as read."""
    await db.execute(
        update(Notification)
        .where(
            (
                (Notification.target_role == current_user.role.value)
                | (Notification.target_role == None)
            )
            & (Notification.status == "unread")
        )
        .values(status="read")
    )
    await db.commit()
    return {"status": "success", "message": "All notifications marked as read"}

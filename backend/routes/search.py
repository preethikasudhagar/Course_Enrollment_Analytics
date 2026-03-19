from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from database import get_db
from models.models import Course, User, UserRole

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
async def global_search(q: str, db: AsyncSession = Depends(get_db)):
    if not q or len(q) < 2:
        return {"courses": [], "students": [], "faculty": []}
        
    # Search courses
    course_query = await db.execute(
        select(Course).where(
            or_(
                Course.course_name.ilike(f"%{q}%"),
                Course.department.ilike(f"%{q}%"),
                Course.course_code.ilike(f"%{q}%")
            )
        )
    )
    courses = course_query.scalars().all()
    
    # Search users
    user_query = await db.execute(
        select(User).where(
            or_(
                User.name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%")
            )
        )
    )
    users = user_query.scalars().all()
    
    return {
        "courses": [{"id": c.id, "name": c.course_name, "type": "course", "department": c.department, "code": c.course_code} for c in courses],
        "students": [{"id": u.id, "name": u.name, "type": "student", "email": u.email} for u in users if u.role == UserRole.STUDENT],
        "faculty": [{"id": u.id, "name": u.name, "type": "faculty", "email": u.email} for u in users if u.role == UserRole.FACULTY]
    }

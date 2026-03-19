from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models.models import SeatExpansionLog, Course, UserRole
from utils.auth import check_admin

router = APIRouter(prefix="/seat-expansion-logs", tags=["seat-expansion"])

@router.get("/")
async def get_seat_expansion_logs(db: AsyncSession = Depends(get_db), admin=Depends(check_admin)):
    try:
        query = select(SeatExpansionLog, Course).join(Course, Course.id == SeatExpansionLog.course_id).order_by(SeatExpansionLog.timestamp.desc())
        result = await db.execute(query)
        rows = result.all()
        
        data = []
        for log, course in rows:
            data.append({
                "id": log.id,
                "course_name": course.course_name,
                "old_limit": log.old_limit,
                "new_limit": log.new_limit,
                "increment_by": log.increment_by,
                "timestamp": log.timestamp
            })
            
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

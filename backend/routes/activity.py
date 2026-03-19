from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models.models import SystemActivity
from utils.auth import check_admin

router = APIRouter(prefix="/activity", tags=["activity"])

@router.get("/")
async def get_system_activity(db: AsyncSession = Depends(get_db), admin=Depends(check_admin)):
    result = await db.execute(select(SystemActivity).order_by(SystemActivity.timestamp.desc()).limit(50))
    activities = result.scalars().all()
    
    return {"status": "success", "data": [{"id": a.id, "action": a.action, "timestamp": a.timestamp} for a in activities]}

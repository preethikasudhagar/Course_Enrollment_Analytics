from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from database import get_db
from models.models import SystemSetting
from utils.auth import check_admin

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    default_seat_increase: int
    auto_seat_expansion: bool
    enable_notifications: bool
    enable_email_alerts: bool
    max_seat_limit: int
    seat_expansion_threshold: int

@router.get("/")
async def get_settings(db: AsyncSession = Depends(get_db)): # We could lock this to admin but system might need defaults
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().first()
    if not settings:
        settings = SystemSetting()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return {
        "status": "success",
        "data": {
            "default_seat_increase": settings.default_seat_increase,
            "auto_seat_expansion": settings.auto_seat_expansion,
            "enable_notifications": settings.enable_notifications,
            "enable_email_alerts": settings.enable_email_alerts,
            "max_seat_limit": settings.max_seat_limit,
            "seat_expansion_threshold": settings.seat_expansion_threshold
        }
    }

@router.put("/")
async def update_settings(settings_data: SettingsUpdate, db: AsyncSession = Depends(get_db), admin=Depends(check_admin)):
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().first()
    
    if not settings:
        settings = SystemSetting(**settings_data.model_dump())
        db.add(settings)
    else:
        for key, value in settings_data.model_dump().items():
            setattr(settings, key, value)
    
    await db.commit()
    return {"status": "success", "message": "Settings updated successfully"}

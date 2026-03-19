from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models.models import Suggestion, Course, UserRole
from utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

# Demo data seed for suggestions if none exist
async def _seed_demo_suggestions(db: AsyncSession):
    res = await db.execute(select(Suggestion))
    if not res.scalars().first():
        s1 = Suggestion(message="Machine Learning demand increased by 40%. Consider increasing seat capacity.", status="pending")
        s2 = Suggestion(message="Cyber Security enrollment is low. Consider revising course content.", status="pending")
        db.add_all([s1, s2])
        await db.commit()

@router.get("/")
async def get_suggestions(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != UserRole.FACULTY:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await _seed_demo_suggestions(db)
        
    result = await db.execute(select(Suggestion).where(Suggestion.status == "pending"))
    suggestions = result.scalars().all()
    
    response = []
    for s in suggestions:
        course_name = "Global Priority"
        if s.course_id:
            c_res = await db.execute(select(Course).where(Course.id == s.course_id))
            course = c_res.scalars().first()
            if course: course_name = course.course_name
        
        response.append({
            "id": s.id,
            "message": s.message,
            "course_name": course_name,
            "timestamp": s.timestamp
        })
    return {"status": "success", "data": response}

@router.post("/{suggestion_id}/approve")
async def approve_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != UserRole.FACULTY:
        raise HTTPException(status_code=403)
    
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    sug = result.scalars().first()
    if not sug: raise HTTPException(status_code=404)
    
    sug.status = "approved"
    await db.commit()
    return {"status": "success", "message": "Suggestion approved"}

@router.post("/{suggestion_id}/dismiss")
async def dismiss_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != UserRole.FACULTY:
        raise HTTPException(status_code=403)
    
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    sug = result.scalars().first()
    if not sug: raise HTTPException(status_code=404)
    
    sug.status = "dismissed"
    await db.commit()
    return {"status": "success", "message": "Suggestion dismissed"}

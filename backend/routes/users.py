from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import os
import uuid
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from models.models import User, UserRole, Enrollment
from schemas.user import UserResponse
from utils.auth import check_admin, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/profile")
async def update_profile(
    phone: Optional[str] = Form(None),
    profile_photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        if phone is not None:
            current_user.phone = phone
        
        if profile_photo is not None:
            allowed_types = {"image/jpeg", "image/png", "image/webp"}
            if profile_photo.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid image type. Use JPG, PNG, or WEBP.")

            max_size = 2 * 1024 * 1024
            content = await profile_photo.read()
            if len(content) > max_size:
                raise HTTPException(status_code=400, detail="Profile photo must be 2MB or less.")

            file_ext = os.path.splitext(profile_photo.filename)[1]
            file_name = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join("uploads", "profile_photos", file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Store relative path for URL access
            current_user.profile_photo = f"/uploads/profile_photos/{file_name}"
        
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "status": "success",
            "data": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "phone": current_user.phone,
                "profile_photo": current_user.profile_photo,
                "department": current_user.department,
                "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_profile(current_user = Depends(get_current_user)):
    return {
        "status": "success",
        "data": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "profile_photo": current_user.profile_photo,
            "department": current_user.department,
            "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
        }
    }

@router.get("/")
async def get_users(db: AsyncSession = Depends(get_db), admin=Depends(check_admin)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    response = []
    for u in users:
        response.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value
        })
    return {"status": "success", "data": response}

@router.put("/{user_id}/role")
async def update_user_role(user_id: int, role: str, db: AsyncSession = Depends(get_db), admin=Depends(check_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simple check for role validity
    if role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    user.role = UserRole(role)
    await db.commit()
    return {"status": "success", "message": "User role updated successfully"}

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(check_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.execute(delete(Enrollment).where(Enrollment.student_id == user_id))
    await db.delete(user)
    await db.commit()
    return {"status": "success", "message": "User deleted successfully"}

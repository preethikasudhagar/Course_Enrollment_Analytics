from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import timedelta, datetime
import random
from database import get_db
from models.models import User, UserRole, OTPRecord
from schemas.user import UserCreate, UserResponse, Token
from pydantic import BaseModel, EmailStr
from utils.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

router = APIRouter(tags=["auth"])

async def seed_admin(db: AsyncSession):
    from sqlalchemy.future import select
    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    if not result.scalars().first():
        admin = User(
            name="System Admin",
            email="admin@example.com",
            password=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        await db.commit()
        print("Default admin created: admin@example.com / admin123")
    
    # Seed Faculty
    result = await db.execute(select(User).where(User.email == "faculty@example.com"))
    if not result.scalars().first():
        faculty = User(
            name="Main Faculty",
            email="faculty@example.com",
            password=get_password_hash("faculty123"),
            role=UserRole.FACULTY
        )
        db.add(faculty)
        await db.commit()
        print("Default faculty created: faculty@example.com / faculty123")

@router.post("/register")
@router.post("/auth/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        if user.role.value == UserRole.STUDENT.value and not user.department:
            raise HTTPException(status_code=400, detail="Department is required for student registration")

        result = await db.execute(select(User).where(User.email == user.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        new_user = User(
            name=user.name,
            email=user.email,
            password=get_password_hash(user.password),
            role=UserRole(user.role),
            department=user.department,
            year=user.year
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Notification for Admin
        from models.models import Notification
        admin_notif = Notification(
            message=f"New student registered: {new_user.name} ({new_user.email})",
            target_role="admin",
            timestamp=datetime.utcnow()
        )
        db.add(admin_notif)
        await db.commit()

        # Demo Enrollments for Students
        if new_user.role == UserRole.STUDENT:
            from models.models import Course, Enrollment
            demo_courses = [
                {"name": "Data Structures", "dept": "Computer Science"},
                {"name": "Web Development", "dept": "Information Technology"},
                {"name": "Database Systems", "dept": "Software Engineering"}
            ]
            
            for dc in demo_courses:
                # Check if course exists
                res = await db.execute(select(Course).where(Course.course_name == dc["name"]))
                course = res.scalars().first()
                if not course:
                    course = Course(course_name=dc["name"], department=dc["dept"], seat_limit=40)
                    db.add(course)
                    await db.commit()
                    await db.refresh(course)
                
                # Create enrollment
                enroll = Enrollment(student_id=new_user.id, course_id=course.id)
                db.add(enroll)
                try:
                    await db.commit()
                except:
                    await db.rollback() 
        
        # Map to schema response
        return {
            "status": "success",
            "data": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role.value,
                "department": new_user.department,
                "year": new_user.year
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        with open("error_log.txt", "a") as f:
            f.write(f"\n--- Error at {datetime.now()} ---\n")
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}, 
        expires_delta=access_token_expires
    )
    return {
        "status": "success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "department": user.department,
                "year": user.year
            }
        }
    }

@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    if not verify_password(req.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    current_user.password = get_password_hash(req.new_password)
    db.add(current_user)
    await db.commit()
    return {"message": "Password successfully updated."}

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()
    if not user:
        return {"message": "If that email is registered, an OTP has been sent."} # Prevent email enumeration
    
    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    expires = datetime.utcnow() + timedelta(minutes=10)
    
    # Remove old OTPs for this email
    await db.execute(delete(OTPRecord).where(OTPRecord.email == req.email))
    
    otp_record = OTPRecord(email=req.email, otp=otp_code, expires_at=expires)
    db.add(otp_record)
    await db.commit()
    
    # In a real app, send email/SMS here. For demo, we just print or return it if running locally for debugging.
    print(f"DEBUG: OTP for {req.email} is {otp_code}")
    
    return {"message": "If that email is registered, an OTP has been sent."}

@router.post("/verify-otp")
async def verify_otp(req: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OTPRecord).where(OTPRecord.email == req.email, OTPRecord.otp == req.otp))
    record = result.scalars().first()
    
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    return {"message": "OTP verified successfully"}

@router.post("/seed-institutional-data")
async def seed_institutional_data_endpoint(background_tasks: BackgroundTasks):
    async def run_seed():
        from seed_institutional_data import seed_data
        await seed_data()
    background_tasks.add_task(run_seed)
    return {"status": "accepted", "message": "Seeding started in background. Check backend logs for completion."}

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Verify OTP again
    result = await db.execute(select(OTPRecord).where(OTPRecord.email == req.email, OTPRecord.otp == req.otp))
    record = result.scalars().first()
    
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    user_res = await db.execute(select(User).where(User.email == req.email))
    user = user_res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password = get_password_hash(req.new_password)
    db.add(user)
    
    # Delete OTP
    await db.execute(delete(OTPRecord).where(OTPRecord.email == req.email))
    await db.commit()
    
    return {"message": "Password successfully reset."}

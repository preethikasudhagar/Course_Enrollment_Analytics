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

from pydantic import BaseModel, EmailStr

class LoginJSON(BaseModel):
    username: str
    password: str

@router.post("/login-json")
async def login_json(credentials: LoginJSON, db: AsyncSession = Depends(get_db)):
    # Standard DB check 
    try:
        from sqlalchemy import text
        import asyncio
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=8.0)
    except Exception as e:
        logger.error(f"Login-JSON DB check failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")

    try:
        result = await db.execute(select(User).where(User.email == credentials.username))
        user = result.scalars().first()
        
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            
        access_token = create_access_token(data={"sub": user.email, "role": user.role})
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login-JSON internal error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal login error")

@router.post("/login")
@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Simple check for database connectivity - Fail fast
    try:
        import asyncio
        from sqlalchemy import text
        # Test basic connection with timeout to prevent hangs
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=8.0)
    except asyncio.TimeoutError:
        logger.error("Login database check TIMED OUT (8s)")
        raise HTTPException(status_code=503, detail="Database is temporarily busy. Please try again.")
    except Exception as e:
        logger.error(f"Login database CRITICAL failure: {str(e)}")
        # If it's a cryptography missing error or similar, log it clearly
        if "cryptography" in str(e).lower():
            logger.critical("MISSING CRYPTOGRAPHY LIBRARY FOR MYSQL AUTH")
        raise HTTPException(status_code=500, detail="Internal connection error. Please contact administrator.")

    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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

@router.post("/debug-seed")
async def debug_seed():
    """Synchronous full wipe and seed to force exact enrollments for specific courses."""
    import random, traceback
    from datetime import datetime
    from sqlalchemy import text
    from database import AsyncSessionLocal
    from models.models import User, Course, Enrollment, Notification, Analytics, UserRole
    from utils.auth import get_password_hash
    try:
        async with AsyncSessionLocal() as db:
            # Full Wipe
            await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            for table in ["enrollments", "notifications", "analytics", "courses", "users"]:
                await db.execute(text(f"TRUNCATE TABLE {table};"))
            await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            await db.commit()
            
            # Users
            admin = User(name="Institutional Admin", email="admin@example.com", password=get_password_hash("admin123"), role=UserRole.ADMIN)
            faculty = User(name="Lead Faculty", email="faculty@example.com", password=get_password_hash("faculty123"), role=UserRole.FACULTY)
            db.add_all([admin, faculty])
            await db.commit()
            
            first_names = ["Rahul", "Priya", "Arjun", "Sneha", "Kavya", "Nikhil", "Ananya", "Rohit", "Divya", "Aditya"]
            last_names = ["Sharma", "Patel", "Mehta", "Reddy", "Iyer", "Verma", "Gupta", "Nair", "Menon", "Singh"]
            students = []
            for i in range(50):
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                student = User(name=f"{fname} {lname}", email=f"{fname.lower()}.{lname.lower()}{i}@university.edu", password=get_password_hash("student123"), role=UserRole.STUDENT)
                db.add(student)
                students.append(student)
            await db.commit()
            for s in students: await db.refresh(s)
            
            # Courses
            course_configs = [
                ("CS201", "Data Structures", "Computer Science", 45),
                ("CS220", "Web Development", "Information Technology", 50),
                ("CS210", "Database Systems", "Software Engineering", 40),
                ("CS305", "Machine Learning", "Artificial Intelligence", 35),
                ("CS330", "Cloud Computing", "Computer Science", 30),
                ("CS301", "Operating Systems", "Computer Science", 40),
                ("CS401", "Artificial Intelligence", "Artificial Intelligence", 30),
                ("CS320", "Computer Networks", "Information Technology", 35),
                ("CS350", "Cyber Security", "Information Technology", 25),
                ("CS360", "Data Analytics", "Data Science", 40),
                ("CS370", "Software Engineering", "Software Engineering", 45),
                ("CS450", "Deep Learning", "Artificial Intelligence", 20)
            ]
            courses = []
            for code, name, dept, limit in course_configs:
                course = Course(course_code=code, course_name=name, department=dept, seat_limit=limit)
                db.add(course)
                courses.append(course)
            await db.commit()
            for c in courses: await db.refresh(c)
            
            course_map = {c.course_name: c for c in courses}
            
            # Specific Enrollments target counts
            target_counts = {
                "Artificial Intelligence": 29,  # capacity 30
                "Data Analytics": 39,          # capacity 40
                "Software Engineering": 44,    # capacity 45
                "Machine Learning": 33,        # capacity 35
                "Web Development": 40          # generic mid-high
            }
            
            used_pairs = set()
            total_enrollments = 0
            
            for c_name, target in target_counts.items():
                if c_name not in course_map: continue
                c = course_map[c_name]
                enrolled = 0
                available_students = list(students)
                random.shuffle(available_students)
                for s in available_students:
                    if enrolled >= target: break
                    enrollment = Enrollment(student_id=s.id, course_id=c.id, enrollment_date=datetime(2024, random.randint(1, 4), random.randint(1, 28)))
                    db.add(enrollment)
                    used_pairs.add((s.id, c.id))
                    enrolled += 1
                    total_enrollments += 1
            
            # Fill remaining to make total ~100 or so. (already 185 from above, so skip random)
            await db.commit()
            
            # Analytics
            for c in courses:
                count = len([e for e in used_pairs if e[1] == c.id])
                score = (count / c.seat_limit) * 10
                db.add(Analytics(course_id=c.id, demand_score=score, trend_data=f"Growth index: {random.uniform(1.1, 1.5):.2f}"))
            await db.commit()
            
            return {"status": "ok", "message": f"Seeded with forced counts. Total enrollments: {total_enrollments}"}
    except Exception as e:
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}


async def seed_institutional_data_endpoint(background_tasks: BackgroundTasks):
    async def run_seed():
        import random
        import logging
        from datetime import datetime
        from sqlalchemy import text
        from database import AsyncSessionLocal, init_db
        from models.models import User, Course, Enrollment, Notification, Analytics, UserRole
        from utils.auth import get_password_hash
        logger = logging.getLogger("seeder")
        try:
            logger.info("Seeding: init_db...")
            await init_db()
            async with AsyncSessionLocal() as db:
                await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                for table in ["enrollments", "notifications", "analytics", "courses", "users"]:
                    await db.execute(text(f"TRUNCATE TABLE {table};"))
                await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                await db.commit()
                admin = User(name="Institutional Admin", email="admin@example.com", password=get_password_hash("admin123"), role=UserRole.ADMIN)
                faculty = User(name="Lead Faculty", email="faculty@example.com", password=get_password_hash("faculty123"), role=UserRole.FACULTY)
                db.add_all([admin, faculty])
                await db.commit()
                departments = ["Computer Science", "Information Technology", "Artificial Intelligence", "Data Science", "Electronics"]
                first_names = ["Rahul", "Priya", "Arjun", "Sneha", "Kavya", "Nikhil", "Ananya", "Rohit", "Divya", "Aditya"]
                last_names = ["Sharma", "Patel", "Mehta", "Reddy", "Iyer", "Verma", "Gupta", "Nair", "Menon", "Singh"]
                students = []
                for i in range(50):
                    fname = random.choice(first_names)
                    lname = random.choice(last_names)
                    email = f"{fname.lower()}.{lname.lower()}{i}@university.edu"
                    student = User(name=f"{fname} {lname}", email=email, password=get_password_hash("student123"), role=UserRole.STUDENT)
                    db.add(student)
                    students.append(student)
                await db.commit()
                for s in students: await db.refresh(s)
                course_configs = [
                    ("CS201", "Data Structures", "Computer Science", 45),
                    ("CS220", "Web Development", "Information Technology", 50),
                    ("CS210", "Database Systems", "Software Engineering", 40),
                    ("CS305", "Machine Learning", "Artificial Intelligence", 35),
                    ("CS330", "Cloud Computing", "Computer Science", 30),
                    ("CS301", "Operating Systems", "Computer Science", 40),
                    ("CS401", "Artificial Intelligence", "Artificial Intelligence", 30),
                    ("CS320", "Computer Networks", "Information Technology", 35),
                    ("CS350", "Cyber Security", "Information Technology", 25),
                    ("CS360", "Data Analytics", "Data Science", 40),
                    ("CS370", "Software Engineering", "Software Engineering", 45),
                    ("CS450", "Deep Learning", "Artificial Intelligence", 20)
                ]
                courses = []
                for code, name, dept, limit in course_configs:
                    course = Course(course_code=code, course_name=name, department=dept, seat_limit=limit)
                    db.add(course)
                    courses.append(course)
                await db.commit()
                for c in courses: await db.refresh(c)
                high_demand = ["Machine Learning", "Data Analytics", "Web Development"]
                medium_demand = ["Data Structures", "Database Systems", "Cloud Computing"]
                enrollments_count = 0
                used_pairs = set()
                while enrollments_count < 100:
                    s = random.choice(students)
                    c = random.choice(courses)
                    if (s.id, c.id) in used_pairs: continue
                    if c.course_name in high_demand: prob = 0.9
                    elif c.course_name in medium_demand: prob = 0.6
                    else: prob = 0.3
                    if random.random() < prob:
                        month = random.randint(1, 4)
                        day = random.randint(1, 28)
                        enrollment = Enrollment(student_id=s.id, course_id=c.id, enrollment_date=datetime(2024, month, day))
                        db.add(enrollment)
                        used_pairs.add((s.id, c.id))
                        enrollments_count += 1
                await db.commit()
                notif_samples = [
                    ("Machine Learning seats almost full.", "admin"),
                    ("New course 'Deep Learning' added to catalog.", "student"),
                    ("Cloud Computing enrollment increased by 20%.", "faculty"),
                ]
                for msg, role in notif_samples:
                    db.add(Notification(message=msg, role=role, status="unread"))
                for c in courses:
                    count = len([e for e in used_pairs if e[1] == c.id])
                    score = (count / c.seat_limit) * 10
                    db.add(Analytics(course_id=c.id, demand_score=score, trend_data=f"Growth index: {random.uniform(1.1, 1.5):.2f}"))
                await db.commit()
                logger.info(f"Seeding complete: 50 students, 12 courses, {enrollments_count} enrollments.")
        except Exception as e:
            logger.error(f"Seeding FAILED: {e}", exc_info=True)
    background_tasks.add_task(run_seed)
    return {"status": "accepted", "message": "Seeding started in background. Check Render logs for completion."}

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

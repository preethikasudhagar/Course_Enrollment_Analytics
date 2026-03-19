from fastapi import FastAPI
from fastapi import Depends
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy import select, or_
from routes import auth, courses, enrollments, analytics, notifications, users, search, settings, suggestions, activity
from database import init_db
from database import get_db, AsyncSessionLocal
from utils.auth import get_current_user, check_admin
from routes.enrollments import EnrollRequest, enroll_post
from schemas.course import CourseCreate
from routes.courses import create_course as create_course_handler
from routes.analytics import get_dashboard_summary
from models.models import Course

app = FastAPI(title="Course Enrollment Analytics System")

# Ensure uploads directory exists
if not os.path.exists("uploads/profile_photos"):
    os.makedirs("uploads/profile_photos", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configure CORS for deployment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()
    from routes.auth import seed_admin
    async with AsyncSessionLocal() as db:
        await seed_admin(db)
        await normalize_course_catalog(db)
        await seed_institutional_if_empty(db)

async def seed_institutional_if_empty(db):
    """Auto-seed the database with institutional data on startup if students are missing."""
    import random
    import logging
    from datetime import datetime
    from sqlalchemy import text, func
    from models.models import User, Course, Enrollment, Notification, Analytics, UserRole
    from utils.auth import get_password_hash
    logger = logging.getLogger("startup_seeder")
    try:
        # Check if students already exist
        result = await db.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.STUDENT)
        )
        student_count = result.scalar()
        if student_count >= 10:
            logger.info(f"Startup seeder: {student_count} students found, skipping seed.")
            return
        logger.info("Startup seeder: No students found, seeding institutional data...")
        first_names = ["Rahul", "Priya", "Arjun", "Sneha", "Kavya", "Nikhil", "Ananya", "Rohit", "Divya", "Aditya"]
        last_names = ["Sharma", "Patel", "Mehta", "Reddy", "Iyer", "Verma", "Gupta", "Nair", "Menon", "Singh"]
        students = []
        for i in range(50):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            email = f"{fname.lower()}.{lname.lower()}{i}@university.edu"
            # Check if user already exists
            existing = await db.execute(select(User).where(User.email == email))
            if existing.scalars().first():
                continue
            student = User(name=f"{fname} {lname}", email=email, password=get_password_hash("student123"), role=UserRole.STUDENT)
            db.add(student)
            students.append(student)
        await db.commit()
        for s in students:
            await db.refresh(s)
        # Seed courses
        from models.models import Course
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
            existing_c = await db.execute(select(Course).where(Course.course_code == code))
            if existing_c.scalars().first():
                continue
            course = Course(course_code=code, course_name=name, department=dept, seat_limit=limit)
            db.add(course)
            courses.append(course)
        await db.commit()
        for c in courses:
            await db.refresh(c)
        if students and courses:
            high_demand = ["Machine Learning", "Data Analytics", "Web Development"]
            medium_demand = ["Data Structures", "Database Systems", "Cloud Computing"]
            enrollments_count = 0
            used_pairs = set()
            while enrollments_count < 100:
                s = random.choice(students)
                c = random.choice(courses)
                if (s.id, c.id) in used_pairs:
                    continue
                if c.course_name in high_demand:
                    prob = 0.9
                elif c.course_name in medium_demand:
                    prob = 0.6
                else:
                    prob = 0.3
                if random.random() < prob:
                    enrollment = Enrollment(student_id=s.id, course_id=c.id, enrollment_date=datetime(2024, random.randint(1, 4), random.randint(1, 28)))
                    db.add(enrollment)
                    used_pairs.add((s.id, c.id))
                    enrollments_count += 1
            await db.commit()
        logger.info(f"Startup seeder: done. {len(students)} students, {len(courses)} courses seeded.")
    except Exception as e:
        logger.error(f"Startup seeder failed: {e}", exc_info=True)


REAL_COURSE_CATALOG = [
    ("CS201", "Data Structures", "Computer Science"),
    ("CS210", "Database Systems", "Computer Science"),
("CS301", "3D Modelling", "Computer Science and Engineering"),
    ("CS320", "Computer Networks", "Computer Science"),
    ("CS305", "Machine Learning", "Artificial Intelligence"),
    ("CS401", "Artificial Intelligence", "Artificial Intelligence"),
    ("CS330", "Cloud Computing", "Information Technology"),
    ("CS220", "Web Development", "Information Technology"),
    ("CS350", "Cyber Security", "Information Technology"),
    ("CS360", "Data Analytics", "Data Science"),
    ("CS370", "Software Engineering", "Software Engineering"),
    ("CS450", "Deep Learning", "Artificial Intelligence"),
]


async def normalize_course_catalog(db):
    # Replace synthetic/test course labels with real institutional names.
    res = await db.execute(
        select(Course).where(
            or_(
                Course.course_name.ilike("Seat Scenario%"),
                Course.course_name.ilike("Alias Course%"),
                Course.course_name.ilike("Scenario %"),
            )
        )
    )
    synthetic_courses = res.scalars().all()
    for idx, course in enumerate(synthetic_courses):
        code, name, dept = REAL_COURSE_CATALOG[idx % len(REAL_COURSE_CATALOG)]
        course.course_name = name
        course.course_code = code
        course.department = dept

    # For existing real courses with missing code, backfill deterministic course code.
    all_courses = (await db.execute(select(Course))).scalars().all()
    fallback_prefix = {
        "Computer Science": "CS",
        "Information Technology": "IT",
        "Artificial Intelligence": "AI",
        "Data Science": "DS",
        "Software Engineering": "SE",
    }
    for c in all_courses:
        if not c.course_code:
            prefix = fallback_prefix.get(c.department, "CRS")
            c.course_code = f"{prefix}{200 + c.id}"

    await db.commit()

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(enrollments.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(settings.router)
app.include_router(suggestions.router)
app.include_router(activity.router)

@app.post("/enroll")
async def enroll_alias(
    req: EnrollRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await enroll_post(req, db, current_user)


@app.post("/create-course")
async def create_course_alias(
    payload: CourseCreate,
    db=Depends(get_db),
    admin=Depends(check_admin)
):
    return await create_course_handler(payload, db, admin)


@app.get("/analytics")
async def analytics_alias(
    db=Depends(get_db),
    current_user=Depends(check_admin)
):
    return await get_dashboard_summary(db)


@app.get("/notifications")
async def notifications_alias(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    from routes.notifications import get_notifications
    return await get_notifications(db, current_user)


@app.get("/")
async def root():
    return {"message": "Course Enrollment Analytics API (MySQL) is running"}

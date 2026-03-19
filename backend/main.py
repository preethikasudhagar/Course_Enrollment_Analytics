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

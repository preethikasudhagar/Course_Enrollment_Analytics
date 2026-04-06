from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from sqlalchemy import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from routes import auth, courses, enrollments, analytics, notifications, users, search, settings, suggestions, activity, seat_expansion
from sqlalchemy.ext.asyncio import AsyncSession
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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"], 
    allow_origin_regex=r"https://.*\.up\.railway\.app|https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_cache_control_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/uploads"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    return response

import asyncio

@app.on_event("startup")
async def on_startup():
    logger.info("Application event: startup. Starting infrastructure initialization...")
    try:
        # Critical: Initialize DB schema
        await init_db()
        logger.info("Database schema initialized/migrated.")
        
        # Start seeding and heavy analytics in the background so we don't block Railway's health check
        async def background_initialization():
            try:
                from routes.auth import seed_admin
                async with AsyncSessionLocal() as db:
                    await seed_admin(db)
                    logger.info("Background: Admin seeding checked.")
                
                from routes.analytics import refresh_all_vitals
                logger.info("Background: Starting analytics precomputation...")
                await refresh_all_vitals()
                logger.info("Background: Analytics precomputed.")
            except Exception as bg_err:
                logger.error(f"Background initialization failed: {bg_err}")

        asyncio.create_task(background_initialization())
        logger.info("Startup sequence complete. Server is now healthy.")
                
    except Exception as e:
        logger.error(f"CRITICAL STARTUP FAILURE: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # We raise here because the container should fail if DB init is broken
        raise e

@app.on_event("shutdown")
async def on_shutdown():
    from database import close_db
    await close_db()

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
app.include_router(seat_expansion.router)

@app.post("/enroll")
async def enroll_alias(
    req: EnrollRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await enroll_post(req, background_tasks, db, current_user)


@app.post("/create-course")
async def create_course_alias(
    payload: CourseCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    admin=Depends(check_admin)
):
    return await create_course_handler(payload, background_tasks, db, admin)


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

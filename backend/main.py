from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
import asyncio
from datetime import datetime
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

# Configure CORS for deployment - MUST BE FIRST
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://course-analytics-frontend-production.up.railway.app"
    ], 
    allow_origin_regex=r"https://.*\.up\.railway\.app|https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"], # More permissive for debugging
)

# Ensure uploads directory exists
if not os.path.exists("uploads/profile_photos"):
    os.makedirs("uploads/profile_photos", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(), "deploy_id": "final_fix_v4"}

@app.middleware("http")
async def add_cache_control_header(request, call_next):
    # Skip for CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)
    response = await call_next(request)
    if request.url.path.startswith("/uploads"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    return response

@app.on_event("startup")
async def on_startup():
    logger.info("Application starting up... Phase: Global Initialization.")
    
    # Run infrastructure tasks in a safely wrapped background task
    async def init_infrastructure():
        logger.info("Infrastructure Task: Starting database initialization.")
        try:
            from database import init_db
            await init_db()
            logger.info("Infrastructure Task: Database schema verified.")
            
            from routes.auth import seed_admin
            async with AsyncSessionLocal() as db:
                await seed_admin(db)
                logger.info("Infrastructure Task: Admin seeding complete.")
            
            from routes.analytics import refresh_all_vitals
            logger.info("Infrastructure Task: Re-calculating analytics cache...")
            await refresh_all_vitals()
            logger.info("Infrastructure Task: Cache pre-warming complete.")
        except Exception as infra_err:
            logger.error(f"Infrastructure Task FAILED (Server remains online): {infra_err}")
            import traceback
            logger.error(traceback.format_exc())

    # We do NOT await this. We let it run in parallel to avoid blocking the port binding.
    asyncio.create_task(init_infrastructure())
    logger.info("Startup sequence handed off to background. Port binding should succeed immediately.")

@app.on_event("shutdown")
async def on_shutdown():
    from database import close_db
    await close_db()

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now()}

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
    return {"message": "Course Enrollment Analytics API (MySQL) is running", "status": "online", "version": "4.1"}

logger.info("Main script fully loaded. Application object ready for uvicorn.")

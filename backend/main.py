from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy import select
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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
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

@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
        from routes.auth import seed_admin
        async with AsyncSessionLocal() as db:
            await seed_admin(db)
            
            # Auto-import legacy data if the seed file is present
            import os
            base_dir = os.path.dirname(__file__)
            seed_path = os.path.join(base_dir, "seed_data.json")
            print(f"DEBUG: Checking for seed file at {seed_path}")
            print(f"DEBUG: Current dir contents: {os.listdir(base_dir)}")
            
            if os.path.exists(seed_path):
                from import_json import import_data
                await import_data(db)
                
                # Force-trim specific courses to exactly 29 enrollments
                from sqlalchemy import text
                target_ids = [307, 311, 315, 316, 318, 324]
                for cid in target_ids:
                    # Simple cleanup: Ensure seat_limit is 30 first
                    await db.execute(text("UPDATE courses SET seat_limit = 30 WHERE id = :cid"), {"cid": cid})
                    # Count existing enrollments
                    res = await db.execute(text("SELECT id FROM enrollments WHERE course_id = :cid ORDER BY id DESC"), {"cid": cid})
                    ids = [r[0] for r in res.fetchall()]
                    if len(ids) > 29:
                        to_delete = ids[: (len(ids) - 29)]
                        await db.execute(text("DELETE FROM enrollments WHERE id IN :ids"), {"ids": tuple(to_delete)})
                        print(f"DEBUG: Deleted {len(to_delete)} excess enrollments for course {cid}")
                await db.commit()
            else:
                print("DEBUG: Seed file not found.")
            
            from routes.analytics import refresh_all_vitals
            await refresh_all_vitals()
    except Exception as e:
        import traceback
        with open("startup_error.txt", "w") as f:
            f.write(f"Startup failed: {str(e)}\n")
            f.write(traceback.format_exc())
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

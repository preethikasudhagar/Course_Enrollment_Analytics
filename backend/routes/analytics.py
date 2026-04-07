from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text
from typing import List, Dict, Any
from datetime import datetime, timedelta
from database import get_db, AsyncSessionLocal
from models.models import Course, Enrollment, User, UserRole, Analytics, SeatExpansionLog
from utils.auth import check_admin, get_current_user
from utils.cache import analytics_cache

router = APIRouter(prefix="/analytics", tags=["analytics"])

async def refresh_all_vitals():
    """Aggressively precompute all vitals into memory cache."""
    async with AsyncSessionLocal() as db:
        await refresh_admin_vitals(db)
        await refresh_faculty_vitals_cache(db)
        await refresh_student_vitals(db)
    print(f"[{datetime.now()}] Aggressive precomputation complete.")

async def refresh_admin_vitals(db: AsyncSession):
    try:
        import asyncio
        from sqlalchemy import func
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        # 1. Base Metrics (Summary) - Crucial
        tc = await db.scalar(select(func.count(Course.id))) or 0
        ts = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.STUDENT)) or 0
        te = await db.scalar(select(func.count(Enrollment.id))) or 0
        tst = await db.scalar(select(func.sum(Course.seat_limit))) or 0
        au = await db.scalar(select(func.count(func.distinct(Enrollment.student_id)))) or 0
        
        top_res = await db.execute(select(Course.course_name, func.count(Enrollment.id)).join(Enrollment, Enrollment.course_id == Course.id).group_by(Course.id, Course.course_name).order_by(func.count(Enrollment.id).desc()).limit(1))
        tr_row = top_res.first()
        
        summary = {
            "total_courses": tc, 
            "total_students": ts, 
            "total_enrollments": te,
            "total_seats": tst, 
            "active_users": au, 
            "growth_rate": "+12.5%",
            "utilization": round((te / tst * 100), 1) if tst > 0 else 0,
            "top_course": tr_row[0] if tr_row else "N/A",
            "most_popular_course": tr_row[0] if tr_row else "N/A",
            "most_popular_course_enrollment_count": tr_row[1] if tr_row else 0
        }

        # 2. Charts & Lists (Resilient)
        trends = []
        try:
            tr = await db.execute(select(func.date_format(Enrollment.enrollment_date, '%b').label('m'), func.count(Enrollment.id)).where(Enrollment.enrollment_date >= six_months_ago).group_by('m').order_by(func.min(Enrollment.enrollment_date)))
            trends = [{"month": r[0], "enrollments": r[1] or 0} for r in tr.all()]
        except Exception as e:
            print(f"Chart Error (Trends): {e}")
            trends = [{"month": datetime.now().strftime('%b'), "enrollments": te}]

        top_courses_list = []
        try:
            pop = await db.execute(select(Course.course_name, func.count(Enrollment.id)).join(Enrollment, Enrollment.course_id == Course.id).group_by(Course.id, Course.course_name).order_by(func.count(Enrollment.id).desc()).limit(5))
            top_courses_list = [{"name": r[0], "students": r[1] or 0} for r in pop.all()]
        except Exception as e:
            print(f"Chart Error (Popularity): {e}")

        courses_list = []
        try:
            ci = await db.execute(select(Course.id, Course.course_code, Course.course_name, Course.department, Course.seat_limit, func.count(Enrollment.id)).outerjoin(Enrollment, Enrollment.course_id == Course.id).group_by(Course.id).order_by(Course.course_name).limit(20))
            courses_list = [{"id": r[0], "course_code": r[1], "course_name": r[2], "department": r[3], "seat_limit": r[4], "enrolled_students": r[5] or 0} for r in ci.all()]
        except Exception as e:
            print(f"List Error (Courses): {e}")

        dept_util = []
        try:
            du = await db.execute(select(Course.department).distinct())
            for r in du.all():
                dept_name = r[0]
                dept_students = await db.scalar(select(func.count(Enrollment.id)).join(Course, Course.id == Enrollment.course_id).where(Course.department == dept_name)) or 0
                dept_seats = await db.scalar(select(func.sum(Course.seat_limit)).where(Course.department == dept_name)) or 0
                util_pct = round((dept_students / dept_seats * 100), 1) if dept_seats > 0 else 0
                dept_util.append({"department": dept_name, "total_students": dept_students, "total_seats": dept_seats, "utilization_pct": util_pct})
        except Exception as e:
            print(f"List Error (Dept): {e}")

        heatmap = []
        try:
            hm = await db.execute(select(func.date_format(Enrollment.enrollment_date, '%b'), func.date_format(Enrollment.enrollment_date, '%W'), func.count(Enrollment.id)).group_by(func.date_format(Enrollment.enrollment_date, '%b'), func.date_format(Enrollment.enrollment_date, '%W')))
            heatmap = [{"month": r[0], "day": r[1], "count": r[2] or 0} for r in hm.all()]
        except Exception as e:
             print(f"Chart Error (Heatmap): {e}")

        expansion_logs = []
        try:
            sl = await db.execute(select(SeatExpansionLog, Course).join(Course, Course.id == SeatExpansionLog.course_id).order_by(SeatExpansionLog.timestamp.desc()).limit(15))
            expansion_logs = [{"id": log.id, "course_name": course.course_name, "old_limit": log.old_limit, "new_limit": log.new_limit, "increment_by": log.increment_by, "timestamp": log.timestamp} for log, course in sl.all()]
        except Exception as e:
            print(f"List Error (Logs): {e}")

        response_data = {
            "summary": summary,
            "courses": courses_list,
            "deptUtilization": dept_util,
            "heatmap": heatmap,
            "expansionLogs": expansion_logs,
            "charts": {
                "utilDetail": [
                    {"name": "Enrolled", "value": summary["total_enrollments"]},
                    {"name": "Remaining", "value": max(0, summary["total_seats"] - summary["total_enrollments"])}
                ],
                "deptEnroll": [{"name": d["department"], "enrollments": d["total_students"]} for d in dept_util],
                "topCourses": top_courses_list,
                "trends": trends
            }
        }
        analytics_cache.set_precomputed("admin_vitals", response_data)
        print("Admin Vitals precomputed successfully.")
    except Exception as e:
        import traceback
        print(f"Refresh Error (Admin):\n{traceback.format_exc()}")

async def refresh_faculty_vitals_cache(db: AsyncSession):
    try:
        import asyncio
        ts = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.STUDENT))
        tc = await db.scalar(select(func.count(Course.id)))
        te = await db.scalar(select(func.count(Enrollment.id)))
        tst = await db.scalar(select(func.sum(Course.seat_limit)))
        pop = await db.execute(select(Course.course_name, func.count(Enrollment.id)).join(Enrollment, Enrollment.course_id == Course.id).group_by(Course.id, Course.course_name).order_by(func.count(Enrollment.id).desc()).limit(1))
        ci = await db.execute(select(Course.id, Course.course_code, Course.course_name, Course.department, Course.seat_limit, func.count(Enrollment.id)).outerjoin(Enrollment, Enrollment.course_id == Course.id).group_by(Course.id).order_by(Course.course_name))
        ts = ts or 0
        tc = tc or 0
        te = te or 0
        tst = tst or 0
        
        pop_row = pop.first()
        course_data = ci.all()
        
        summary = {
            "total_students": ts or 0, "total_courses": tc or 0, "total_enrollments": te or 0,
            "top_course": pop_row[0] if pop_row else "N/A", "most_popular_course": pop_row[0] if pop_row else "N/A",
            "most_popular_course_enrollment_count": pop_row[1] if pop_row else 0,
            "utilization": round((te / tst) * 100, 1), "total_seats": tst
        }
        
        response_data = {
            "summary": summary,
            "performance": [
                {"label": "Courses Handled", "value": len(course_data), "icon": "book", "trend": "Active"},
                {"label": "Total Students", "value": sum(r[5] or 0 for r in course_data), "icon": "users", "trend": f"Avg {round(sum(r[5] or 0 for r in course_data)/(len(course_data) or 1))} / course"},
                {"label": "Average Demand", "value": f"{round(summary['utilization'])}%", "icon": "star", "trend": "Stable"},
                {"label": "Retention Rate", "value": "94%", "icon": "thumbs-up", "trend": "Excellent"}
            ],
            "enrollmentData": [{"name": r[2], "enrollments": r[5] or 0, "capacity": r[4]} for r in course_data],
            "courses": [{"id": r[0], "course_code": r[1], "course_name": r[2], "department": r[3], "seat_limit": r[4], "enrolled_students": r[5] or 0} for r in course_data]
        }
        analytics_cache.set_precomputed("faculty_vitals", response_data)
    except Exception as e:
        import traceback
        print(f"Refresh Error (Faculty):\n{traceback.format_exc()}")

async def refresh_student_vitals(db: AsyncSession):
    try:
        # 1. Get all courses (Ready-to-Render)
        courses_query = select(
            Course.id, Course.course_code, Course.course_name, Course.department, Course.seat_limit,
            func.count(Enrollment.id).label("enrolled")
        ).outerjoin(Enrollment, Enrollment.course_id == Course.id).group_by(Course.id).order_by(Course.created_at.desc())
        
        result = await db.execute(courses_query)
        course_data = result.all()
        courses = [{"id": r[0], "course_code": r[1], "course_name": r[2], "department": r[3], "seat_limit": r[4], "enrolled_students": r[5] or 0} for r in course_data]
        
        # 2. Get recommendations (Sample logic)
        recs = [
            {**c, "course_id": c["id"], "reason": "High demand in your department"} for c in courses[:3]
        ]
        
        response_data = {
            "courses": courses,
            "recommendations": recs
        }
        analytics_cache.set_precomputed("student_vitals", response_data)
    except Exception as e:
        print(f"Refresh Error (Student): {e}")


@router.get("/student-vitals")
async def get_student_vitals():
    data = analytics_cache.get_precomputed("student_vitals")
    if not data:
        async with AsyncSessionLocal() as db:
            await refresh_student_vitals(db)
        data = analytics_cache.get_precomputed("student_vitals")
    return data


async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    try:
        total_courses = await db.scalar(select(func.count(Course.id)))
        total_students = await db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.STUDENT)
        )
        total_enrollments = await db.scalar(select(func.count(Enrollment.id)))
        total_seats = await db.scalar(select(func.sum(Course.seat_limit)))

        active_users = await db.scalar(
            select(func.count(func.distinct(Enrollment.student_id)))
        )

        top_course_row = (
            await db.execute(
                select(
                    Course.course_name,
                    func.count(Enrollment.id).label("enrollment_count"),
                    Course.seat_limit
                )
                .join(Enrollment, Enrollment.course_id == Course.id)
                .group_by(Course.id, Course.course_name, Course.seat_limit)
                .order_by(func.count(Enrollment.id).desc())
                .limit(1)
            )
        ).first()

        most_popular_course = top_course_row[0] if top_course_row else "N/A"
        most_popular_course_enrollment_count = top_course_row[1] if top_course_row else 0
        most_popular_course_capacity = top_course_row[2] if top_course_row else 0

        return {
            "status": "success",
            "data": {
                "total_courses": total_courses or 0,
                "total_students": total_students or 0,
                "total_enrollments": total_enrollments or 0,
                "total_seats": total_seats or 0,
                "active_users": active_users or 0,
                "growth_rate": "+12.5%",
                "utilization": round((total_enrollments / total_seats * 100), 1) if total_seats else 0,
                "top_course": most_popular_course,
                "most_popular_course": most_popular_course,
                "most_popular_course_enrollment_count": most_popular_course_enrollment_count,
                "top_course_capacity": most_popular_course_capacity
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrollment-trends")
async def get_enrollment_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Real data: group enrollments by month for the last 6 months
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    query = select(
        func.date_format(Enrollment.enrollment_date, '%b').label('month'),
        func.count(Enrollment.id).label('count')
    ).where(
        Enrollment.enrollment_date >= six_months_ago
    ).group_by('month').order_by(func.min(Enrollment.enrollment_date))

    result = await db.execute(query)
    rows = result.all()

    if rows:
        data = [{"name": row[0], "enrollments": row[1]} for row in rows]
    else:
        # Fallback: show current month with total count
        total = await db.scalar(select(func.count(Enrollment.id))) or 0
        current_month = datetime.utcnow().strftime('%b')
        data = [{"name": current_month, "enrollments": total}]

    return {"status": "success", "data": data}


@router.get("/course-popularity")
async def get_course_popularity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Course.course_name, func.count(Enrollment.id))
        .join(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Course.id, Course.course_name)
        .order_by(func.count(Enrollment.id).desc())
        .limit(5)
    )
    popularity = result.all()

    return {
        "status": "success",
        "data": [{"course_name": p[0], "value": p[1]} for p in popularity]
    }


@router.get("/demand-prediction")
async def get_demand_prediction(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course))
    courses = result.scalars().all()

    prediction_data = []
    for c in courses:
        enrolled = c.enrolled_students or 0
        limit = c.seat_limit or 1
        utilization = round((enrolled / limit) * 100, 1)
        # Use utilization-based prediction instead of random
        growth = min(utilization * 0.4, 40.0)
        predicted_growth = "High" if growth > 25 else "Medium" if growth > 10 else "Low"
        prediction_data.append({
            "course_name": c.course_name,
            "current": enrolled,
            "value": int(enrolled * (1 + growth / 100)),
            "growth_pct": f"{growth}%",
            "demand": predicted_growth
        })
    return {"status": "success", "data": prediction_data}


@router.get("/enrollment-heatmap")
async def get_enrollment_heatmap(db: AsyncSession = Depends(get_db)):
    query = select(
        func.date_format(Enrollment.enrollment_date, '%b').label('month'),
        func.date_format(Enrollment.enrollment_date, '%W').label('day'),
        func.count(Enrollment.id)
    ).group_by('month', 'day')

    result = await db.execute(query)
    rows = result.all()
    return [{"month": row[0], "day": row[1], "count": row[2]} for row in rows]


@router.get("/smart-insights")
async def get_smart_insights(db: AsyncSession = Depends(get_db)):
    insights = []

    pop_query = select(Course.course_name).order_by(Course.enrolled_students.desc()).limit(1)
    pop_res = await db.execute(pop_query)
    pop_course = pop_res.scalar()
    if pop_course:
        insights.append({"type": "growth", "message": f"{pop_course} is the fastest growing course this semester.", "icon": "trending-up"})

    low_query = select(Course.course_name).order_by(Course.enrolled_students.asc()).limit(1)
    low_res = await db.execute(low_query)
    low_course = low_res.scalar()
    if low_course:
        insights.append({"type": "warning", "message": f"{low_course} enrollment is low this semester.", "icon": "alert-circle"})

    util_res = await db.execute(select(func.sum(Course.enrolled_students), func.sum(Course.seat_limit)))
    util_data = util_res.first()
    if util_data and util_data[1]:
        util_pct = round((util_data[0] / util_data[1]) * 100, 1)
        insights.append({"type": "info", "message": f"Seat utilization reached {util_pct}% across all courses.", "icon": "bar-chart"})

    return insights


@router.get("/faculty-stats")
async def get_faculty_stats(db: AsyncSession = Depends(get_db)):
    return {
        "status": "success",
        "data": [
            {"label": "Courses Handled", "value": 3, "icon": "book"},
            {"label": "Total Enrollments", "value": 120, "icon": "users"},
            {"label": "Average Demand", "value": "85%", "icon": "star"},
            {"label": "Retention Rate", "value": "94%", "icon": "thumbs-up"}
        ]
    }


@router.get("/department-utilization")
async def get_department_utilization(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    try:
        depts_query = select(Course.department).distinct()
        depts_res = await db.execute(depts_query)
        departments = [d[0] for d in depts_res.all()]

        utilization_data = []
        for dept in departments:
            # Fix department utilization count by using separate queries or correct grouping
            enroll_sum = await db.scalar(
                select(func.count(Enrollment.id))
                .join(Course, Course.id == Enrollment.course_id)
                .where(Course.department == dept)
            ) or 0
            seat_sum = await db.scalar(
                select(func.sum(Course.seat_limit))
                .where(Course.department == dept)
            ) or 0
            
            utilization = round((enroll_sum / seat_sum) * 100, 1) if seat_sum else 0
            utilization_data.append({
                "department": dept,
                "total_students": enroll_sum,
                "utilization_pct": utilization,
                "total_seats": seat_sum
            })

        return {"status": "success", "data": utilization_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_analytics(format: str = "csv", report_type: str = "general", db: AsyncSession = Depends(get_db)):
    try:
        if report_type == "department":
            depts_query = select(
                Course.department,
                func.count(Course.id).label("total_courses"),
                func.sum(Course.seat_limit).label("total_seats"),
                func.sum(Course.enrolled_students).label("total_enrolled")
            ).group_by(Course.department)

            result = await db.execute(depts_query)
            rows = result.all()

            report_data = []
            for row in rows:
                utilization = round((row[3] / row[2]) * 100, 1) if row[2] else 0
                report_data.append({
                    "Department": row[0],
                    "Total Courses": row[1],
                    "Total Seats": row[2],
                    "Total Enrolled": row[3],
                    "Utilization %": f"{utilization}%"
                })

            if format == "csv":
                import io, csv
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["Department", "Total Courses", "Total Seats", "Total Enrolled", "Utilization %"])
                writer.writeheader()
                writer.writerows(report_data)
                from fastapi.responses import Response
                return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=dept_report.csv"})

        result = await db.execute(select(Course))
        courses = result.scalars().all()
        return {"message": "Export completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    student_count_res = await db.execute(select(func.count(User.id)).where(User.role == UserRole.STUDENT))
    total_students = student_count_res.scalar()

    course_count_res = await db.execute(select(func.count(Course.id)))
    total_courses = course_count_res.scalar()

    enroll_count_res = await db.execute(select(func.count(Enrollment.id)))
    total_enrollments = enroll_count_res.scalar()

    popular_query = select(Enrollment.course_id, func.count(Enrollment.id).label("cnt"))\
        .group_by(Enrollment.course_id).order_by(func.count(Enrollment.id).desc()).limit(1)

    popular_result = await db.execute(popular_query)
    popular_data = popular_result.first()

    popular_course_name = "N/A"
    popular_course_count = 0
    if popular_data:
        course_res = await db.execute(select(Course).where(Course.id == popular_data.course_id))
        course = course_res.scalars().first()
        if course:
            popular_course_name = course.course_name
            popular_course_count = popular_data[1]

    util_res = await db.execute(select(func.sum(Course.seat_limit)))
    total_seats = util_res.scalar() or 1
    seat_utilization = round((total_enrollments / total_seats) * 100, 1)

    return {
        "status": "success",
        "data": {
            "total_students": total_students,
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
            "top_course": popular_course_name,
            "most_popular_course": popular_course_name,
            "most_popular_course_enrollment_count": popular_course_count,
            "utilization": seat_utilization,
            "total_seats": total_seats
        }
    }


@router.get("/course_enrollments")
async def get_course_enrollments_chart(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course))
    courses = result.scalars().all()

    chart_data = []
    for c in courses:
        count_res = await db.execute(select(func.count(Enrollment.id)).where(Enrollment.course_id == c.id))
        count = count_res.scalar()
        chart_data.append({
            "name": c.course_name,
            "enrollments": count,
            "capacity": c.seat_limit
        })
    return {"status": "success", "data": chart_data}


@router.get("/monthly_trends")
async def get_monthly_trends(db: AsyncSession = Depends(get_db)):
    query = select(
        func.date_format(Enrollment.enrollment_date, '%Y-%m').label('month'),
        func.count(Enrollment.id).label('count')
    ).group_by('month').order_by('month')

    result = await db.execute(query)
    rows = result.all()
    return {"status": "success", "data": [{"month": row[0], "enrollments": row[1]} for row in rows]}


@router.get("/department-stats")
async def get_dept_stats(db: AsyncSession = Depends(get_db)):
    query = select(Course.department, func.count(Course.id)).group_by(Course.department)
    result = await db.execute(query)
    rows = result.all()
    return {"status": "success", "data": [{"name": row[0], "value": row[1]} for row in rows]}


@router.get("/demand_forecast")
async def get_demand_forecast(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Course.course_name,
            Analytics.demand_score,
            Analytics.growth_rate,
            Analytics.forecast
        ).join(Analytics, Analytics.course_id == Course.id)
    )
    analytics_data = result.all()
    return {
        "status": "success",
        "data": [{
            "course_name": row[0],
            "demand_score": row[1],
            "growth_rate": row[2],
            "forecast": row[3]
        } for row in analytics_data]
    }


@router.get("/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(
            Course.id,
            Course.course_name,
            Course.department,
            Analytics.demand_score
        )
        .join(Analytics, Analytics.course_id == Course.id)
        .order_by(Analytics.demand_score.desc())
        .limit(3)
    )
    data = result.all()
    return {
        "status": "success",
        "data": [{
            "course_id": row[0],
            "course_name": row[1],
            "department": row[2],
            "reason": f"Top demand in {row[2]}",
            "popularity": row[3]
        } for row in data]
    }

@router.get("/admin-vitals")
async def get_admin_vitals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    precomputed = analytics_cache.get_precomputed("admin_vitals")
    if precomputed:
        return {"status": "success", "data": precomputed}
    
    # Fallback if cache is empty (unlikely but safe)
    await refresh_admin_vitals(db)
    return {"status": "success", "data": analytics_cache.get_precomputed("admin_vitals")}

@router.get("/faculty-vitals")
async def get_faculty_vitals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    precomputed = analytics_cache.get_precomputed("faculty_vitals")
    if precomputed:
        return {"status": "success", "data": precomputed}
    
    await refresh_faculty_vitals_cache(db)
    return {"status": "success", "data": analytics_cache.get_precomputed("faculty_vitals")}


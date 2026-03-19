from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
from database import get_db
from models.models import Course, Enrollment, User, UserRole, Analytics
from utils.auth import check_admin, get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard-stats")
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
                    func.count(Enrollment.id).label("enrollment_count")
                )
                .join(Enrollment, Enrollment.course_id == Course.id)
                .group_by(Course.id, Course.course_name)
                .order_by(func.count(Enrollment.id).desc())
                .limit(1)
            )
        ).first()

        most_popular_course = top_course_row[0] if top_course_row else "N/A"
        most_popular_course_enrollment_count = top_course_row[1] if top_course_row else 0

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
                "most_popular_course_enrollment_count": most_popular_course_enrollment_count
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
        select(Course.course_name, Course.enrolled_students)
        .order_by(Course.enrolled_students.desc())
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
            enroll_sum = await db.scalar(
                select(func.sum(Course.enrolled_students))
                .where(Course.department == dept)
            )
            seat_sum = await db.scalar(
                select(func.sum(Course.seat_limit))
                .where(Course.department == dept)
            )
            utilization = round((enroll_sum / seat_sum) * 100, 1) if seat_sum else 0

            utilization_data.append({
                "department": dept,
                "total_students": enroll_sum or 0,
                "utilization_pct": utilization,
                "total_seats": seat_sum or 0
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

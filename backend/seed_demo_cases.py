import asyncio
from datetime import datetime
from sqlalchemy import select, func
from database import AsyncSessionLocal, init_db
from models.models import User, Course, Enrollment, Notification, SystemActivity, UserRole
from utils.auth import get_password_hash


DEPARTMENTS = [
    "Computer Science and Engineering",
    "Information Technology",
    "Information Science and Engineering",
    "Artificial Intelligence and Data Science",
    "Electronics and Communication Engineering",
]


SCENARIO_COURSES = [
    # 2 seats left
    {
        "course_code": "IT401",
        "course_name": "Web Development",
        "department": "Information Technology",
        "seat_limit": 40,
        "target_enrolled": 39,
    },
    # Almost full
    {
        "course_code": "IT420",
        "course_name": "Cloud Computing",
        "department": "Information Technology",
        "seat_limit": 40,
        "target_enrolled": 36,
    },
    # Auto-expanded case
    {
        "course_code": "AI510",
        "course_name": "Machine Learning",
        "department": "Artificial Intelligence and Data Science",
        "seat_limit": 50,  # expanded from 40
        "target_enrolled": 45,
    },
    # Additional normal courses
    {
        "course_code": "CS301",
        "course_name": "Data Structures",
        "department": "Computer Science and Engineering",
        "seat_limit": 45,
        "target_enrolled": 25,
    },
    {
        "course_code": "EC330",
        "course_name": "Digital Signal Processing",
        "department": "Electronics and Communication Engineering",
        "seat_limit": 40,
        "target_enrolled": 18,
    },
]


async def get_or_create_user(db, name, email, password, role, department=None):
    res = await db.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        return existing

    user = User(
        name=name,
        email=email,
        password=get_password_hash(password),
        role=role,
        department=department,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_course(db, spec):
    # Prefer matching by course name first to prevent duplicate demo courses.
    by_name = await db.execute(
        select(Course).where(func.lower(Course.course_name) == spec["course_name"].lower())
    )
    course = by_name.scalars().first()
    if course:
        course.course_code = spec["course_code"]
        course.course_name = spec["course_name"]
        course.department = spec["department"]
        course.seat_limit = spec["seat_limit"]
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    res = await db.execute(select(Course).where(Course.course_code == spec["course_code"]))
    course = res.scalars().first()
    if not course:
        course = Course(
            course_code=spec["course_code"],
            course_name=spec["course_name"],
            department=spec["department"],
            seat_limit=spec["seat_limit"],
            enrolled_students=0,
            remaining_seats=spec["seat_limit"],
            auto_expand_enabled=True,
            max_seat_limit=200,
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
    else:
        course.course_name = spec["course_name"]
        course.department = spec["department"]
        course.seat_limit = spec["seat_limit"]
        db.add(course)
        await db.commit()
        await db.refresh(course)
    return course


async def create_students(db, count=70):
    students = []
    for i in range(1, count + 1):
        dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
        email = f"demo.student{i:02d}@university.edu"
        user = await get_or_create_user(
            db=db,
            name=f"Demo Student {i:02d}",
            email=email,
            password="student123",
            role=UserRole.STUDENT,
            department=dept,
        )
        students.append(user)
    return students


async def ensure_admin_faculty(db):
    await get_or_create_user(
        db=db,
        name="System Admin",
        email="admin@example.com",
        password="admin123",
        role=UserRole.ADMIN,
    )
    await get_or_create_user(
        db=db,
        name="Lead Faculty",
        email="faculty@example.com",
        password="faculty123",
        role=UserRole.FACULTY,
    )


async def upsert_enrollment(db, student_id, course_id):
    exists = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id
        )
    )
    if exists.scalars().first():
        return False

    db.add(Enrollment(student_id=student_id, course_id=course_id, enrollment_date=datetime.utcnow()))
    return True


async def seed_notifications(db):
    messages = [
        ("Seat limit reached for Machine Learning. Capacity was auto-increased from 40 to 50.", None),
        ("Web Development is almost full: only 2 seats left.", None),
        ("Cloud Computing is almost full and trending high demand.", None),
    ]
    for msg, target_role in messages:
        exists = await db.execute(
            select(Notification.id).where(Notification.message == msg).limit(1)
        )
        if not exists.first():
            db.add(Notification(message=msg, target_role=target_role, status="unread"))

    db.add(SystemActivity(action="Demo cases seeded: auto-increase, almost full, and 2 seats left scenarios."))
    await db.commit()


async def sync_course_counts(db, course):
    enrolled = await db.scalar(
        select(func.count(Enrollment.id)).where(Enrollment.course_id == course.id)
    ) or 0
    course.enrolled_students = enrolled
    course.remaining_seats = max(0, (course.seat_limit or 0) - enrolled)
    await db.commit()


async def seed_demo_cases():
    await init_db()
    async with AsyncSessionLocal() as db:
        await ensure_admin_faculty(db)
        students = await create_students(db, count=70)

        cursor = 0
        for spec in SCENARIO_COURSES:
            course = await get_or_create_course(db, spec)

            target = spec["target_enrolled"]
            needed_students = students[cursor: cursor + target]
            if len(needed_students) < target:
                needed_students = students[:target]
            cursor = (cursor + target) % len(students)

            for s in needed_students:
                await upsert_enrollment(db, s.id, course.id)

            await db.commit()
            await sync_course_counts(db, course)

        # Safety cleanup: keep only one course record per scenario course name.
        for spec in SCENARIO_COURSES:
            dup_rows = await db.execute(
                select(Course).where(func.lower(Course.course_name) == spec["course_name"].lower()).order_by(Course.id.asc())
            )
            matches = dup_rows.scalars().all()
            if len(matches) <= 1:
                continue
            keeper = next((c for c in matches if c.course_code == spec["course_code"]), matches[0])
            for c in matches:
                if c.id == keeper.id:
                    continue
                await db.execute(
                    Enrollment.__table__.delete().where(Enrollment.course_id == c.id)
                )
                await db.delete(c)
            await db.commit()
            await sync_course_counts(db, keeper)

        await seed_notifications(db)

        total_students = await db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.STUDENT)
        ) or 0
        total_courses = await db.scalar(select(func.count(Course.id))) or 0
        total_enrollments = await db.scalar(select(func.count(Enrollment.id))) or 0

        print("Demo data seeded successfully.")
        print(f"Students: {total_students}")
        print(f"Courses: {total_courses}")
        print(f"Enrollments: {total_enrollments}")
        print("Scenario courses:")
        for spec in SCENARIO_COURSES:
            print(f"- {spec['course_name']}: seat_limit={spec['seat_limit']}, target_enrolled={spec['target_enrolled']}")


if __name__ == "__main__":
    asyncio.run(seed_demo_cases())

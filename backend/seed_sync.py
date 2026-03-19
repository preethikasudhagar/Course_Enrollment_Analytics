"""
Institutional Data Seed Script — synchronous PyMySQL, no asyncio.
Run from backend/:  python seed_sync.py
"""
import pymysql, random, bcrypt
from datetime import datetime

def hp(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

conn = pymysql.connect(
    host="localhost", port=3306, user="root",
    password="Preethika_13#", database="course_analytics_db",
    charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor
)
cur = conn.cursor()

print("🔄 Clearing tables…")
cur.execute("SET FOREIGN_KEY_CHECKS=0")
for t in ["enrollments","notifications","analytics","courses","users"]:
    cur.execute(f"TRUNCATE TABLE {t}")
cur.execute("SET FOREIGN_KEY_CHECKS=1")
conn.commit()

# ── Staff ────────────────────────────────────────────────────────────────────
print("👥 Seeding admin & faculty…")
cur.execute("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
            ("Institutional Admin","admin@example.com",hp("admin123"),"admin"))
cur.execute("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
            ("Lead Faculty","faculty@example.com",hp("faculty123"),"faculty"))
conn.commit()

# ── 50 Students ───────────────────────────────────────────────────────────────
print("🎓 Seeding 50 students…")
fnames = ["Rahul","Priya","Arjun","Sneha","Kavya","Nikhil","Ananya","Rohit","Divya","Aditya"]
lnames = ["Sharma","Patel","Mehta","Reddy","Iyer","Verma","Gupta","Nair","Menon","Singh"]
student_ids = []
for i in range(50):
    fn = random.choice(fnames); ln = random.choice(lnames)
    email = f"{fn.lower()}.{ln.lower()}{i}@university.edu"
    cur.execute("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,'student')",
                (f"{fn} {ln}", email, hp("student123")))
    student_ids.append(cur.lastrowid)
conn.commit()
print(f"  → {len(student_ids)} students inserted")

# ── 12 Courses ────────────────────────────────────────────────────────────────
print("📚 Seeding 12 courses…")
course_cfg = [
    ("CS201", "Data Structures",        "Computer Science",        45),
    ("CS220", "Web Development",        "Information Technology",  50),
    ("CS210", "Database Systems",       "Software Engineering",    40),
    ("CS305", "Machine Learning",       "Artificial Intelligence", 35),
    ("CS330", "Cloud Computing",        "Computer Science",        30),
    ("CS301", "Operating Systems",      "Computer Science",        40),
    ("CS401", "Artificial Intelligence","Artificial Intelligence", 30),
    ("CS320", "Computer Networks",      "Information Technology",  35),
    ("CS350", "Cyber Security",         "Information Technology",  25),
    ("CS360", "Data Analytics",         "Data Science",            40),
    ("CS370", "Software Engineering",   "Software Engineering",    45),
    ("CS450", "Deep Learning",          "Artificial Intelligence", 20),
]
course_ids = []
for code, name, dept, limit in course_cfg:
    cur.execute("INSERT INTO courses (course_code,course_name,department,seat_limit) VALUES (%s,%s,%s,%s)",
                (code, name, dept, limit))
    course_ids.append(cur.lastrowid)
conn.commit()
print(f"  → {len(course_ids)} courses inserted")

# ── 100+ Enrollments ─────────────────────────────────────────────────────────
print("📋 Seeding ~120 enrollments (Jan–May 2024)…")
# High demand: DS, Web Dev, ML, Data Analytics
high_demand = {course_ids[0], course_ids[1], course_ids[3], course_ids[9]}
medium_demand = {course_ids[2], course_ids[4], course_ids[10]}

used, count = set(), 0
for _ in range(8000):
    if count >= 120:
        break
    sid = random.choice(student_ids)
    cid = random.choice(course_ids)
    if (sid, cid) in used:
        continue
    
    # Probability logic
    prob = 0.90 if cid in high_demand else (0.65 if cid in medium_demand else 0.40)
    if random.random() <= prob:
        # Spread dates for heatmap (Jan to May)
        month = random.choice([1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5]) 
        day   = random.randint(1, 28)
        cur.execute(
            "INSERT INTO enrollments (student_id,course_id,enrollment_date) VALUES (%s,%s,%s)",
            (sid, cid, datetime(2024, month, day))
        )
        used.add((sid, cid))
        count += 1
conn.commit()
print(f"  → {count} enrollments inserted")

# ── Update course counts ─────────────────────────────────────────────────────
for cid in course_ids:
    cur.execute("SELECT COUNT(*) as cnt FROM enrollments WHERE course_id=%s", (cid,))
    cnt = cur.fetchone()["cnt"]
    cur.execute("UPDATE courses SET enrolled_students=%s WHERE id=%s", (cnt, cid))
conn.commit()

# ── Waitlist ──────────────────────────────────────────────────────────────────
print("⏳ Seeding waitlist…")
for _ in range(5):
    sid = random.choice(student_ids)
    cid = random.choice(course_ids)
    cur.execute("INSERT INTO waitlist (student_id,course_id,position,created_at) VALUES (%s,%s,%s,%s)",
                (sid, cid, random.randint(1, 5), datetime.utcnow()))
conn.commit()

# ── Notifications ─────────────────────────────────────────────────────────────
print("🔔 Seeding professional notifications…")
notifs = [
    ("Machine Learning demand increased by 35% this semester. Review capacity.", "admin"),
    ("Web Development enrollment expected to grow next semester. Staff accordingly.", "faculty"),
    ("Cloud Computing course is reaching seat capacity soon.", "admin"),
    ("Total enrollments grew by 22% compared to last month.", "admin"),
    ("Seats for your course was full. Capacity increased and you were enrolled.", "student"),
]
for msg, role in notifs:
    cur.execute(
        "INSERT INTO notifications (message,target_role,status,timestamp) VALUES (%s,%s,'unread',%s)",
        (msg, role, datetime.utcnow())
    )
conn.commit()

# ── System Activity ──────────────────────────────────────────────────────────
print("📜 Seeding activity timeline…")
activities = [
    "Student Rahul enrolled in Machine Learning",
    "Admin increased seat limit for Data Analytics",
    "Admin added new course 'Deep Learning'",
    "Faculty updated course description for Algorithms",
    "System auto-expanded Web Development capacity to 60 seats"
]
for act in activities:
    cur.execute("INSERT INTO system_activities (action,timestamp) VALUES (%s,%s)",
                (act, datetime.utcnow()))
conn.commit()

# ── Analytics rows ────────────────────────────────────────────────────────────
print("📊 Seeding advanced analytics data…")
for cid in course_ids:
    cur.execute("SELECT enrolled_students, seat_limit FROM courses WHERE id=%s", (cid,))
    row = cur.fetchone()
    cnt  = row["enrolled_students"]
    seat = row["seat_limit"]
    
    score = int((cnt / seat) * 100) if seat else 0
    growth = f"{random.uniform(1.05,1.55):.2f}x"
    forecast = f"Enrollment expected to {'increase' if cnt > 10 else 'stabilize'} next term"
    
    cur.execute(
        "INSERT INTO analytics (course_id,demand_score,growth_rate,forecast) VALUES (%s,%s,%s,%s)",
        (cid, score, growth, forecast)
    )
conn.commit()

cur.close(); conn.close()
print("\n✅ Institutional-level data synthesis complete!")
print("   Admin    → admin@example.com    / admin123")
print("   Faculty  → faculty@example.com  / faculty123")
print("   Student  → (any)@university.edu / student123")

"""
Patches the live MySQL database to match the SQLAlchemy models.
Run once from backend/:  python patch_schema.py
"""
import pymysql

conn = pymysql.connect(
    host="localhost", port=3306, user="root",
    password="Preethika_13#", database="course_analytics_db",
    charset="utf8mb4"
)
cur = conn.cursor()

patches = [
    # Notifications: add role column
    ("notifications", "role",   "ALTER TABLE notifications ADD COLUMN role VARCHAR(50) NULL"),
    # Notifications: add status column
    ("notifications", "status", "ALTER TABLE notifications ADD COLUMN status VARCHAR(20) DEFAULT 'unread'"),
]

for tbl, col, sql in patches:
    try:
        cur.execute(sql)
        print(f"  ✅ {tbl}.{col} added")
    except pymysql.err.OperationalError as e:
        if "Duplicate column" in str(e):
            print(f"  ⏭  {tbl}.{col} already exists")
        else:
            print(f"  ❌ {tbl}.{col}: {e}")

# Create analytics table
cur.execute("""
CREATE TABLE IF NOT EXISTS analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    demand_score INT DEFAULT 0,
    growth_rate VARCHAR(50) DEFAULT '0%%',
    forecast VARCHAR(100) NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
)
""")
print("  ✅ analytics table ready")

conn.commit()
cur.close()
conn.close()
print("\n✅ Schema patch complete")

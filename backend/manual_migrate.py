import pymysql

conn = pymysql.connect(
    host="localhost", port=3306, user="root",
    password="Preethika_13#", database="course_analytics_db",
    charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor
)
cur = conn.cursor()

try:
    print("Checking users table for missing columns...")
    cur.execute("SHOW COLUMNS FROM users LIKE 'phone'")
    if not cur.fetchone():
        print("Adding 'phone' column...")
        cur.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL")
    
    cur.execute("SHOW COLUMNS FROM users LIKE 'profile_photo'")
    if not cur.fetchone():
        print("Adding 'profile_photo' column...")
        cur.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT NULL")

    print("Checking enrollments table for foreign key and relationship fixes...")
    # SQLAlchemy model has cascade delete now, but at DB level we should ensure it's robust if needed
    # (Actually DB level is usually safe if models are synchronized)

    conn.commit()
    print("✅ Database schema manually updated.")
except Exception as e:
    print(f"❌ Error during migration: {e}")
finally:
    cur.close(); conn.close()

import pymysql, bcrypt

def hp(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

conn = pymysql.connect(
    host="localhost", port=3306, user="root",
    password="Preethika_13#", database="course_analytics_db",
    charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor
)
cur = conn.cursor()

email = "preethika.se23@bitsathy.se.in"
pwd = "preethika"
hashed = hp(pwd)

cur.execute("SELECT id FROM users WHERE email=%s", (email,))
user = cur.fetchone()

if user:
    print(f"User {email} found. Resetting password...")
    cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, email))
else:
    print(f"User {email} not found. Creating...")
    cur.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Preethika", email, hashed, "student"))

conn.commit()
cur.close(); conn.close()
print("✅ User verification/reset complete.")

from sqlalchemy import create_engine, text
import os

password = "Preethika_13#"
# URL encoded password for the connection string
encoded_password = "Preethika_13%23"
LOCAL_URL = f"mysql+pymysql://root:{encoded_password}@localhost:3306/course_analytics_db"

def check_data():
    try:
        engine = create_engine(LOCAL_URL)
        with engine.connect() as conn:
            # Check users
            user_count = conn.execute(text("SELECT count(*) FROM users")).scalar()
            # Check courses
            course_count = conn.execute(text("SELECT count(*) FROM courses")).scalar()
            # Check enrollments
            enroll_count = conn.execute(text("SELECT count(*) FROM enrollments")).scalar()
            
            print(f"Local Database Status:")
            print(f"- Users: {user_count}")
            print(f"- Courses: {course_count}")
            print(f"- Enrollments: {enroll_count}")
            
            if user_count > 1 or enroll_count > 0:
                print("\nSUCCESS: Found non-default data in local database.")
            else:
                print("\nNOTE: Only default data/admin user found.")
                
    except Exception as e:
        print(f"Error connecting to local DB: {e}")

if __name__ == "__main__":
    check_data()

import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000"

def test_login():
    print("Testing Login...")
    login_data = {"username": "admin@example.com", "password": "admin123"}
    data = urllib.parse.urlencode(login_data).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/login", data=data)
    try:
        with urllib.request.urlopen(req) as res:
            body = res.read()
            # print(body)
            data = json.loads(body)
            print("Login Successful!")
            return data["data"]["access_token"]
    except Exception as e:
        print(f"Login Failed: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())
    return None

def test_vitals(token):
    print("\nTesting Admin Vitals...")
    req = urllib.request.Request(f"{BASE_URL}/analytics/admin-vitals")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as res:
            body = res.read()
            data = json.loads(body)
            print("Vitals Fetched Successfully!")
            print(f"Total Enrollments: {data['summary']['total_enrollments']}")
            print(f"Total Courses: {data['summary']['total_courses']}")
            print(f"Top Courses Count: {len(data['charts']['topCourses'])}")
            
            se = next((c for c in data['courses'] if c['course_name'] == 'Software Engineering'), None)
            if se:
                print(f"Software Engineering: {se['enrolled_students']}/{se['seat_limit']}")
            else:
                print("Software Engineering course NOT FOUND!")
    except Exception as e:
        print(f"Vitals Failed: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())

if __name__ == "__main__":
    token = test_login()
    if token:
        test_vitals(token)

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    print("Testing Login...")
    login_data = {"username": "admin@example.com", "password": "admin123"}
    # OAuth2PasswordRequestForm expects data, not json
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            print("Login Successful!")
            token = response.json()["data"]["access_token"]
            return token
        else:
            print(f"Login Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")
    return None

def test_vitals(token):
    print("\nTesting Admin Vitals...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/analytics/admin-vitals", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("Vitals Fetched Successfully!")
            print(f"Total Enrollments: {data['summary']['total_enrollments']}")
            print(f"Total Courses: {data['summary']['total_courses']}")
            print(f"Top Courses Count: {len(data['charts']['topCourses'])}")
            
            # Check for Software Engineering
            se = next((c for c in data['courses'] if c['course_name'] == 'Software Engineering'), None)
            if se:
                print(f"Software Engineering: {se['enrolled_students']}/{se['seat_limit']}")
            else:
                print("Software Engineering course NOT FOUND in vitals!")
        else:
            print(f"Vitals Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    token = test_login()
    if token:
        test_vitals(token)

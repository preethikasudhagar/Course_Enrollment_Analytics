import requests
import json

def test_registration():
    url = "http://localhost:8000/auth/register"
    payload = {
        "name": "Debug User",
        "email": "debug@example.com",
        "password": "password123",
        "role": "student"
    }
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_registration()

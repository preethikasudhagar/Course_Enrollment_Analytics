from main import app
from fastapi.testclient import TestClient
import json

client = TestClient(app)

try:
    print("Testing /openapi.json...")
    response = client.get("/openapi.json")
    if response.status_code == 200:
        print("SUCCESS: /openapi.json is valid.")
    else:
        print(f"FAILED: /openapi.json returned {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"CRASH: {str(e)}")
    import traceback
    traceback.print_exc()

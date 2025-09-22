import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# ------------------------------
# 1️⃣ Test home endpoint
# ------------------------------
print("Testing / endpoint...")
resp = requests.get(f"{BASE_URL}/")
print("Status Code:", resp.status_code)
print("Response:", resp.json())
print("-" * 50)

# ------------------------------
# 2️⃣ Test chat endpoint
# ------------------------------
print("Testing /chat endpoint...")

test_messages = [
    "I have a fever",
    "I have a headache",
    "I feel body pain and rash",
    "What should I do if I have dengue?",
    "How to prevent malaria?"
]

for idx, msg in enumerate(test_messages, 1):
    data = {"user_id": f"test_user_{idx}", "message": msg}
    resp = requests.post(f"{BASE_URL}/chat", json=data)
    print(f"Message: {msg}")
    try:
        print("Response:", resp.json()['response'])
    except Exception as e:
        print("Error:", e)
    print("-" * 50)

# ------------------------------
# 3️⃣ Test stats endpoint
# ------------------------------
print("Testing /stats endpoint...")
resp = requests.get(f"{BASE_URL}/stats")
print("Status Code:", resp.status_code)
print("Response:", json.dumps(resp.json(), indent=2))
print("-" * 50)

import requests

response = requests.post(
    "http://127.0.0.1:8000/v1/llm/agent/query",
    json={
        "user_id": "test",
        "session_id": "s1",
        "question": "안녕하세요"
    }
)
print(response.status_code)
print(response.json())
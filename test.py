import sys
import requests

QUERY_URL = "http://127.0.0.1:8001/v1/llm/agent/query"
FEEDBACK_URL = "http://127.0.0.1:8001/v1/llm/agent/feedback"
USER_ID = "test"
SESSION_ID = "s1"

print("=== LLM 서버 테스트 (종료: Ctrl+C 또는 'q') ===\n")

while True:
    try:
        question = input("질문: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n종료합니다.")
        sys.exit(0)

    if question.lower() in ("q", "quit", "exit"):
        print("종료합니다.")
        sys.exit(0)

    if not question:
        continue

    try:
        response = requests.post(QUERY_URL, json={"user_id": USER_ID, "session_id": SESSION_ID, "question": question})
        data = response.json()
        print(f"\n답변: {data.get('final_answer', data)}\n")
    except Exception as e:
        print(f"\n오류: {e}\n")
        continue

    try:
        fb = input("피드백 (y=좋음 / n=나쁨 / 엔터=건너뜀): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n종료합니다.")
        sys.exit(0)

    if fb in ("y", "n"):
        try:
            fb_resp = requests.post(FEEDBACK_URL, json={"user_id": USER_ID, "session_id": SESSION_ID, "is_good": fb == "y"})
            if fb_resp.status_code == 200:
                print("피드백 저장 완료\n")
            else:
                print(f"피드백 저장 실패 ({fb_resp.status_code}): {fb_resp.text}\n")
        except Exception as e:
            print(f"피드백 오류: {e}\n")
    else:
        print()

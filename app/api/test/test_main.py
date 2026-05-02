# api/test/test_main.py
# LLM 서버의 주요 기능을 테스트하는 모듈입니다. 헬스체크와 텍스트 생성 기능이 정상적으로 작동하는지 확인합니다.

from fastapi import FastAPI
from app.api.test.test_routers import llm

app = FastAPI()

app.include_router(llm.router)

@app.get("/health")
async def health():
    return {"status": "llm server ok"}
# api/test/test_routers/llm.py
# LLM 서버의 라우터를 정의하는 모듈입니다. 헬스체크와 텍스트 생성 엔드포인트를 포함합니다.

from fastapi import APIRouter
from pydantic import BaseModel
from google import genai
from app.core.config import settings

router = APIRouter(prefix="/llm", tags=["LLM"])

client = genai.Client(api_key=settings.GEMINI_API_KEY)


class ChatRequest(BaseModel):
    prompt: str


@router.post("/chat")
async def llm_chat(request: ChatRequest):
    # 🔥 지금은 그냥 테스트용 응답
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite", contents={request.prompt}
    )

    return {"reply": f"LLM Response to : {response.text}"}

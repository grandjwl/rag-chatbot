# llmServer/app/api/routes/health_router.py
# 헬스 체크 라우터를 정의하는 모듈입니다. 서버의 상태

from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    """
    서버의 상태를 확인하는 엔드포인트입니다.
    """
    return {"status": "건강합니다."} 

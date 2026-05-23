# app/core/types.py
# 서비스·프로바이더 계층에서 공통으로 사용하는 도메인 타입

from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

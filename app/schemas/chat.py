# llmServer/app/schemas/chat.py

from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    response: str
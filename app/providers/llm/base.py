# llmServer/app/provider/llm/base.py

from abc import ABC, abstractmethod
from typing import List
from app.schemas.chat import ChatMessage


class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: List[ChatMessage],
    ) -> str:
        pass
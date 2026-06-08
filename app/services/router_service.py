# llmServer/app/services/router_service.py

import logging

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RouterService:

    DATA_KEYWORDS = [
        "재고", "품목", "제품", "상품", "부품",
        "수량", "매출", "매입", "판매", "구매",
        "많은", "적은", "최대", "최소", "평균",
        "합계", "얼마", "보여줘", "조회", "현황", "통계",
    ]

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def route(self, question: str, conversation_history: list = None) -> str:
        if any(kw in question for kw in self.DATA_KEYWORDS):
            return "INVENTORY"

        prompt = self._build_prompt(question, conversation_history or [])

        try:
            raw = await self.llm_service.generate_router(prompt)
            raw = raw.strip().upper()
            if "INVENTORY" in raw:
                return "INVENTORY"
            return "CHIT_CHAT"

        except Exception:
            logger.warning("LLM router failed, fallback to INVENTORY")
            return "INVENTORY"

    def _build_prompt(self, question: str, history: list) -> str:
        history_section = ""
        if history:
            lines = [f"Q: {h['question']}\nA: {h['answer']}" for h in history]
            history_section = "[최근 대화 기록]\n" + "\n\n".join(lines) + "\n\n"

        return f"""{history_section}[현재 질문]
{question}

INVENTORY 또는 CHIT_CHAT 중 하나만 출력하세요. 다른 말은 절대 붙이지 마세요."""
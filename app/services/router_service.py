# llmServer/app/services/router_service.py

import logging

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RouterService:
    """
    ============================================================
    [Domain Role]
    질문의 Intent 분류 서비스.

    1차: Rule-based 키워드 매칭
    2차: LLM fallback

    Graph에서 "분기 노드" 역할을 수행한다.

    ============================================================
    [Graph Input State Fields]
    - refined_question: str
    - structured_memory: Optional[dict]  (현재는 직접 사용하지 않음)
    - work_context: Optional[str]        (직전 대화 맥락)

    ============================================================
    [Graph Output State Fields]
    - intent: str

    가능한 값:
        - "INVENTORY"
        - "TECH_SALES"
        - "CHIT_CHAT"

    ============================================================
    [Routing Policy]

    1️⃣ Rule-based 우선
        - DATA_KEYWORDS → INVENTORY
        - TECH_SALES_KEYWORDS → TECH_SALES

    2️⃣ LLM fallback
        - generate_router(prompt)
        - 출력값에 INVENTORY / TECH 포함 여부 검사
        - 그 외 → CHIT_CHAT

    3️⃣ 예외 발생 시
        - LLM 오류 → 기본값 INVENTORY

    ============================================================
    [Failure Strategy]

    - Router는 error_type 설정하지 않음.
    - 실패해도 fallback 존재 → Hard Fail 없음.
    - Graph 상에서 retry 대상 아님.

    ============================================================
    [Graph 위치]

    memory_node
        ↓
    refine_node
        ↓
    router_node  ← 분기점
        ↓
    conditional edge:
        INVENTORY  → sql_gen
        TECH_SALES → answer (or tech flow)
        CHIT_CHAT  → answer
    ============================================================
    """

    DATA_KEYWORDS = [
        "재고", "품목", "제품", "상품", "부품",
        "수량", "매출", "매입", "판매", "구매",
        "많은", "적은", "최대", "최소", "평균",
        "합계", "얼마", "보여줘", "조회", "현황", "통계",
    ]

    TECH_SALES_KEYWORDS = [
        "스펙", "사양", "대체품", "호환",
        "납기", "리드타임", "EOL", "단종",
        "전압", "전류", "패키지",
    ]

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def route(self, question: str, work_context: str = "") -> str:
        """
        [Input]
        - question (refined_question 기준)
        - work_context (선택)

        [Output]
        - intent: str
        """

        # 디버깅용
        # print("ROUTER INPUT:", question)

        # 1️⃣ Rule 기반
        if any(kw in question for kw in self.DATA_KEYWORDS):
            # 디버깅용
            # print("ROUTER RULE MATCHED: DATA_KEYWORDS")
            return "INVENTORY"

        if any(kw in question for kw in self.TECH_SALES_KEYWORDS):
            # 디버깅용
            # print("ROUTER RULE MATCHED: TECH_SALES_KEYWORDS")
            return "TECH_SALES"

        # 2️⃣ LLM fallback
        prompt = self._build_prompt(question, work_context)

        try:
            raw = await self.llm_service.generate_router(prompt)
            # 디버깅용
            # print("DEBUG RAW:", raw)

            raw = raw.strip().upper()

            if "INVENTORY" in raw:
                return "INVENTORY"
            elif "TECH" in raw:
                return "TECH_SALES"
            return "CHIT_CHAT"

        except Exception:
            logger.warning("LLM router failed, fallback to INVENTORY")
            return "INVENTORY"

    def _build_prompt(self, question: str, ctx: str) -> str:
        ctx_section = f"[직전 업무 대화 맥락]\n{ctx}\n\n" if ctx else ""

        return f"""
        {ctx_section}
        질문: {question}

        반드시 아래 세 단어 중 하나만 출력하세요.
        다른 설명은 절대 붙이지 마세요.

        INVENTORY
        TECH_SALES
        CHIT_CHAT
        """
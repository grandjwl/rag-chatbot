# llmServer/app/services/memory_service.py

import re
import logging
from typing import Dict, Optional, List
from app.infra.database.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)


class MemoryService:
    """
    ============================================================
    [Domain Role]
    대화 기반 Context Resolution + Conversation Persistence 서비스.

    역할은 두 가지 블록으로 나뉨:

    1️⃣ Context Resolver
        - 최근 대화 조회
        - Follow-up 질문 재조립
        - Structured memory 추출
        - Pronoun resolution

    2️⃣ Conversation Persistence
        - 최종 질문/응답/SQL 저장

    Refine과 다름.
    → 이 서비스는 "대화 상태 관리" 책임을 가진다.

    ============================================================
    [Graph Input State Fields - Context 단계]
    - user_id: str
    - question: str

    ============================================================
    [Graph Output State Fields - Context 단계]
    - refined_question: str
    - structured_memory: Dict

    ============================================================
    [Graph Input State Fields - Save_conversation 단계]
    - user_id
    - session_id
    - question
    - refined_question
    - final_answer
    - sql_query
    - execution_time_ms
    - refine_corrections

    ============================================================
    [Failure Policy]
    - Context 단계는 Soft-fail (원 질문 유지)
    - Persist 단계는 DB 예외 발생 시 상위에서 처리
    ============================================================
    """

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository
        
        
    # ==================================================
    # 1️⃣ Context Resolver 영역
    # ==================================================
    
    async def load_recent(self, user_id: str, limit: int = 6):
        rows = await self.conversation_repository.get_recent(
            user_id=user_id,
            limit=limit,
        )
        return list(reversed(rows))  # 오래된 → 최신

    async def inject_context(self, user_id: str, question: str):
        """
        [Input]
        - user_id
        - question

        [Processing]
        1. 최근 대화 조회
        2. follow-up 재조립
        3. structured memory 추출
        4. pronoun resolution 적용

        [Return]
        - refined_question
        - structured_memory
        """

        recent = await self.load_recent(user_id)

        rebuilt_q = self._rebuild_followup(question, recent)

        structured_memory = self._extract_structured_memory(recent)

        # 🔥 대명사 해석 통합 (기존 test 코드에서 분리했던 부분)
        final_q = self._apply_pronoun_resolution(rebuilt_q, structured_memory)

        return final_q, structured_memory

    # --------------------------------------------------
    # follow-up 재조립
    # --------------------------------------------------
    def _rebuild_followup(self, question: str, recent: List[Dict]) -> str:

        if not recent:
            return question

        q = question.strip()

        # 짧은 질문만 follow-up 처리
        if len(q.replace(" ", "")) > 12:
            return q

        base_q = self._find_base_question(recent, q)
        if not base_q:
            return q

        # 🔥 연도 치환
        year_match = re.search(r"(\d{2,4})년", q)
        if year_match:
            new_year = year_match.group(1)

            if len(new_year) == 2:
                new_year = f"20{new_year}"

            rebuilt = re.sub(r"\d{2,4}년", f"{new_year}년", base_q)

            logger.info(f"[연도치환] {q} → {rebuilt}")
            return rebuilt

        # 🔥 분기 치환
        qtr_match = re.search(r"([1-4])분기", q)
        if qtr_match:
            qtr = qtr_match.group(1)

            if "분기" in base_q:
                rebuilt = re.sub(r"[1-4]분기", f"{qtr}분기", base_q)
            else:
                rebuilt = base_q + f" ({qtr}분기 기준)"

            logger.info(f"[분기치환] {q} → {rebuilt}")
            return rebuilt

        return q

    # --------------------------------------------------
    # 기준 질문 선택 로직
    # --------------------------------------------------
    def _find_base_question(self, recent: List[Dict], question: str):

        if re.search(r"\d{2,4}년", question):
            for m in reversed(recent):
                if re.search(r"\d{2,4}년", m["question"]):
                    return m["question"]

        if re.search(r"[1-4]분기", question):
            for m in reversed(recent):
                if "분기" in m["question"]:
                    return m["question"]

        return recent[-1]["question"] if recent else ""

    # --------------------------------------------------
    # 🔥 Pronoun Resolution (신규 통합)
    # --------------------------------------------------
    def _apply_pronoun_resolution(self, question: str, memory: Dict) -> str:
        """
        structured_memory 기반 대명사 해석.
        테스트 파일에 있던 로직을 통합.
        """

        if not memory:
            return question

        q = question

        PRONOUN_MAP = {
              "이 제품": "last_product",
              "해당 제품": "last_product",
              "그 제품": "last_product",
              "이 고객사": "last_vendor",
              "해당 고객사": "last_vendor",
              "이 제조사": "last_manufacturer",
              "해당 제조사": "last_manufacturer",
          }

        for pronoun, key in PRONOUN_MAP.items():
            if pronoun in q and memory.get(key):
                q = q.replace(pronoun, f"'{memory[key]}'")

        if "같은 기간" in q and memory.get("last_year"):
            q += f" ({memory['last_year']}년 기준)"

        return q

    # --------------------------------------------------
    # structured memory 추출
    # --------------------------------------------------
    def _extract_structured_memory(self, recent: List[Dict]) -> Dict:

        memory = {}

        for m in reversed(recent):

            text_blob = ""

            if m.get("response_data"):
                text_blob = str(m["response_data"])

            # 🔥 제품 코드 추출
            pn_matches = re.findall(r"\b[A-Z0-9][A-Z0-9\-#\.+]{4,}\b", text_blob)
            if pn_matches and "last_product" not in memory:
                memory["last_product"] = pn_matches[-1]

            # 🔥 최근 연도 저장
            year_match = re.search(r"\d{4}", m["question"])
            if year_match and "last_year" not in memory:
                memory["last_year"] = year_match.group(0)

        return memory
      
    # ==================================================
    # 2️⃣ Conversation Persistence 영역
    # ==================================================

    async def save_conversation(
        self,
        user_id: str,
        session_id: str,
        question: str,
        refined_question: str,
        response_data: Dict,
        final_sql: Optional[str],
        refine_corrections: Dict,
        execution_time_ms: int,
    ):
        """
        Graph 마지막 persist 노드에서 호출.

        retry 중간에는 호출하지 않음.
        final_status 기반으로 호출 여부 결정 가능.
        """

        await self.conversation_repository.save(
            user_id=user_id,
            session_id=session_id,
            question=question,
            refined_question=refined_question,
            response_data=response_data,
            final_sql=final_sql,
            entity_corrections=refine_corrections,
            execution_time_ms=execution_time_ms,
        )

# llmServer/app/services/answer_service.py

import logging
from typing import Dict
from app.services.llm_service import LLMService


logger = logging.getLogger(__name__)


class AnswerService:
    """
    ============================================================
    [Domain Role]
    최종 자연어 응답 생성 서비스 (Presentation Layer)

    역할:
        - CHIT_CHAT 분기 처리
        - DB 에러 메시지 사용자 친화 변환
        - 빈 결과 안내
        - DB 결과 기반 자연어 생성

    ============================================================
    🔥 Graph에서 관리할 영역

    이 서비스는:
        ❌ retry 판단하지 않음
        ❌ error_history 수정하지 않음
        ❌ retry_count 변경하지 않음
        ❌ state를 직접 mutate하지 않음

    Graph는:
        - result_anomalies 발생 시 재시도 여부 결정
        - 최종 성공/실패 상태 확정
        - persist 호출 여부 결정

    ============================================================
    [Input State Fields]

    - intent: str
    - question: str
    - refined_question: str
    - rows: List
    - db_result: str
    - explain_meta: dict
    - result_anomalies: List[str]

    ============================================================
    [Output]

    {
        "final_answer": str
    }

    ============================================================
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def generate(self, state: Dict) -> Dict:

        intent = state.get("intent")
        question = state.get("refined_question") or state.get("question", "")

        # --------------------------------------------------
        # 1️⃣ CHIT_CHAT 분기
        # --------------------------------------------------
        if intent == "CHIT_CHAT":
            return {
                "final_answer": await self.llm.generate_answer_chitchat(question)
            }

        # --------------------------------------------------
        # 2️⃣ DB 에러 처리
        # --------------------------------------------------
        db_res = state.get("db_result", "")
        if isinstance(db_res, str) and "Error" in db_res:
            return {
                "final_answer": f"❌ 데이터 조회 중 문제가 발생했습니다.\n\n{db_res}"
            }

        # --------------------------------------------------
        # 3️⃣ 빈 데이터 처리
        # --------------------------------------------------
        rows = state.get("rows", [])
        if not rows:
            return {
                "final_answer": "🔍 조회된 데이터가 없습니다. 질문의 조건을 확인해 주세요."
            }

        # --------------------------------------------------
        # 4️⃣ 결과 이상 경고 표시 (Retry 안 할 경우 대비)
        # --------------------------------------------------
        anomalies = state.get("result_anomalies", [])
        anomaly_notice = ""

        if anomalies:
            anomaly_notice = (
                "\n\n⚠ 데이터 이상 감지:\n- "
                + "\n- ".join(anomalies)
            )

        # --------------------------------------------------
        # 5️⃣ FACT 데이터 조립 (Hallucination 방지)
        # --------------------------------------------------
        rows_formatted = "\n".join(
            [str(dict(r)) for r in rows[:20]]
        )

        meta = state.get("explain_meta", {})

        meta_str = (
            f"대상 테이블: {', '.join(meta.get('tables_used', []))}\n"
            f"수행된 집계: {', '.join(meta.get('aggregations', []))}\n"
            f"전체 결과 행 수: {meta.get('row_count', 0)}"
        )

        final_prompt = (
            f"### 사용자 질문\n{question}\n\n"
            f"### DB 조회 데이터 (FACT)\n{rows_formatted}\n\n"
            f"### 데이터 정보\n{meta_str}"
        )

        # --------------------------------------------------
        # 6️⃣ LLM 호출
        # --------------------------------------------------
        try:
            response = await self.llm.generate_answer(final_prompt)

            return {
                "final_answer": response + anomaly_notice
            }

        except Exception as e:
            logger.error(f"Answer generation failed: {repr(e)}")

            return {
                "final_answer": "죄송합니다. 답변 생성 중 기술적인 오류가 발생했습니다."
            }
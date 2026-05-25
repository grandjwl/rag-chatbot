# llmServer/app/services/sql_generate_service.py

import re
import logging
from typing import Dict, Any, Optional

from app.services.llm_service import LLMService
from app.services.retry_strategy_service import RetryStrategyService
from app.services.rag_service import RAGService
from app.core.metadata_bundle import MetadataBundle

logger = logging.getLogger(__name__)


class SQLGenerateService:
    """자연어 질문 → PostgreSQL SELECT 쿼리 생성. retry 여부 판단은 Graph 레벨에서 수행한다."""

    def __init__(
        self,
        llm_service: LLMService,
        retry_service: RetryStrategyService,
        rag_service: RAGService,
        metadata_bundle: MetadataBundle,
    ):
        self.llm_service = llm_service
        self.retry_service = retry_service
        self.rag_service = rag_service
        self.metadata_bundle = metadata_bundle

    # ============================================================
    # 메인 실행
    # ============================================================
    async def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:

        question: str = state["refined_question"]
        retry_count = state.get("retry_count", 0)
        error_history = state.get("error_history", [])

        last_error: Optional[str] = (
            error_history[-1] if error_history else None
        )

        # ------------------------------------------------------------
        # 1️⃣ Retry 전략 분석
        # ------------------------------------------------------------
        retry_section = ""
        if last_error:
            retry_info = self.retry_service.analyze(last_error)

            if retry_info and retry_info.get("hint"):
                retry_section = f"""
                [이전 SQL 실행 실패]

                에러:
                {last_error}

                아래 전략을 반드시 반영하여 SQL을 수정하시오.
                같은 실수를 반복하지 말 것.

                수정 지침:
                {retry_info['hint']}
                """

        # ------------------------------------------------------------
        # 2️⃣ RAG 컨텍스트 구성 (병렬화)
        # ------------------------------------------------------------
        stored_embedding = state.get("question_embedding")
        reuse_embedding = stored_embedding if (stored_embedding is not None and question == state.get("question")) else None
        rag_section = await self.rag_service.build(question=question, question_embedding=reuse_embedding)

        # ------------------------------------------------------------
        # 3️⃣ 스키마 + 데이터 기간
        # ------------------------------------------------------------
        schema_ctx = self.metadata_bundle.schema_context
        min_date = self.metadata_bundle.data_stats.get("min_date")
        max_date = self.metadata_bundle.data_stats.get("max_date")

        # ------------------------------------------------------------
        # 4️⃣ 프롬프트 구성
        # ------------------------------------------------------------
        user_prompt = self._build_user_prompt(
            question=question,
            schema=schema_ctx,
            min_date=min_date,
            max_date=max_date,
            error_history=error_history,
            retry_section=retry_section,
            rag_section=rag_section,
        )

        # ------------------------------------------------------------
        # 5️⃣ LLM 호출
        # ------------------------------------------------------------
        try:
            raw_sql = await self.llm_service.generate_sql(user_prompt, premium=(retry_count >= 2))
        except Exception as e:
            logger.exception("LLM SQL 생성 실패")
            return {
                "sql_query": "",
                "error_type": "LLM_SQL_ERROR",
            }

        # ------------------------------------------------------------
        # 6️⃣ SQL 정리
        # ------------------------------------------------------------
        sql = self._clean_sql(raw_sql)

        # ------------------------------------------------------------
        # 7️⃣ 최소 안전 검증
        # ------------------------------------------------------------
        if not self._is_valid_select(sql):
            logger.warning("⚠️ 유효하지 않은 SQL 반환")
            return {
                "sql_query": "",
                "error_type": "invalid_sql_generated",
            }

        logger.info(f"\n📌 생성된 SQL:\n{sql}")

        return {
            "sql_query": sql,
            "error_type": None,
        }

    # ============================================================
    # Prompt Builder
    # ============================================================
    def _build_user_prompt(
        self,
        question: str,
        schema: str,
        min_date: Optional[str],
        max_date: Optional[str],
        error_history,
        retry_section: str,
        rag_section: str,
    ) -> str:

        return f"""
        [스키마 정보]
        {schema}

        [데이터 유효 기간]
        {min_date} ~ {max_date}

        [이전 에러 기록]
        {error_history}

        {retry_section}

        {rag_section}

        [사용자 질문]
        {question}

        반드시 실행 가능한 PostgreSQL SELECT 문만 생성하라.
        INSERT, UPDATE, DELETE, DROP, ALTER 금지.
        설명 금지.
        마크다운 금지.
        SQL 한 개만 출력하라.
        """

    # ============================================================
    # SQL 클린업
    # ============================================================
    def _clean_sql(self, raw: str) -> str:

        if not raw:
            return ""

        # ANSI escape 제거
        raw = re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", raw)

        # 코드블럭 추출
        match = re.search(
            r"```(?:sql)?\s*(.*?)\s*```",
            raw,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            sql = match.group(1).strip()
        else:
            sql = raw.strip()

        # 세미콜론 이후 제거
        sql = sql.split(";")[0].strip()

        return sql

    # ============================================================
    # 최소 SELECT 유효성 검증
    # ============================================================
    def _is_valid_select(self, sql: str) -> bool:

        if not sql:
            return False

        sql_lower = sql.lower().strip()

        # SELECT 또는 WITH(CTE) 시작 확인
        if not sql_lower.startswith("select") and not sql_lower.startswith("with"):
            return False

        # 위험 쿼리 차단
        forbidden = ["insert ", "update ", "delete ", "drop ", "alter "]
        if any(word in sql_lower for word in forbidden):
            return False

        return True
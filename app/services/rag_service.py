# llmServer/app/services/rag_service.py

import asyncio
import logging
from app.services.retrieval.engine import RetrievalEngine
from app.services.retrieval.strategies import (
    BiztermStrategy,
    TableSchemaStrategy,
)

logger = logging.getLogger(__name__)


class RAGService:
    """SQL 생성 보조 컨텍스트(few-shot, 비즈니스 용어, 테이블 스키마)를 병렬로 조회해 반환한다."""

    def __init__(self, retrieval_engine: RetrievalEngine):
        self.engine = retrieval_engine

    async def build(self, question: str) -> str:

        tasks = []

        # 1️⃣ Few-shot
        tasks.append(self.engine.retrieve_fewshot(question, n=1))

        # 2️⃣ Bizterm
        tasks.append(
            self.engine.retrieve(BiztermStrategy(), question)
        )

        # 3️⃣ Table_Schema
        tasks.append(
            self.engine.retrieve(TableSchemaStrategy(), question)
        )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []

        for idx, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning(f"RAG 전략 {idx} 실패: {r}")
                processed.append("")
            elif isinstance(r, str):
                processed.append(r)
            else:
                processed.append("")

        fewshot, bizterm, table_schema = processed

        section = ""

        if fewshot:
            section += f"\n[유사 질문-SQL 예시]\n{fewshot}"
        if bizterm:
            section += f"\n[비즈니스 용어 정의]\n{bizterm}"
        if table_schema:
            section += f"\n[관련 테이블 스키마]\n{table_schema}"

        return section.strip()
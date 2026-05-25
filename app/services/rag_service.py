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

    async def build(self, question: str, question_embedding=None) -> str:

        # refine에서 이미 embed한 벡터를 재사용할 수 있으면 재사용 (질문 미변경 시)
        query_embedding = question_embedding if question_embedding is not None else await self.engine.embed_query(question)

        results = await asyncio.gather(
            self.engine.retrieve_fewshot(question, n=1, query_embedding=query_embedding),
            self.engine.retrieve(BiztermStrategy(), question, query_embedding=query_embedding),
            self.engine.retrieve(TableSchemaStrategy(), question, query_embedding=query_embedding),
            return_exceptions=True,
        )
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
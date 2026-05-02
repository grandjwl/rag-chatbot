# llmServer/app/services/rag_service.py

import asyncio
import logging
from app.services.retrieval.engine import RetrievalEngine
from app.services.retrieval.strategies import (
    # SynonymStrategy,
    BiztermStrategy,
    TableSchemaStrategy,
    # ErrorStrategy,
    # KeywordStrategy,
)

logger = logging.getLogger(__name__)


class RAGService:
    """
    ============================================================
    [Domain Role]
    SQL 생성 보조 컨텍스트 생성 서비스.

    - Few-shot 예시
    - 동의어 정보
    - 비즈니스 용어 정의
    - 관련 테이블 스키마
    - 에러 해결 힌트
    - 질문 의도 힌트

    이 서비스는:
    - SQL을 생성하지 않음
    - retry를 수행하지 않음
    - state를 수정하지 않음
    - 실패 시 빈 문자열 반환 (Soft-Fail)

    ============================================================
    [Input]
    - question: str
    - synonym_hint: str
    - last_error: str

    ============================================================
    [Output]
    - str (프롬프트 삽입용 RAG 텍스트 블록)

    ============================================================
    [Failure Policy]
    - 개별 전략 실패 → 로그 기록 후 빈 문자열 처리
    - 전체 실패 → 빈 문자열 반환
    ============================================================
    """

    def __init__(self, retrieval_engine: RetrievalEngine):
        self.engine = retrieval_engine

    async def build(
        self,
        question: str,
        synonym_hint: str = "",
        last_error: str = "",
    ) -> str:

        tasks = []

        # 1️⃣ Few-shot
        tasks.append(self.engine.retrieve_fewshot(question))

        # 2️⃣ Synonym -> 이건 여기 노드 아님. 전처리할 때 사용할것임.
        # if synonym_hint:
        #     tasks.append(asyncio.sleep(0, result=synonym_hint))
        # else:
        #     tasks.append(
        #         self.engine.retrieve(SynonymStrategy(), question)
        #     )

        # 3️⃣ Bizterm
        tasks.append(
            self.engine.retrieve(BiztermStrategy(), question)
        )

        # 4️⃣ Table_Schema
        tasks.append(
            self.engine.retrieve(TableSchemaStrategy(), question)
        )

        # 1차 준협꺼
        # 5️⃣ Error-based retrieval
        # if last_error:
        #     tasks.append(
        #         self.engine.retrieve(ErrorStrategy(), last_error)
        #     )
        # else:
        #     tasks.append(asyncio.sleep(0, result=""))

        # 6️⃣ Keyword
        # tasks.append(
        #     self.engine.retrieve(KeywordStrategy(), question)
        # )

        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # 디버깅용
        # print("RAG 전략 결과:", results)
        processed = []

        for idx, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning(f"RAG 전략 {idx} 실패: {r}")
                processed.append("")
            elif isinstance(r, str):
                processed.append(r)
            else:
                processed.append("")

        (
            fewshot,
            # synonym,
            bizterm,
            table_schema,
            # error,
            # keyword,
        ) = processed

        section = ""

        if fewshot:
            section += f"\n[유사 질문-SQL 예시]\n{fewshot}"
        # if synonym:
        #     section += f"\n[동의어 정보]\n{synonym}"
        if bizterm:
            section += f"\n[비즈니스 용어 정의]\n{bizterm}"
        if table_schema:
            section += f"\n[관련 테이블 스키마]\n{table_schema}"
        # if error:
        #     section += f"\n[에러 해결 힌트]\n{error}"
        # if keyword:
        #     section += f"\n[질문 의도 힌트]\n{keyword}"

        return section.strip()
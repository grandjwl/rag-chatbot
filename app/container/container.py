# app/container.py

from app.prompts.registry import PromptRegistry
from app.providers.registry import ProviderRegistry
from app.infra.vector.vector_repository import VectorRepository
from app.infra.database.rdb_repository import RDBRepository
from app.infra.database.conversation_repository import ConversationRepository

from app.services.refine_service import RefineService
from app.services.router_service import RouterService
from app.services.llm_service import LLMService
from app.services.rerank_service import RerankService
from app.services.rag_service import RAGService
from app.services.memory_service import MemoryService
from app.services.retrieval.engine import RetrievalEngine
from app.services.retrieval.bm25 import BM25Index
from app.services.sql_generate_service import SQLGenerateService
from app.services.retry_strategy_service import RetryStrategyService
from app.services.execute_db_service import ExecuteDBService
from app.services.result_validation_service import ResultValidationService
from app.services.answer_service import AnswerService
from app.services.retry_decision_service import RetryDecisionService

from app.core.config import settings
from app.core.metadata_bundle import MetadataBundle


class ServiceContainer:

    def __init__(
        self,
        *,
        prompt_registry: PromptRegistry,
        provider_registry: ProviderRegistry,
        vector_repository: VectorRepository,
        rdb_repository: RDBRepository,
        conversation_repository: ConversationRepository,
        metadata_bundle: MetadataBundle,
    ):
        # 🔹 Provider 기반 객체 생성
        _reranker_provider = provider_registry.get_reranker(settings.COHERE_MODEL)
        self.conversation_repository = conversation_repository
      
        # 🔹 Application Services
        self.llm_service = LLMService(
            llm_registry=provider_registry,
            prompt_registry=prompt_registry,
        )

        self.rerank_service = RerankService(reranker=_reranker_provider)

        self.router_service = RouterService(llm_service=self.llm_service)

        self.retry_strategy_service = RetryStrategyService(metadata_bundle.column_map)

        self.rag_service = RAGService(retrieval_engine=self.retrival_engine)

        self.memory_service = MemoryService(
            conversation_repository=conversation_repository
        )

        self.refine_service = RefineService(
            refine_cache=metadata_bundle.refine_cache,
            vector_repository=vector_repository,
            reranker=self.rerank_service,
        )

        self.sql_generate_service = SQLGenerateService(
            llm_service=self.llm_service,
            retry_service=self.retry_strategy_service,
            rag_service=self.rag_service,
            metadata_bundle=metadata_bundle,
        )

        self.execute_db_service = ExecuteDBService(
            rdb_repository=rdb_repository,
            column_map=metadata_bundle.column_map,
            valid_joins=metadata_bundle.valid_joins,
            db_schema=settings.POSTGRES_SCHEMA,
        )

        self.result_validation_service = ResultValidationService()

        self.answer_service = AnswerService(llm_service=self.llm_service)

        self.retry_decision_service = RetryDecisionService()
        
        # ─────────────────────────────
        # 🔥 RAG Stack
        # ─────────────────────────────

        # 1️⃣ BM25 (fewshot용)
        self.bm25_index = BM25Index(
            vector_repository=vector_repository,
            collection_name="fewshot",
        )

        # 2️⃣ Retrieval Engine
        self.retrieval_engine = RetrievalEngine(
            vector_repository=vector_repository,
            rerank_service=self.rerank_service,
            bm25_index=self.bm25_index,
        )

        # 3️⃣ RAG Service
        self.rag_service = RAGService(retrieval_engine=self.retrieval_engine)
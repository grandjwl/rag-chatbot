# app/container.py
# 서비스 컨테이너: 모든 서비스 인스턴스를 한 곳에서 생성하고 보관 (의존성 주입 컨테이너)

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
        _reranker_provider = provider_registry.get_reranker(settings.COHERE_MODEL)
        _embedding_provider = provider_registry.get_embedding(settings.EMBEDDING_MODEL)
        self.conversation_repository = conversation_repository

        self.llm_service = LLMService(
            llm_registry=provider_registry,
            prompt_registry=prompt_registry,
        )

        self.rerank_service = RerankService(reranker=_reranker_provider)

        _bm25_collections = ["fewshot", "bizterm_store", "table_schema_store", "refine_store"]
        self.bm25_indexes = {
            name: BM25Index(vector_repository=vector_repository, collection_name=name)
            for name in _bm25_collections
        }

        self.retrieval_engine = RetrievalEngine(
            vector_repository=vector_repository,
            rerank_service=self.rerank_service,
            bm25_indexes=self.bm25_indexes,
            embedding_provider=_embedding_provider,
        )

        self.rag_service = RAGService(retrieval_engine=self.retrieval_engine)

        self.router_service = RouterService(llm_service=self.llm_service)

        self.retry_strategy_service = RetryStrategyService(metadata_bundle.column_map)

        self.memory_service = MemoryService(
            conversation_repository=conversation_repository
        )

        self.refine_service = RefineService(engine=self.retrieval_engine)

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

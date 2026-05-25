# app/dependency.py

from app.container import ServiceContainer
from app.prompts.registry import PromptRegistry
from app.providers.registry import ProviderRegistry

from app.providers.llm.gemini_llm_provider import GeminiLLMProvider
from app.providers.embedding.gemini_embedding_provider import GeminiEmbeddingProvider
from app.providers.reranker.cohere_provider import CohereRerankerProvider

from app.infra.database.postgre_rdb_client import PostgresRDBClient
from app.infra.database.rdb_repository import RDBRepository
from app.infra.database.rdb_metadata_loader import RDBMetaRepository
from app.infra.vector.chroma_vector_client import ChromaVectorClient
from app.infra.vector.vector_repository import VectorRepository
from app.infra.database.conversation_repository import ConversationRepository

from app.prompts.schema_context_builder import SchemaContextBuilder
from app.prompts.valid_joins import VALID_JOINS

from app.core.config import settings
from app.core.metadata_bundle import MetadataBundle


# -----------------------------
# Provider Registry
# -----------------------------
def create_provider_registry() -> ProviderRegistry:

    registry = ProviderRegistry()

    # LLM_MODEL과 서비스별 모델이 다를 수 있으므로 중복 제거 후 전부 등록
    llm_models_to_register = {
        settings.LLM_MODEL,
        settings.router_model,
        settings.sql_model,
        settings.sql_premium_model,
        settings.answer_model,
        settings.chitchat_model,
    }
    for model_name in llm_models_to_register:
        registry.register_llm(
            model_name=model_name,
            provider=GeminiLLMProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=model_name,
            ),
        )

    registry.register_embedding(
        model_name=settings.EMBEDDING_MODEL,
        provider=GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.EMBEDDING_MODEL,
        )
    )

    registry.register_reranker(
        model_name=settings.COHERE_MODEL,
        provider=CohereRerankerProvider(
            api_key=settings.COHERE_API_KEY,
            model_name=settings.COHERE_MODEL,
        ),
    )

    return registry


# -----------------------------
# RDB Repository
# -----------------------------
async def create_rdb_repository() -> RDBRepository:
    client = PostgresRDBClient()
    await client.connect()
    return RDBRepository(rdb_client=client)


# -----------------------------
# Vector Repository
# -----------------------------
def create_vector_repository(embedding_provider) -> VectorRepository:
    chroma_client = ChromaVectorClient(embedding_provider=embedding_provider)
    return VectorRepository(vector_client=chroma_client)


# -----------------------------
# metadata_bundle 생성
# -----------------------------
async def create_metadata_bundle(rdb_repository) -> dict:
    meta_repo = RDBMetaRepository(rdb_repository=rdb_repository)
    raw_meta = await meta_repo.load_all()

    builder = SchemaContextBuilder()
    schema_context = builder.build(raw_meta["column_map"])

    metadata_bundle = MetadataBundle(
        refine_cache=raw_meta["refine_cache"],
        column_map=raw_meta["column_map"],
        data_stats=raw_meta["data_stats"],
        schema_context=schema_context,
        valid_joins=VALID_JOINS,
    )
    return metadata_bundle


# -----------------------------
# 최종 Container (싱글턴 — 서버 생애주기 동안 1회 생성)
# -----------------------------

_container: ServiceContainer | None = None


async def get_container() -> ServiceContainer:
    global _container
    if _container is not None:
        return _container

    import asyncio

    prompt_registry = PromptRegistry()
    provider_registry = create_provider_registry()

    embedding_provider = provider_registry.get_embedding(settings.EMBEDDING_MODEL)

    rdb_repository = await create_rdb_repository()
    conversation_repository = ConversationRepository(rdb_repository=rdb_repository)

    vector_repository = create_vector_repository(embedding_provider=embedding_provider)

    metadata_bundle = await create_metadata_bundle(rdb_repository)

    container = ServiceContainer(
        prompt_registry=prompt_registry,
        provider_registry=provider_registry,
        vector_repository=vector_repository,
        rdb_repository=rdb_repository,
        conversation_repository=conversation_repository,
        metadata_bundle=metadata_bundle,
    )

    await asyncio.gather(*[idx.build() for idx in container.bm25_indexes.values()])

    _container = container
    return _container


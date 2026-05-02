#llmServer/app/core/config/__init__.py

from app.core.config.database import PostgresSettings
from app.core.config.llm_embedding import LLM_EMBEDDING_Settings
from app.core.config.vector import ChromaSettings
from app.core.config.cloudflare import CloudflareSettings
from app.core.config.rerank import Rerank_Settings


class Settings(
    PostgresSettings,
    LLM_EMBEDDING_Settings,
    ChromaSettings,
    CloudflareSettings,
    Rerank_Settings,
):
    pass


settings = Settings()

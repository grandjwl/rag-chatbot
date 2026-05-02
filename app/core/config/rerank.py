# llmServer/app/core/config/rerank.py

from app.core.config.base import BaseAppSettings

class Rerank_Settings(BaseAppSettings):
    COHERE_API_KEY: str
    COHERE_MODEL: str
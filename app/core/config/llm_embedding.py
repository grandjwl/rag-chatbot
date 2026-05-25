# llmServer/app/core/config/llm.py

from app.core.config.base import BaseAppSettings


class LLM_EMBEDDING_Settings(BaseAppSettings):
    GEMINI_API_KEY: str
    LLM_MODEL: str
    EMBEDDING_MODEL: str

    router_model: str      = "gemini-2.5-flash-lite"
    sql_model: str         = "gemini-2.5-flash"
    sql_premium_model: str = "gemini-2.5-pro"      # 마지막 재시도(retry_count>=2)
    answer_model: str      = "gemini-2.5-flash"
    chitchat_model: str    = "gemini-2.5-flash-lite"
    
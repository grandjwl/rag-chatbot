# llmServer/app/core/config/llm.py

from app.core.config.base import BaseAppSettings


class LLM_EMBEDDING_Settings(BaseAppSettings):
    GEMINI_API_KEY: str
    LLM_MODEL: str
    EMBEDDING_MODEL: str

    router_model: str = "gemini-2.5-flash-lite"   # 분류만 하므로 lite 유지
    sql_model: str = "gemini-2.5-flash"
    answer_model: str = "gemini-2.5-flash"
    chitchat_model: str = "gemini-2.5-flash-lite"
    
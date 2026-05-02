# llmServer/app/core/config/vector.py

from app.core.config.base import BaseAppSettings

class ChromaSettings(BaseAppSettings):
    CHROMA_HOST: str
    CHROMA_PORT: int
    CHROMA_SSL: bool = False



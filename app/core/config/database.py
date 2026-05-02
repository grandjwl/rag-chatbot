# llmServer/app/core/config/database.py

from app.core.config.base import BaseAppSettings


class PostgresSettings(BaseAppSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SCHEMA: str
    CONVERSATION_SCHEMA: str

    @property
    def POSTGRES_DSN(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

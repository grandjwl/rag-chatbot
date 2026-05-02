# llmServer/app/core/config/base.py

from pydantic_settings import BaseSettings

class BaseAppSettings(BaseSettings):
    class Config:
        env_file = ".env"
        extra = "ignore"
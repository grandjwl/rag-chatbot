# llmServer/app/core/config/cloudflare.py

from app.core.config.base import BaseAppSettings

class CloudflareSettings(BaseAppSettings):
    CLOUDFLARE_HOSTNAME: str | None = None



# llmServer/main.py

from fastapi import FastAPI
from app.api.v1.routes import main_router
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings
from app.core.logging.logging_config import setup_logging

setup_logging()

app = FastAPI()

app.include_router(main_router.router, )

@app.on_event("startup")
async def startup_event():
    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()
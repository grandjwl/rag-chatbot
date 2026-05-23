# llmServer/main.py

from fastapi import FastAPI
from app.api.v1.routes import main_router
from app.core.logging.logging_config import setup_logging

setup_logging()

app = FastAPI()

app.include_router(main_router.router)
# app/core/logging/logging_config.py

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.core.logging.logging_json_formatter import CompactApiFormatter


def setup_logging():
    os.makedirs("logs", exist_ok=True)

    # ─────────────────────────────────────────────────────────
    # logs/app.log — JSON, 기술 세부사항 (LLM 토큰·비용·레이턴시)
    # "app" 네임스페이스만 수집 (외부 라이브러리 노이즈 차단)
    # ─────────────────────────────────────────────────────────
    json_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    json_handler.setFormatter(CompactApiFormatter())

    # root는 WARNING — uvicorn/chromadb/asyncpg/httpx 등 노이즈 차단
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    root.handlers.clear()

    # 우리 코드(app.*)만 INFO로 app.log에 기록
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    app_logger.handlers.clear()
    app_logger.addHandler(json_handler)

    # 외부 라이브러리 노이즈 차단
    for lib in ("uvicorn.access", "chromadb", "asyncpg", "httpx", "google"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    # 내부 bookkeeping — 유료 모델 호출 + 에러 외 억제
    for internal in (
        "app.providers.registry",              # "Provider registered/selected" 반복
        "app.agent.nodes.time_node",           # 노드별 ms 타이밍
        "app.services.llm_service",            # generate start/success (gemini log로 대체)
        "app.services.sql_generate_service",   # 생성된 SQL 내용 (flow.log에 있음)
        "app.providers.reranker.cohere_provider",  # 초기화 메시지
    ):
        logging.getLogger(internal).setLevel(logging.WARNING)

    # ─────────────────────────────────────────────────────────
    # 콘솔 + logs/flow.log — 텍스트, 비즈니스 흐름 (사람이 읽는 용)
    #   REQUEST → QUESTION → ROUTE → SQL → DB → ANSWER → DONE
    # ─────────────────────────────────────────────────────────
    flow_fmt = logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(flow_fmt)

    flow_file = RotatingFileHandler(
        "logs/flow.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    flow_file.setFormatter(flow_fmt)

    flow_logger = logging.getLogger("flow")
    flow_logger.setLevel(logging.INFO)
    flow_logger.propagate = False
    flow_logger.handlers.clear()
    flow_logger.addHandler(console)
    flow_logger.addHandler(flow_file)

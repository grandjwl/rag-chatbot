# app/core/logging/logging_config.py

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.core.logging.logging_json_formatter import JsonFormatter


def setup_logging():
    os.makedirs("logs", exist_ok=True)

    # ─────────────────────────────────────────────────────────
    # logs/app.log — JSON, 기술 세부사항 (LLM 토큰·비용·레이턴시)
    # ─────────────────────────────────────────────────────────
    json_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    json_handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(json_handler)

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
    flow_logger.propagate = False  # app.log로 중복 전파 방지
    flow_logger.handlers.clear()
    flow_logger.addHandler(console)
    flow_logger.addHandler(flow_file)

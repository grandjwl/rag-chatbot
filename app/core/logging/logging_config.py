# app/core/logging/logging_config.py

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.core.logging.logging_json_formatter import JsonFormatter


def setup_logging():
    os.makedirs("logs", exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = JsonFormatter()

    # 콘솔
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 파일
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
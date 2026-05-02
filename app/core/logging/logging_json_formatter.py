# app/core/logging/logging_json_formatter.py

import json
import logging
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 기본 필드 제외하고 extra 자동 포함
        skip_fields = {
            "name", "msg", "args", "levelname", "levelno",
            "pathname", "filename", "module", "exc_info",
            "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process",
        }

        for key, value in record.__dict__.items():
            if key not in skip_fields:
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)
# llmServer/infra/database/rdb_metadata_loader.py

from collections import defaultdict
from typing import Dict, Any

from app.infra.database.rdb_repository import RDBRepository
from app.core.config import settings


class RDBMetaRepository:
    """
    PostgreSQL 메타데이터 전용 Repository (Infra Layer)

    책임:
    - 제조사 / 고객사 목록
    - 매출 데이터 기간
    - 테이블/컬럼 구조

    ❗ 비즈니스 로직 포함 금지
    ❗ 프롬프트 생성 금지
    """

    def __init__(self, rdb_repository: RDBRepository):
        self.rdb_repository = rdb_repository
        self.schema = settings.POSTGRES_SCHEMA

    # -------------------------------------------------
    # 통합 로드 (앱 시작 시 1회 권장)
    # -------------------------------------------------
    async def load_all(self) -> Dict[str, Any]:
        return {
            "refine_cache": await self.load_entities(),
            "data_stats": await self.load_date_range(),
            "column_map": await self.load_column_map(),
        }

    # -------------------------------------------------
    # 제조사 / 고객사 목록
    # -------------------------------------------------
    async def load_entities(self) -> Dict[str, list]:
        manufacturers = await self.rdb_repository.fetch(
            f"SELECT name FROM {self.schema}.manufacturers"
        )

        vendors = await self.rdb_repository.fetch(
            f"SELECT vendor_name FROM {self.schema}.vendors"
        )

        return {
            "manufacturers": [row["name"] for row in manufacturers],
            "vendors": [row["vendor_name"] for row in vendors],
        }

    # -------------------------------------------------
    # 매출 데이터 기간
    # -------------------------------------------------
    async def load_date_range(self) -> Dict[str, str | None]:
        row = await self.rdb_repository.fetch_one(
            f"""
            SELECT MIN(sale_date) AS min_date,
                   MAX(sale_date) AS max_date
            FROM {self.schema}.sales_orders
            """
        )

        if not row:
            return {"min_date": None, "max_date": None}

        return {
            "min_date": str(row["min_date"]) if row["min_date"] else None,
            "max_date": str(row["max_date"]) if row["max_date"] else None,
        }

    # -------------------------------------------------
    # 테이블/컬럼 구조 (1회 쿼리)
    # -------------------------------------------------
    async def load_column_map(self) -> Dict[str, list]:
        rows = await self.rdb_repository.fetch(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = $1
            ORDER BY table_name, ordinal_position
            """,
            self.schema,
        )

        column_map = defaultdict(list)

        for row in rows:
            column_map[row["table_name"]].append(row["column_name"])

        return dict(column_map)
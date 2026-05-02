import logging
from typing import Any, List
from app.infra.database.base import BaseRDBClient

logger = logging.getLogger(__name__)


class RDBRepository:
    """
    RDB 접근 계층.
    Service는 DB 벤더를 모른다.
    """

    def __init__(self, rdb_client: BaseRDBClient):
        self.rdb_client = rdb_client

    # -------------------------------
    # 조회
    # -------------------------------
    async def fetch(self, query: str, *args) -> List[Any]:
        try:
            return await self.rdb_client.fetch(query, *args)
        except Exception:
            logger.exception("RDB fetch failed")
            raise
    
    async def fetch_one(self, query: str, *args):
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None


    # -------------------------------
    # 실행
    # -------------------------------
    async def execute(self, query: str, *args) -> Any:
        try:
            # 디버깅용
            # print("🚨 EXEC QUERY:")
            # print(query)
            # print("ARGS:", args)
            return await self.rdb_client.execute(query, *args)
        except Exception:
            logger.exception("RDB execute failed")
            raise

    # -------------------------------
    # 트랜잭션 지원 (추가)
    # -------------------------------
    def transaction(self):
        return self.rdb_client.transaction()
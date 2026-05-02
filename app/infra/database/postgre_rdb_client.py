# llmServer/app/infra/database/postgre_rdb_client.py

import asyncpg
from typing import Any, List
from app.core.config import settings
from app.infra.database.base import BaseRDBClient
from contextlib import asynccontextmanager


class PostgresRDBClient(BaseRDBClient):
    """
    asyncpg 기반 PostgreSQL 클라이언트 구현체.
    """

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=settings.POSTGRES_DSN,
                min_size=1,
                max_size=5,
            )

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def fetch(self, query: str, *args) -> List[Any]:
        if not self._pool:
            raise RuntimeError("Postgres pool is not initialized. Call connect() first.")

        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute(self, query: str, *args) -> Any:
        if not self._pool:
            raise RuntimeError("Postgres pool is not initialized. Call connect() first.")

        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
          
    @asynccontextmanager
    async def transaction(self):
        # ❌ self.pool.acquire() -> self._pool (언더바 누락 확인 필요)
        if not self._pool:
            raise RuntimeError("Pool not initialized")
            
        async with self._pool.acquire() as conn:
            # 이 시점에 BEGIN 명령이 나갑니다.
            async with conn.transaction():
                # 사용자는 이 conn을 받아서 여러 작업을 수행합니다.
                yield conn 
            # 이 블록을 나가면 자동으로 COMMIT 혹은 ROLLBACK이 나갑니다.
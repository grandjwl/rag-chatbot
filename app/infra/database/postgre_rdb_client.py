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

    async def fetch_readonly(self, query: str, *args) -> List[Any]:
        if not self._pool:
            raise RuntimeError("Postgres pool is not initialized. Call connect() first.")

        async with self._pool.acquire() as conn:
            # 읽기 전용 트랜잭션: 검증을 우회한 쓰기 쿼리도 DB 엔진이 거부한다.
            async with conn.transaction(readonly=True):
                return await conn.fetch(query, *args)

    async def execute(self, query: str, *args) -> Any:
        if not self._pool:
            raise RuntimeError("Postgres pool is not initialized. Call connect() first.")

        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
          
    @asynccontextmanager
    async def transaction(self):
        if not self._pool:
            raise RuntimeError("Pool not initialized")

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn
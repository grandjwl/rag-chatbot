# app/infra/database/test/test_rdb_repository.py
# PYTHONPATH=. python -m app.infra.database.test.test_rdb_repository

import asyncio

from app.core.config import settings
from app.infra.network.cloudflare import CloudflareTunnel
from app.infra.database.postgre_rdb_client import PostgresRDBClient
from app.infra.database.rdb_repository import RDBRepository


async def main():
    # 🔥 1. 터널 열기 (필요하면)
    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()

    try:
        # 🔥 2. DB Client 생성 및 연결
        client = PostgresRDBClient()
        await client.connect()

        # 🔥 3. Repository로 감싸기
        repo = RDBRepository(client)

        # 🔥 4. 실제 테이블 조회
        query = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{settings.POSTGRES_SCHEMA}';
            """
        rows = await repo.fetch(query)

        print("📦 조회 결과:")
        for row in rows:
            print(dict(row))

        await client.close()

    finally:
        tunnel.stop()


if __name__ == "__main__":
    asyncio.run(main())
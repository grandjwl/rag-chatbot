# llmServer/app/infra/database/test/test_rdb_metadata_loader.py
# PYTHONPATH=. python -m app.infra.database.test.test_rdb_metadata_loader

import asyncio

from app.infra.database.postgre_rdb_client import PostgresRDBClient
from app.infra.database.rdb_repository import RDBRepository
from app.infra.database.rdb_metadata_loader import RDBMetaRepository
from app.infra.network.cloudflare import CloudflareTunnel
from app.prompts.schema_context_builder import SchemaContextBuilder
from app.core.config import settings

async def main():

    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()
     
    print("🔌 Postgres 연결 중...")

    client = PostgresRDBClient()
    await client.connect()

    repo = RDBRepository(rdb_client=client)
    meta_repo = RDBMetaRepository(repo)

    print("📦 메타데이터 로딩 중...\n")

    meta = await meta_repo.load_all()
    
    builder = SchemaContextBuilder()
    schema_ctx = builder.build(meta["column_map"])


    # ----------------------------
    # refine 확인
    # ----------------------------
    print("=== refine CACHE ===")
    print("manufacturers 개수:", len(meta["refine_cache"]["manufacturers"]))
    print("vendors 개수:", len(meta["refine_cache"]["vendors"]))
    print("sample manufacturers:", meta["refine_cache"]["manufacturers"][:5])
    print()

    # ----------------------------
    # 날짜 범위 확인
    # ----------------------------
    print("=== DATA RANGE ===")
    print("min_date:", meta["data_stats"]["min_date"])
    print("max_date:", meta["data_stats"]["max_date"])
    print()

    # ----------------------------
    # 컬럼맵 확인
    # ----------------------------
    print("=== COLUMN MAP ===")
    print("테이블 수:", len(meta["column_map"]))
    print("sales_orders 컬럼:", meta["column_map"].get("sales_orders"))
    print()

    # ----------------------------
    # schema_context 확인
    # ----------------------------    
    print("=== SCHEMA CONTEXT ===")
    print(schema_ctx)
    await client.close()

    print("✅ 완료")


if __name__ == "__main__":
    asyncio.run(main())
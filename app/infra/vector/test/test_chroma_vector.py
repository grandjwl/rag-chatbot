# llmServer/app/infra/vector/test/test_chroma_vector.py
# PYTHONPATH=. python -m app.infra.vector.test.test_chroma_vector

import asyncio
from app.infra.vector.chroma_vector_client import ChromaVectorClient


async def main():
    client = ChromaVectorClient()

    # HttpClient는 동기 객체라 바로 접근 가능
    collections = client.client.list_collections()

    print("📦 저장된 컬렉션 목록:")
    for col in collections:
        print("-", col.name)


if __name__ == "__main__":
    asyncio.run(main())
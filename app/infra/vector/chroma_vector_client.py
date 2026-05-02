# llmServer/app/infra/vector/chroma_vector_client.py

import asyncio
import chromadb
from typing import List, Tuple
from app.core.config import settings
from app.infra.vector.base import BaseVectorClient
from app.providers.embedding.base import BaseEmbeddingProvider
from app.infra.vector.exceptions import VectorCollectionNotFound


class ChromaVectorClient(BaseVectorClient):
    """
    Chroma SDK 어댑터.
    BaseVectorClient 인터페이스에 맞게 외부 SDK를 변환한다.
    """

    def __init__(self, embedding_provider: BaseEmbeddingProvider):
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            ssl=settings.CHROMA_SSL,
        )
        self.embedder = embedding_provider

    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int,
    ) -> List[Tuple[str, dict, float]]:

        loop = asyncio.get_running_loop()

        def _search():
            collection = self._get_collection(collection_name)

            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]

            return list(zip(docs, metas, distances))

        return await loop.run_in_executor(None, _search)

    async def search_by_text(
    self,
    collection_name: str,
    query_text: str,
    top_k: int,
    ) -> List[Tuple[str, dict, float]]:

        # 1️⃣ async embed는 여기서 await
        embeddings = await self.embedder.embed([query_text])
        query_embedding = embeddings[0]

        # 2️⃣ 그 다음 search 재사용
        return await self.search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=top_k,
        )


    async def insert(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[dict],
    ):

        loop = asyncio.get_running_loop()

        def _insert():
            collection = self._get_collection(collection_name)

            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

        await loop.run_in_executor(None, _insert)
        
    # RAG 로직에서 사용
    async def get_all(self, collection_name: str):

        loop = asyncio.get_running_loop()

        def _get():
            collection = self._get_collection(collection_name)
            return collection.get()

        return await loop.run_in_executor(None, _get)


    async def count(self, collection_name: str):

        loop = asyncio.get_running_loop()

        def _count():
            collection = self._get_collection(collection_name)
            return collection.count()

        return await loop.run_in_executor(None, _count)


    async def delete(self, collection_name: str, ids: List[str]):

        loop = asyncio.get_running_loop()

        def _delete():
            collection = self._get_collection(collection_name)
            collection.delete(ids=ids)

        await loop.run_in_executor(None, _delete)
        
    def _get_collection(self, name: str):
        try:
            return self.client.get_collection(name)
        except Exception as e:
            raise VectorCollectionNotFound(
                f"Vector collection '{name}' does not exist."
            ) from e
        
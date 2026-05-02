# llmServer/app/infra/vector/vector_repository.py

import logging
from typing import List, Tuple, Dict, Any
from app.infra.vector.base import BaseVectorClient

logger = logging.getLogger(__name__)


class VectorRepository:
    """
    벡터 검색/저장 접근 계층.
    Service는 Chroma SDK를 모른다.
    """

    def __init__(self, vector_client: BaseVectorClient):
        self.vector_client = vector_client

    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 3,
    ) -> List[Tuple[str, dict, float]]:

        try:
            return await self.vector_client.search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        except Exception:
            logger.exception("Vector search failed")
            raise
    
    async def search_by_text(
    self,
    collection_name: str,
    query_text: str,
    top_k: int = 3,
  ):
      try:
          return await self.vector_client.search_by_text(
              collection_name=collection_name,
              query_text=query_text,
              top_k=top_k,
          )
      except Exception:
          logger.exception("Vector search_by_text failed")
          raise

    async def insert(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[dict],
    ):
        try:
            await self.vector_client.insert(
                collection_name=collection_name,
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception:
            logger.exception("Vector insert failed")
            raise
          
    # -----------------------------
    # 추가된 기능 (RAG 로직에서 사용)
    # -----------------------------
    async def get_all(self, collection_name: str) -> Dict[str, Any]:
        return await self.vector_client.get_all(collection_name)

    async def count(self, collection_name: str) -> int:
        return await self.vector_client.count(collection_name)

    async def delete(self, collection_name: str, ids: List[str]):
        await self.vector_client.delete(collection_name, ids)
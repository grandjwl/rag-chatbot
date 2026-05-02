# llmServer/app/infra/vector/base.py

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any


class BaseVectorClient(ABC):

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int,
    ) -> List[Tuple[str, dict, float]]:
        pass

    @abstractmethod
    async def search_by_text(
        self,
        collection_name: str,
        query_text: str,
        top_k: int,
    ) -> List[Tuple[str, dict, float]]:
        pass

    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[dict],
    ):
        pass

    @abstractmethod
    async def get_all(
        self,
        collection_name: str,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def count(
        self,
        collection_name: str,
    ) -> int:
        pass

    @abstractmethod
    async def delete(
        self,
        collection_name: str,
        ids: List[str],
    ):
        pass
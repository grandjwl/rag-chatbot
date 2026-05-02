# provider/embedding/base.py
from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        pass
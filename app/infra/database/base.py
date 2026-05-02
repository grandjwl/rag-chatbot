# llmServer/app/infra/database/base.py

from abc import ABC, abstractmethod
from typing import Any, List


class BaseRDBClient(ABC):
    """
    RDB 표준 인터페이스.
    외부 DB 벤더와 무관하게 우리 시스템 기준으로 정의한다.
    """

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def fetch(self, query: str, *args) -> List[Any]:
        """
        SELECT 계열 쿼리
        """
        pass

    @abstractmethod
    async def execute(self, query: str, *args) -> Any:
        """
        INSERT / UPDATE / DELETE 계열 쿼리
        """
        pass
      
    @abstractmethod
    def transaction(self):
        """
        트랜잭션 컨텍스트 매니저 반환
        사용 예:
        async with client.transaction():
            ...
        """
        pass
      
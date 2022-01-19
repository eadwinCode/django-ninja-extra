from abc import ABC, abstractmethod
from typing import Any, Optional

from django.http import HttpRequest
from ninja.security.apikey import APIKeyBase, APIKeyCookie, APIKeyHeader, APIKeyQuery

__all__ = [
    "AsyncAPIKeyBase",
    "AsyncAPIKeyQuery",
    "AsyncAPIKeyCookie",
    "AsyncAPIKeyHeader",
]


class AsyncAPIKeyBase(APIKeyBase, ABC):
    async def __call__(self, request: HttpRequest) -> Optional[Any]:
        key = self._get_key(request)
        return await self.authenticate(request, key)

    @abstractmethod
    async def authenticate(
        self, request: HttpRequest, key: Optional[str]
    ) -> Optional[Any]:
        pass  # pragma: no cover


class AsyncAPIKeyQuery(AsyncAPIKeyBase, APIKeyQuery, ABC):
    pass


class AsyncAPIKeyCookie(AsyncAPIKeyBase, APIKeyCookie, ABC):
    pass


class AsyncAPIKeyHeader(AsyncAPIKeyBase, APIKeyHeader, ABC):
    pass

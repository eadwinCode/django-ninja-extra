import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from django.conf import settings
from django.http import HttpRequest
from ninja.security.http import DecodeError, HttpBasicAuth, HttpBearer

logger = logging.getLogger("django")

__all__ = ["AsyncHttpBearer", "AsyncHttpBasicAuth"]


class AsyncHttpBearer(HttpBearer, ABC):
    async def __call__(self, request: HttpRequest) -> Optional[Any]:
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return None
        parts = auth_value.split(" ")

        if parts[0].lower() != self.openapi_scheme:
            if settings.DEBUG:
                logger.error(f"Unexpected auth - '{auth_value}'")
            return None
        token = " ".join(parts[1:])
        return await self.authenticate(request, token)

    @abstractmethod
    async def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        pass  # pragma: no cover


class AsyncHttpBasicAuth(HttpBasicAuth, ABC):
    async def __call__(self, request: HttpRequest) -> Optional[Any]:
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return None

        try:
            username, password = self.decode_authorization(auth_value)
        except DecodeError as e:
            if settings.DEBUG:
                logger.exception(e)
            return None
        return await self.authenticate(request, username, password)

    @abstractmethod
    async def authenticate(
        self, request: HttpRequest, username: str, password: str
    ) -> Optional[Any]:
        pass  # pragma: no cover

from django.http import HttpRequest
from ninja_extra.security.api_key import AsyncAPIKeyCookie
from django.conf import settings

__all__ = ["AsyncSessionAuth"]

from typing import Optional, Any


class AsyncSessionAuth(AsyncAPIKeyCookie):
    """Reusing Django session authentication"""
    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        if request.user.is_authenticated:
            return request.user
        return None

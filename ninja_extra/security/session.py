from django.conf import settings
from django.http import HttpRequest
from ninja.signature import is_async

from ninja_extra.security.api_key import AsyncAPIKeyCookie

__all__ = ["AsyncSessionAuth"]

from typing import Any, Optional


class AsyncSessionAuth(AsyncAPIKeyCookie):
    """Reusing Django session authentication"""

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(
        self, request: HttpRequest, key: Optional[str]
    ) -> Optional[Any]:
        if hasattr(request, "auser") and is_async(request.auser):
            current_user = await request.auser()
        else:
            current_user = request.user

        if current_user.is_authenticated:
            return current_user
        return None

from django.conf import settings
from django.contrib.auth.middleware import get_user
from django.http import HttpRequest

from ninja_extra.security.api_key import AsyncAPIKeyCookie

__all__ = ["AsyncSessionAuth"]

from typing import Any, Optional


class AsyncSessionAuth(AsyncAPIKeyCookie):
    """Reusing Django session authentication"""

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(
        self, request: HttpRequest, key: Optional[str]
    ) -> Optional[Any]:
        from asgiref.sync import sync_to_async

        if hasattr(request, "auser"):
            current_user = await request.auser()
        else:
            current_user = await sync_to_async(get_user)(request)

        if current_user.is_authenticated:
            return current_user
        return None

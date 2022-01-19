from ninja.security import *
from .session import AsyncSessionAuth
from .http import AsyncHttpBasicAuth, AsyncHttpBearer
from .api_key import AsyncAPIKeyCookie, AsyncAPIKeyBase, AsyncAPIKeyHeader, AsyncAPIKeyQuery

__all__ = [
    "APIKeyCookie",
    "APIKeyHeader",
    "APIKeyQuery",
    "HttpBasicAuth",
    "HttpBearer",
    "SessionAuth",
    "django_auth",
    "async_django_auth",
    "AsyncHttpBasicAuth", "AsyncHttpBasicAuth", "AsyncHttpBearer",
    "AsyncAPIKeyCookie",
    "AsyncAPIKeyBase",
    "AsyncAPIKeyHeader",
    "AsyncAPIKeyQuery",
]

async_django_auth = AsyncSessionAuth()

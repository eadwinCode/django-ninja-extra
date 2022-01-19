from ninja.security import (
    APIKeyCookie,
    APIKeyHeader,
    APIKeyQuery,
    HttpBasicAuth,
    HttpBearer,
    SessionAuth,
    django_auth,
)

from .api_key import (
    AsyncAPIKeyBase,
    AsyncAPIKeyCookie,
    AsyncAPIKeyHeader,
    AsyncAPIKeyQuery,
)
from .http import AsyncHttpBasicAuth, AsyncHttpBearer
from .session import AsyncSessionAuth

__all__ = [
    "APIKeyCookie",
    "APIKeyHeader",
    "APIKeyQuery",
    "HttpBasicAuth",
    "HttpBearer",
    "SessionAuth",
    "django_auth",
    "async_django_auth",
    "AsyncHttpBasicAuth",
    "AsyncHttpBasicAuth",
    "AsyncHttpBearer",
    "AsyncAPIKeyCookie",
    "AsyncAPIKeyBase",
    "AsyncAPIKeyHeader",
    "AsyncAPIKeyQuery",
]

async_django_auth = AsyncSessionAuth()

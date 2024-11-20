from unittest.mock import AsyncMock, Mock

import pytest
from asgiref.sync import sync_to_async
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest

from ninja_extra.security import async_django_auth


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_async_session_auth():
    request = HttpRequest()

    # Add session to request
    middleware = SessionMiddleware(lambda x: x)
    await sync_to_async(middleware.process_request)(request)
    await sync_to_async(request.session.save)()

    # Test async authenticated user
    async_user = AsyncMock()
    async_user.is_authenticated = True
    request.auser = AsyncMock(return_value=async_user)

    authenticated_user = await async_django_auth.authenticate(request, None)
    assert authenticated_user == async_user
    request.auser.assert_called_once()

    # Test async non-authenticated user
    async_user.is_authenticated = False
    authenticated_user = await async_django_auth.authenticate(request, None)
    assert authenticated_user is None

    # Test non-async authenticated user
    delattr(request, "auser")
    sync_user = Mock()
    sync_user.is_authenticated = True
    request._cached_user = sync_user

    authenticated_user = await async_django_auth.authenticate(request, None)
    assert authenticated_user == sync_user

    # Test non-async non-authenticated user
    sync_user.is_authenticated = False
    authenticated_user = await async_django_auth.authenticate(request, None)
    assert authenticated_user is None

from unittest.mock import AsyncMock, Mock

import pytest
from django.http import HttpRequest

from ninja_extra.security.session import AsyncSessionAuth


@pytest.mark.asyncio
async def test_async_session_auth():
    auth = AsyncSessionAuth()
    request = HttpRequest()

    # Test async authenticated user
    async_user = AsyncMock()
    async_user.is_authenticated = True
    request.auser = AsyncMock(return_value=async_user)

    authenticated_user = await auth.authenticate(request, None)
    assert authenticated_user == async_user
    request.auser.assert_called_once()

    # Test async non-authenticated user
    async_user.is_authenticated = False
    authenticated_user = await auth.authenticate(request, None)
    assert authenticated_user is None

    # Test non-async authenticated user
    delattr(request, "auser")
    sync_user = Mock()
    sync_user.is_authenticated = True
    request.user = sync_user

    authenticated_user = await auth.authenticate(request, None)
    assert authenticated_user == sync_user

    # Test non-async non-authenticated user
    sync_user.is_authenticated = False
    authenticated_user = await auth.authenticate(request, None)
    assert authenticated_user is None

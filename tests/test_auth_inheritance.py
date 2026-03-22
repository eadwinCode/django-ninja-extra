"""Test that API-level auth is inherited by controller routes.

Reproduces the issue where NinjaExtraAPI(auth=AsyncJWTAuth()) would not
propagate auth to @api_controller routes, causing 403s even with valid tokens.
"""

import pytest
from ninja.security import HttpBearer
from ninja.testing import TestAsyncClient, TestClient

from ninja_extra import ControllerBase, NinjaExtraAPI, api_controller, http_get


class AsyncBearerAuth(HttpBearer):
    """Simulates django-ninja-jwt's AsyncJWTAuth."""

    async def authenticate(self, request, token):
        if token == "valid-token":
            return {"user_id": 1}
        return None


class SyncBearerAuth(HttpBearer):
    def authenticate(self, request, token):
        if token == "valid-token":
            return {"user_id": 1}
        return None


def test_controller_inherits_api_auth(reflect_context):
    """Controller routes with no explicit auth should inherit NinjaExtraAPI(auth=...)."""

    @api_controller("/protected")
    class ProtectedController(ControllerBase):
        @http_get("/data")
        def get_data(self):
            return {"secret": "value"}

    api = NinjaExtraAPI(auth=SyncBearerAuth())
    api.register_controllers(ProtectedController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert op.auth_callbacks, (
                    "Controller operation should have inherited API auth_callbacks"
                )

    client = TestClient(api)
    assert client.get("/protected/data").status_code == 401
    assert (
        client.get(
            "/protected/data", headers={"Authorization": "Bearer valid-token"}
        ).status_code
        == 200
    )


def test_controller_explicit_auth_not_overridden(reflect_context):
    """Controller with its own auth should NOT be overridden by API auth."""

    class ControllerAuth(HttpBearer):
        def authenticate(self, request, token):
            if token == "controller-token":
                return {"scope": "controller"}
            return None

    @api_controller("/scoped", auth=ControllerAuth())
    class ScopedController(ControllerBase):
        @http_get("/info")
        def get_info(self):
            return {"scoped": True}

    api = NinjaExtraAPI(auth=SyncBearerAuth())
    api.register_controllers(ScopedController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert len(op.auth_callbacks) == 1
                assert isinstance(op.auth_callbacks[0], ControllerAuth), (
                    "Controller-level auth should not be overridden by API auth"
                )

    client = TestClient(api)
    assert client.get("/scoped/info").status_code == 401
    assert (
        client.get(
            "/scoped/info", headers={"Authorization": "Bearer controller-token"}
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/scoped/info", headers={"Authorization": "Bearer valid-token"}
        ).status_code
        == 401
    )


def test_controller_without_api_auth(reflect_context):
    """When API has no auth, controller operations should remain unauthenticated."""

    @api_controller("/open")
    class OpenController(ControllerBase):
        @http_get("/ping")
        def ping(self):
            return {"ok": True}

    api = NinjaExtraAPI()
    api.register_controllers(OpenController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert op.auth_callbacks == [], (
                    "Operations should have no auth when API has no auth"
                )


@pytest.mark.asyncio
async def test_async_controller_inherits_api_auth(reflect_context):
    """Async controller routes should also inherit API-level auth."""

    @api_controller("/async-protected")
    class AsyncProtectedController(ControllerBase):
        @http_get("/data")
        async def get_data(self):
            return {"secret": "async_value"}

    api = NinjaExtraAPI(auth=AsyncBearerAuth(), urls_namespace="async_inherit")
    api.register_controllers(AsyncProtectedController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert op.auth_callbacks, (
                    "Async controller operation should have inherited API auth_callbacks"
                )

    client = TestAsyncClient(api)
    assert (await client.get("/async-protected/data")).status_code == 401
    assert (
        await client.get(
            "/async-protected/data",
            headers={"Authorization": "Bearer valid-token"},
        )
    ).status_code == 200

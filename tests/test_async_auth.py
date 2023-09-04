import base64

import django
import pytest
from django.conf import settings
from ninja.security import APIKeyCookie
from ninja.testing import TestAsyncClient, TestClient

from ninja_extra import NinjaExtraAPI, exceptions
from ninja_extra.security import (
    AsyncAPIKeyCookie,
    AsyncAPIKeyHeader,
    AsyncAPIKeyQuery,
    AsyncHttpBasicAuth,
    AsyncHttpBearer,
    async_django_auth,
)

user_secret = base64.b64encode("admin:secret".encode("utf-8")).decode()


async def callable_auth(request):
    return request.GET.get("auth")


class KeyQuery(AsyncAPIKeyQuery):
    async def authenticate(self, request, key):
        if key == "keyquerysecret":
            return key


class KeyHeader(AsyncAPIKeyHeader):
    async def authenticate(self, request, key):
        if key == "keyheadersecret":
            return key


class KeyCookie(AsyncAPIKeyCookie):
    async def authenticate(self, request, key):
        if key == "keycookiersecret":
            return key


class SyncKeyCookie(APIKeyCookie):
    def authenticate(self, request, key):
        if key == "keycookiersecret":
            return key
        raise exceptions.NotAuthenticated()


class BasicAuth(AsyncHttpBasicAuth):
    async def authenticate(self, request, username, password):
        if username == "admin" and password == "secret":
            return username


class BearerAuth(AsyncHttpBearer):
    async def authenticate(self, request, token):
        if token == "bearertoken":
            return token


async def demo_operation(request):
    return {"auth": request.auth}


def sync_demo_operation(request):
    return {"auth": request.auth}


class MockUser(str):
    is_authenticated = True


BODY_UNAUTHORIZED_DEFAULT = {"detail": "Unauthorized"}

if not django.VERSION < (3, 1):

    class TestAsyncCSRFClient(TestAsyncClient):
        def _build_request(self, *args, **kwargs):
            request = super()._build_request(*args, **kwargs)
            request._dont_enforce_csrf_checks = False
            return request

    csrf_OFF = NinjaExtraAPI(urls_namespace="csrf_OFF")
    csrf_ON = NinjaExtraAPI(urls_namespace="csrf_ON", csrf=True)

    @csrf_OFF.post("/post")
    async def post_off(request):
        return {"success": True}

    @csrf_ON.post("/post")
    async def post_on(request):
        return {"success": True}

    @csrf_ON.post("/post-async-sync-auth", auth=SyncKeyCookie())
    async def auth_with_sync_auth(request):
        return {"success": True}

    TOKEN = "1bcdefghij2bcdefghij3bcdefghij4bcdefghij5bcdefghij6bcdefghijABCD"
    COOKIES = {settings.CSRF_COOKIE_NAME: TOKEN}

    @pytest.mark.asyncio
    async def test_auth_with_sync_auth_fails():
        async_client = TestAsyncClient(csrf_ON)
        res = await async_client.post("/post-async-sync-auth")
        assert res.status_code == 401
        assert res.json() == {"detail": "Authentication credentials were not provided."}

    @pytest.mark.asyncio
    async def test_auth_with_sync_auth_works():
        async_client = TestAsyncClient(csrf_ON)
        res = await async_client.post(
            "/post-async-sync-auth", COOKIES={"key": "keycookiersecret"}
        )
        assert res.status_code == 200
        assert res.json() == {"success": True}

    @pytest.mark.asyncio
    async def test_csrf_off():
        async_client = TestAsyncCSRFClient(csrf_OFF)
        res = await async_client.post("/post", COOKIES=COOKIES)
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_csrf_on():
        async_client = TestAsyncCSRFClient(csrf_ON)
        res = await async_client.post("/post", COOKIES=COOKIES)
        assert res.status_code == 403

        # check with token in formdata
        response = await async_client.post(
            "/post", {"csrfmiddlewaretoken": TOKEN}, COOKIES=COOKIES
        )
        assert response.status_code == 200

        # check with headers
        response = await async_client.post(
            "/post", COOKIES=COOKIES, headers={"X-CSRFTOKEN": TOKEN}
        )
        assert response.status_code == 200


if not django.VERSION < (3, 1):
    api = NinjaExtraAPI(csrf=True, urls_namespace="async_auth")

    for path, auth in [
        ("django_auth", async_django_auth),
        ("callable", callable_auth),
        ("apikeyquery", KeyQuery()),
        ("apikeyheader", KeyHeader()),
        ("apikeycookie", KeyCookie()),
        ("basic", BasicAuth()),
        ("bearer", BearerAuth()),
    ]:
        api.get(f"/{path}", auth=auth, operation_id=path)(demo_operation)

    client = TestAsyncClient(api)


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,kwargs,expected_code,expected_body",
    [
        ("/django_auth", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        ("/django_auth", {"user": MockUser("admin")}, 200, {"auth": "admin"}),
        ("/callable", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        ("/callable?auth=demo", {}, 200, {"auth": "demo"}),
        ("/apikeyquery", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        ("/apikeyquery?key=keyquerysecret", {}, 200, {"auth": "keyquerysecret"}),
        ("/apikeyheader", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeyheader",
            {"headers": {"key": "keyheadersecret"}},
            200,
            {"auth": "keyheadersecret"},
        ),
        ("/apikeycookie", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeycookie",
            {"COOKIES": {"key": "keycookiersecret"}},
            200,
            {"auth": "keycookiersecret"},
        ),
        ("/basic", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/basic",
            {"headers": {"Authorization": f"Basic {user_secret}"}},
            200,
            {"auth": "admin"},
        ),
        (
            "/basic",
            {"headers": {"Authorization": f"{user_secret}"}},
            200,
            {"auth": "admin"},
        ),
        (
            "/basic",
            {"headers": {"Authorization": "Basic invalid"}},
            401,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
        (
            "/basic",
            {"headers": {"Authorization": "some invalid value"}},
            401,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
        ("/bearer", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/bearer",
            {"headers": {"Authorization": "Bearer bearertoken"}},
            200,
            {"auth": "bearertoken"},
        ),
        (
            "/bearer",
            {"headers": {"Authorization": "Invalid bearertoken"}},
            401,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
    ],
)
async def test_auth(path, kwargs, expected_code, expected_body, settings):
    for debug in (False, True):
        settings.DEBUG = debug
        response = await client.get(path, **kwargs)
        assert response.status_code == expected_code
        assert response.json() == expected_body


def test_auth_failure():
    sync_api = NinjaExtraAPI(csrf=True)
    sync_api.get(
        "/sync-cookie-auth", auth=SyncKeyCookie(), operation_id="sync-cookie-auth"
    )(sync_demo_operation)

    sync_client = TestClient(sync_api)
    res = sync_client.get("sync-cookie-auth")
    assert res.status_code == 401
    assert res.json() == {"detail": "Authentication credentials were not provided."}

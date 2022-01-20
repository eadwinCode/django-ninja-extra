import django
import pytest
from ninja.testing import TestAsyncClient

from ninja_extra import NinjaExtraAPI
from ninja_extra.security import (
    AsyncAPIKeyCookie,
    AsyncAPIKeyHeader,
    AsyncAPIKeyQuery,
    AsyncHttpBasicAuth,
    AsyncHttpBearer,
    async_django_auth,
)


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


class MockUser(str):
    is_authenticated = True


BODY_UNAUTHORIZED_DEFAULT = dict(detail="Unauthorized")

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
        ("/django_auth", dict(user=MockUser("admin")), 200, dict(auth="admin")),
        ("/callable", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        ("/callable?auth=demo", {}, 200, dict(auth="demo")),
        ("/apikeyquery", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        ("/apikeyquery?key=keyquerysecret", {}, 200, dict(auth="keyquerysecret")),
        ("/apikeyheader", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeyheader",
            dict(headers={"key": "keyheadersecret"}),
            200,
            dict(auth="keyheadersecret"),
        ),
        ("/apikeycookie", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeycookie",
            dict(COOKIES={"key": "keycookiersecret"}),
            200,
            dict(auth="keycookiersecret"),
        ),
        ("/basic", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/basic",
            dict(headers={"Authorization": "Basic YWRtaW46c2VjcmV0"}),
            200,
            dict(auth="admin"),
        ),
        (
            "/basic",
            dict(headers={"Authorization": "YWRtaW46c2VjcmV0"}),
            200,
            dict(auth="admin"),
        ),
        (
            "/basic",
            dict(headers={"Authorization": "Basic invalid"}),
            401,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
        (
            "/basic",
            dict(headers={"Authorization": "some invalid value"}),
            401,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
        ("/bearer", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/bearer",
            dict(headers={"Authorization": "Bearer bearertoken"}),
            200,
            dict(auth="bearertoken"),
        ),
        (
            "/bearer",
            dict(headers={"Authorization": "Invalid bearertoken"}),
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

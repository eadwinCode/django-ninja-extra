import uuid

import django
import pytest
from ninja import Schema

from ninja_extra import api_controller, route
from ninja_extra.testing import TestAsyncClient, TestClient


@api_controller("", tags=["Users"])
class UserController:
    @route.get("/users")
    def list_users(self):
        return [
            {
                "first_name": "Ninja Extra",
                "username": "django_ninja",
                "email": "john.doe@gmail.com",
            }
        ]


class TestClientWithController:
    def test_get_users(self):
        client = TestClient(UserController)
        response = client.get("/users")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list) and len(body) == 1
        assert body[0] == {
            "first_name": "Ninja Extra",
            "username": "django_ninja",
            "email": "john.doe@gmail.com",
        }


@api_controller("", tags=["Math"])
class MyMathController:
    @route.get("/add")
    async def add(self, a: int, b: int):
        """Return a - b to mirror the docs example."""
        return {"result": a - b}


class TestAsyncClientWithController:
    @pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
    @pytest.mark.asyncio
    async def test_add_async(self):
        client = TestAsyncClient(MyMathController)
        response = await client.get("/add", query={"a": 3, "b": 5})
        assert response.status_code == 200
        assert response.json() == {"result": -2}


@api_controller("/api", tags=["Users"])
class PrefixedUserController:
    @route.get("/users")
    def list_users(self):
        return [
            {
                "first_name": "Ninja Extra",
                "username": "django_ninja",
                "email": "john.doe@gmail.com",
            }
        ]


class TestClientWithPrefixedController:
    def test_get_users_under_prefix(self):
        client = TestClient(PrefixedUserController)
        response = client.get("/users")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list) and len(body) == 1
        assert body[0]["username"] == "django_ninja"


@api_controller("/math", tags=["Math"])
class PrefixedMathController:
    @route.get("/add")
    async def add(self, a: int, b: int):
        return {"result": a + b}


class TestAsyncClientWithPrefixedController:
    @pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
    @pytest.mark.asyncio
    async def test_add_async_under_prefix(self):
        client = TestAsyncClient(PrefixedMathController)
        response = await client.get("/add", query={"a": 3, "b": 5})
        assert response.status_code == 200
        assert response.json() == {"result": 8}


class UserIn(Schema):
    username: str
    email: str


@api_controller("/users/{int:org_id}/", tags=["Users"])
class OrgUsersController:
    @route.post("")
    def create_user(self, org_id: int, user: UserIn):
        return {"id": str(uuid.uuid4()), "org_id": org_id, "username": user.username}


@api_controller("/headers-cookies", tags=["Test"])
class HeaderCookieController:
    @route.get("/check")
    def check_headers_cookies(self, request):
        return {
            "headers": {k.lower(): v for k, v in request.headers.items()},
            "cookies": dict(request.COOKIES),
        }


@api_controller("/headers-cookies-async", tags=["Test"])
class AsyncHeaderCookieController:
    @route.get("/check")
    async def check_headers_cookies(self, request):
        return {
            "headers": {k.lower(): v for k, v in request.headers.items()},
            "cookies": dict(request.COOKIES),
        }


class TestClientWithParamPrefixedController:
    def test_create_user_under_param_prefix(self):
        client = TestClient(OrgUsersController)
        response = client.post(
            "/users/123/", json={"username": "jane", "email": "jane@example.com"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["org_id"] == 123
        assert body["username"] == "jane"
        assert "id" in body


class TestClientWithHeadersAndCookies:
    def test_headers_and_cookies_passed_to_controller(self):
        headers = {"X-Test-Header": "test-value"}
        cookies = {"test-cookie": "cookie-value"}
        client = TestClient(HeaderCookieController, headers=headers, COOKIES=cookies)
        response = client.get("/check")
        assert response.status_code == 200
        data = response.json()
        # Django headers are usually capitalized and prefixed with HTTP_ in META,
        # but request.headers (HttpHeaders) allows case-insensitive access.
        # Ninja's TestClient puts them in META as HTTP_X_TEST_HEADER.
        assert data["headers"]["x-test-header"] == "test-value"
        assert data["cookies"]["test-cookie"] == "cookie-value"

    @pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
    @pytest.mark.asyncio
    async def test_async_headers_and_cookies_passed_to_controller(self):
        headers = {"X-Async-Test-Header": "async-test-value"}
        cookies = {"async-test-cookie": "async-cookie-value"}
        client = TestAsyncClient(AsyncHeaderCookieController, headers=headers, COOKIES=cookies)
        response = await client.get("/check")
        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["x-async-test-header"] == "async-test-value"
        assert data["cookies"]["async-test-cookie"] == "async-cookie-value"

import uuid

import django
import pytest

from ninja_extra import api_controller, http_get, throttle
from ninja_extra.testing import TestAsyncClient, TestClient
from ninja_extra.throttling import (
    AnonRateThrottle,
    DynamicRateThrottle,
    UserRateThrottle,
)

from .sample_models import ThrottlingMockUser, User3SecRateThrottle


@api_controller
class ThrottledController:
    @http_get(
        "/throttle_user_default",
        throttle=[AnonRateThrottle("2/sec"), UserRateThrottle("3/sec")],
    )
    def throttle_user_default(self, request):
        return "foo"

    @http_get("/throttle_user_3_sec")
    @throttle(User3SecRateThrottle)
    def throttle_user_3_sec(self, request):
        return "foo"

    @http_get("/dynamic_throttling_scope")
    @throttle(DynamicRateThrottle("3/min"))
    def dynamic_throttling_scope(self, request):
        return "foo"


class TestThrottledController:
    def setup_method(self):
        self.user = ThrottlingMockUser("Ninja")
        self.user.set_id(uuid.uuid4())

    def test_requests_are_throttled_using_default_user_scope(self):
        cloned_controller = api_controller(
            type("ThrottledController", (ThrottledController,), {})
        )
        client = TestClient(cloned_controller)

        for _dummy in range(4):
            response = client.get("/throttle_user_default", user=self.user)
        assert response.status_code == 429

    def test_requests_are_throttled(self):
        """
        Ensure request rate is limited
        """
        client = TestClient(ThrottledController)

        for _dummy in range(4):
            response = client.get("/throttle_user_3_sec", user=self.user)
        assert response.status_code == 429

    def test_request_throttling_for_dynamic_throttling(self, monkeypatch):
        # for authenticated user
        client = TestClient(ThrottledController)

        for _dummy in range(4):
            response = client.get("/dynamic_throttling_scope", user=self.user)
        assert response.status_code == 429
        # for unauthenticated user

        for _dummy in range(4):
            client.get("/dynamic_throttling_scope")
        assert response.status_code == 429


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
async def test_async_controller_throttling(monkeypatch):
    @api_controller
    class ThrottledControllerAsync:
        @http_get(
            "/throttle_user_default_async",
            throttle=[AnonRateThrottle("2/sec"), UserRateThrottle("3/sec")],
        )
        async def throttle_user_default_async(self, request):
            return "foo"

        @http_get("/throttle_user_3_sec_async")
        @throttle(User3SecRateThrottle)
        async def throttle_user_3_sec_async(self, request):
            return "foo"

    def create_user():
        _user = ThrottlingMockUser("Ninja")
        _user.set_id(uuid.uuid4())
        return _user

    client_async = TestAsyncClient(ThrottledControllerAsync)

    user = create_user()

    for _dummy in range(4):
        response = await client_async.get("/throttle_user_default_async", user=user)
    assert response.status_code == 429

    user = create_user()
    for _idx, _dummy in enumerate(range(4)):
        response = await client_async.get("/throttle_user_3_sec_async", user=user)
    assert response.status_code == 429

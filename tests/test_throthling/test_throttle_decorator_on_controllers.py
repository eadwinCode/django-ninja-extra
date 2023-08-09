import uuid

import django
import pytest

from ninja_extra import api_controller, http_get, throttle
from ninja_extra.conf import settings
from ninja_extra.testing import TestAsyncClient, TestClient
from ninja_extra.throttling import DynamicRateThrottle

from .sample_models import ThrottlingMockUser, User3SecRateThrottle


@api_controller
class ThrottledController:
    @http_get("/throttle_user_default")
    @throttle
    def throttle_user_default(self, request):
        return "foo"

    @http_get("/throttle_user_3_sec")
    @throttle(User3SecRateThrottle)
    def throttle_user_3_sec(self, request):
        return "foo"

    @http_get("/dynamic_throttling_scope")
    @throttle(DynamicRateThrottle, scope="dynamic_scope")
    def dynamic_throttling_scope(self, request):
        return "foo"


client = TestClient(ThrottledController)


class TestThrottledController:
    def setup_method(self):
        self.user = ThrottlingMockUser("Ninja")
        self.user.set_id(uuid.uuid4())

    def test_requests_are_throttled_using_default_user_scope(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(settings, "THROTTLE_RATES", {"user": "3/sec", "anon": "2/sec"})
            for _dummy in range(4):
                response = client.get("/throttle_user_default", user=self.user)
            assert response.status_code == 429

    def test_requests_are_throttled(self):
        """
        Ensure request rate is limited
        """

        for _dummy in range(4):
            response = client.get("/throttle_user_3_sec", user=self.user)
        assert response.status_code == 429

    def test_request_throttling_for_dynamic_throttling(self, monkeypatch):
        # for authenticated user
        with monkeypatch.context() as m:
            m.setattr(settings, "THROTTLE_RATES", {"dynamic_scope": "3/min"})
            for _dummy in range(4):
                response = client.get("/dynamic_throttling_scope", user=self.user)
            assert response.status_code == 429
        # for unauthenticated user
        with monkeypatch.context() as m:
            m.setattr(settings, "THROTTLE_RATES", {"dynamic_scope": "3/min"})
            for _dummy in range(4):
                client.get("/dynamic_throttling_scope")
            assert response.status_code == 429


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
async def test_async_controller_throttling(monkeypatch):
    @api_controller
    class ThrottledControllerAsync:
        @http_get("/throttle_user_default_async")
        @throttle
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

    with monkeypatch.context() as m:
        m.setattr(settings, "THROTTLE_RATES", {"user": "3/sec", "anon": "2/sec"})
        for _dummy in range(4):
            response = await client_async.get("/throttle_user_default_async", user=user)
        assert response.status_code == 429

    user = create_user()
    for _idx, _dummy in enumerate(range(4)):
        response = await client_async.get("/throttle_user_3_sec_async", user=user)
    assert response.status_code == 429

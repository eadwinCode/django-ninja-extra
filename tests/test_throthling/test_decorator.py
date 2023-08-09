import uuid
from contextlib import contextmanager

import django
import pytest
from ninja.testing import TestAsyncClient, TestClient

from ninja_extra import NinjaExtraAPI
from ninja_extra.conf import settings
from ninja_extra.throttling import DynamicRateThrottle, throttle

from .sample_models import (
    ThrottlingMockUser,
    User3MinRateThrottle,
    User3SecRateThrottle,
    User6MinRateThrottle,
)

api = NinjaExtraAPI(urls_namespace="throttle_decorator_1")


@api.get("/throttle_user_default")
@throttle
def throttle_user_default(request):
    return "foo"


@api.get("/throttle_user_3_sec")
@throttle(User3SecRateThrottle)
def throttle_user_3_sec(request):
    return "foo"


@api.get("/throttling_multiple_throttle")
@throttle(User3SecRateThrottle, User6MinRateThrottle)
def throttling_multiple_throttle(request):
    return "foo"


@api.get("/throttle_user_3_min")
@throttle(User3MinRateThrottle)
def throttle_user_3_min(request):
    return "foo"


@api.get("/dynamic_throttling_scope")
@throttle(DynamicRateThrottle, scope="dynamic_scope")
def dynamic_throttling_scope(request):
    return "foo"


client = TestClient(api)


class TestThrottling:
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

    @contextmanager
    def set_throttle_timer(self, monkeypatch, *throttling_classes, value=0):
        """
        Explicitly set the timer, overriding time.time()
        """
        with monkeypatch.context() as m:
            for throttling_class in throttling_classes:
                m.setattr(throttling_class, "timer", lambda self: value)
            yield m

    def test_request_throttling_expires(self, monkeypatch):
        """
        Ensure request rate is limited for a limited duration only
        """
        with self.set_throttle_timer(monkeypatch, User3SecRateThrottle, value=0):
            for _dummy in range(4):
                response = client.get("/throttle_user_3_sec", user=self.user)
            assert response.status_code == 429

        # Advance the timer by one second
        with self.set_throttle_timer(monkeypatch, User3SecRateThrottle, value=1):
            response = client.get("/throttle_user_3_sec", user=self.user)
            assert response.status_code == 200

    def ensure_is_throttled(self, path, expect):
        for _dummy in range(3):
            client.get(f"/{path}", user=self.user)

        user = ThrottlingMockUser("NinjaNew")
        user.set_id(uuid.uuid4())

        response = client.get(f"/{path}", user=user)
        assert response.status_code == expect

    def test_request_throttling_is_per_user(self):
        """
        Ensure request rate is only limited per user, not globally for
        PerUserThrottles
        """
        self.ensure_is_throttled("throttle_user_3_sec", 200)

    def test_request_throttling_multiple_throttles(self, monkeypatch):
        """
        Ensure all throttle classes see each request even when the request is
        already being throttled
        """
        with self.set_throttle_timer(
            monkeypatch, User3SecRateThrottle, User6MinRateThrottle, value=0
        ):
            for _dummy in range(4):
                response = client.get("throttling_multiple_throttle", user=self.user)
            assert response.status_code == 429
            assert int(response["retry-after"]) == 1

        # At this point our client made 4 requests (one was throttled) in a
        # second. If we advance the timer by one additional second, the client
        # should be allowed to make 2 more before being throttled by the 2nd
        # throttle class, which has a limit of 6 per minute.
        with self.set_throttle_timer(
            monkeypatch, User3SecRateThrottle, User6MinRateThrottle, value=1
        ):
            for _dummy in range(2):
                response = client.get("throttling_multiple_throttle", user=self.user)
                assert response.status_code == 200

            response = client.get("throttling_multiple_throttle", user=self.user)
            assert response.status_code == 429
            assert int(response["retry-after"]) == 59

        # Just to make sure check again after two more seconds.
        with self.set_throttle_timer(
            monkeypatch, User3SecRateThrottle, User6MinRateThrottle, value=2
        ):
            response = client.get("throttling_multiple_throttle", user=self.user)
            assert response.status_code == 429
            assert int(response["retry-after"]) == 58

    def test_throttle_rate_change_negative(self, monkeypatch):
        with self.set_throttle_timer(
            monkeypatch, User3SecRateThrottle, User6MinRateThrottle, value=0
        ):
            for _dummy in range(24):
                response = client.get("/throttling_multiple_throttle", user=self.user)
            assert response.status_code == 429
            assert int(response._response["retry-after"]) == 60

            previous_rate = User3SecRateThrottle.rate
            try:
                User3SecRateThrottle.rate = "1/sec"

                for _dummy in range(24):
                    response = client.get(
                        "/throttling_multiple_throttle", user=self.user
                    )

                assert response.status_code == 429
                assert int(response._response["retry-after"]) == 60
            finally:
                # reset
                User3SecRateThrottle.rate = previous_rate

    def ensure_response_header_contains_proper_throttle_field(
        self, path, monkeypatch, *throttling_class, expected_headers=()
    ):
        """
        Ensure the response returns an Retry-After field with status and next attributes
        set properly.
        """
        for timer, expect in expected_headers:
            with self.set_throttle_timer(monkeypatch, *throttling_class, value=timer):
                response = client.get(f"/{path}", user=self.user)
                if expect is not None:
                    assert response._response["Retry-After"] == expect
                else:
                    assert "Retry-After" not in response._response

    def test_seconds_fields(self, monkeypatch):
        """
        Ensure for second based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(
            "throttle_user_3_sec",
            monkeypatch,
            User3SecRateThrottle,
            expected_headers=((0, None), (0, None), (0, None), (0, "1")),
        )

    def test_minutes_fields(self, monkeypatch):
        """
        Ensure for minute based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(
            "throttle_user_3_min",
            monkeypatch,
            User3MinRateThrottle,
            expected_headers=((0, None), (0, None), (0, None), (0, "60")),
        )

    def test_next_rate_remains_constant_if_followed(self, monkeypatch):
        """
        If a client follows the recommended next request rate,
        the throttling rate should stay constant.
        """
        self.ensure_response_header_contains_proper_throttle_field(
            "throttle_user_3_min",
            monkeypatch,
            User3MinRateThrottle,
            expected_headers=(
                (0, None),
                (20, None),
                (40, None),
                (60, None),
                (80, None),
            ),
        )

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
                response = client.get("/dynamic_throttling_scope")
            assert response.status_code == 429


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
async def test_async_throttling(monkeypatch):
    api_async = NinjaExtraAPI(urls_namespace="decorator_async_1")

    @api_async.get("/throttle_user_default_async")
    @throttle
    async def throttle_user_default_async(request):
        return "foo"

    @api_async.get("/throttle_user_3_sec_async")
    @throttle(User3SecRateThrottle)
    async def throttle_user_3_sec_async(request):
        return "foo"

    @api_async.get("/throttle_user_3_min_async")
    @throttle(User3MinRateThrottle)
    async def throttle_user_3_min_async(request):
        return "foo"

    def create_user():
        _user = ThrottlingMockUser("Ninja")
        _user.set_id(uuid.uuid4())
        return _user

    client_async = TestAsyncClient(api_async)

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

    user = create_user()
    for _idx, _dummy in enumerate(range(4)):
        response = await client_async.get("/throttle_user_3_min_async", user=user)
    assert response.status_code == 429

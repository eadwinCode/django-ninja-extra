import uuid

import pytest

from ninja_extra import ControllerBase, api_controller, http_get
from ninja_extra.conf import settings
from ninja_extra.constants import THROTTLED_FUNCTION
from ninja_extra.testing import TestClient
from ninja_extra.throttling import DynamicRateThrottle, throttle

from .sample_models import ThrottlingMockUser


@api_controller("/throttled-controller")
class ThrottlingControllerSample(ControllerBase):
    throttling_classes = [
        DynamicRateThrottle,
    ]
    throttling_init_kwargs = {"scope": "dynamic_scope"}

    @http_get("/endpoint_1")
    @throttle
    def endpoint_1(self, request):
        return "foo"

    @http_get("/endpoint_2")
    def endpoint_2(self, request):
        return "foo"

    @http_get("/endpoint_3")
    def endpoint_3(self, request):
        return "foo"


client = TestClient(ThrottlingControllerSample)


class TestThrottlingControllerSample:
    def setup_method(self):
        self.user = ThrottlingMockUser("Ninja")
        self.user.set_id(uuid.uuid4())

    def test_all_controller_func_has_throttling_decorator(self):
        api_controller_instance = ThrottlingControllerSample.get_api_controller()
        for (
            _,
            func,
        ) in api_controller_instance._controller_class_route_functions.items():
            assert THROTTLED_FUNCTION in func.route.view_func.__dict__

    def test_controller_endpoint_throttle_override(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(settings, "THROTTLE_RATES", {"user": "10/sec", "anon": "2/sec"})
            for _dummy in range(11):
                response = client.get("/endpoint_1", user=self.user)
            assert response.status_code == 429

    @pytest.mark.parametrize(
        "endpoint, time_out",
        [
            ("/endpoint_1", 10),
            ("/endpoint_2", 5),
            ("/endpoint_3", 5),
        ],
    )
    def test_controller_endpoints_throttling(self, endpoint, time_out, monkeypatch):
        # for authenticated user
        with monkeypatch.context() as m:
            m.setattr(
                settings,
                "THROTTLE_RATES",
                {"dynamic_scope": "5/min", "user": "10/sec", "anon": "10/sec"},
            )
            for _dummy in range(time_out + 1):
                response = client.get(endpoint, user=self.user)
            assert response.status_code == 429

        # for unauthenticated user
        with monkeypatch.context() as m:
            m.setattr(
                settings,
                "THROTTLE_RATES",
                {"dynamic_scope": "5/min", "user": "10/sec", "anon": "10/sec"},
            )
            for _dummy in range(time_out + 1):
                response = client.get(endpoint)
            assert response.status_code == 429

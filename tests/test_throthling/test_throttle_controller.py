import uuid

import pytest
from ninja.constants import NOT_SET

from ninja_extra import ControllerBase, api_controller, http_get
from ninja_extra.testing import TestClient
from ninja_extra.throttling import (
    AnonRateThrottle,
    DynamicRateThrottle,
    UserRateThrottle,
)

from .sample_models import ThrottlingMockUser


@api_controller("/throttled-controller")
class ThrottlingControllerSample(ControllerBase):
    throttling_classes = [
        DynamicRateThrottle,
    ]
    throttling_init_kwargs = {"rate": "5/min"}

    @http_get(
        "/endpoint_1", throttle=[AnonRateThrottle("2/sec"), UserRateThrottle("10/sec")]
    )
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
        cloned_controller = api_controller(
            "/throttled-controller", throttle=DynamicRateThrottle(rate="5/min")
        )(type("ThrottlingControllerSample", (ThrottlingControllerSample,), {}))
        api_controller_instance = cloned_controller.get_api_controller()
        for (
            _,
            func,
        ) in api_controller_instance._controller_class_route_functions.items():
            assert func.route.route_params.throttle is not NOT_SET

    def test_controller_endpoint_throttle_override(self):
        cloned_controller = api_controller("/throttled-controller")(
            type("ThrottlingControllerSample", (ThrottlingControllerSample,), {})
        )
        client = TestClient(cloned_controller)

        for _dummy in range(11):
            response = client.get("/endpoint_1", user=self.user)
        assert response.status_code == 429

    @pytest.mark.parametrize(
        "endpoint, time_out",
        [
            ("/endpoint_1", 10),  # applying AnonRate and UserRate
            ("/endpoint_2", 5),  # applying DynamicRate at 5/min
            ("/endpoint_3", 5),  # applying DynamicRate at 5/min
        ],
    )
    def test_controller_endpoints_throttling(self, endpoint, time_out):
        # for authenticated user
        for _dummy in range(time_out + 1):
            response = client.get(endpoint, user=self.user)
        assert response.status_code == 429

        # for unauthenticated user
        for _dummy in range(time_out + 1):
            response = client.get(endpoint)
        assert response.status_code == 429

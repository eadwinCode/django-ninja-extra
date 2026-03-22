"""Test that API-level throttle is inherited by controller routes.

Mirrors test_auth_inheritance.py but for throttle settings on NinjaExtraAPI.
"""

from ninja.testing import TestClient
from ninja.throttling import BaseThrottle

from ninja_extra import ControllerBase, NinjaExtraAPI, api_controller, http_get


class AlwaysThrottle(BaseThrottle):
    """Throttle that always denies requests."""

    def allow_request(self, request):
        return False

    def wait(self):
        return 30


class NeverThrottle(BaseThrottle):
    """Throttle that always allows requests."""

    def allow_request(self, request):
        return True

    def wait(self):
        return None


def test_controller_inherits_api_throttle(reflect_context):
    """Controller routes with no explicit throttle should inherit NinjaExtraAPI(throttle=...)."""

    @api_controller("/throttled")
    class ThrottledController(ControllerBase):
        @http_get("/data")
        def get_data(self):
            return {"ok": True}

    api = NinjaExtraAPI(throttle=AlwaysThrottle())
    api.register_controllers(ThrottledController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert op.throttle_objects, (
                    "Controller operation should have inherited API throttle"
                )
                assert isinstance(op.throttle_objects[0], AlwaysThrottle)

    client = TestClient(api)
    response = client.get("/throttled/data")
    assert response.status_code == 429


def test_controller_inherits_api_throttle_list(reflect_context):
    """API throttle passed as a list should be inherited correctly."""

    @api_controller("/multi-throttled")
    class MultiThrottledController(ControllerBase):
        @http_get("/data")
        def get_data(self):
            return {"ok": True}

    throttles = [NeverThrottle(), AlwaysThrottle()]
    api = NinjaExtraAPI(throttle=throttles)
    api.register_controllers(MultiThrottledController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert len(op.throttle_objects) == 2
                assert isinstance(op.throttle_objects[0], NeverThrottle)
                assert isinstance(op.throttle_objects[1], AlwaysThrottle)

    client = TestClient(api)
    response = client.get("/multi-throttled/data")
    assert response.status_code == 429


def test_controller_explicit_throttle_not_overridden(reflect_context):
    """Controller with its own throttle should NOT be overridden by API throttle."""

    @api_controller("/ctrl-throttled", throttle=NeverThrottle())
    class CtrlThrottledController(ControllerBase):
        @http_get("/data")
        def get_data(self):
            return {"ok": True}

    api = NinjaExtraAPI(throttle=AlwaysThrottle())
    api.register_controllers(CtrlThrottledController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert len(op.throttle_objects) == 1
                assert isinstance(op.throttle_objects[0], NeverThrottle), (
                    "Controller-level throttle should not be overridden by API throttle"
                )

    client = TestClient(api)
    response = client.get("/ctrl-throttled/data")
    assert response.status_code == 200


def test_controller_without_api_throttle(reflect_context):
    """When API has no throttle, controller operations should have no throttle objects."""

    @api_controller("/unthrottled")
    class UnthrottledController(ControllerBase):
        @http_get("/ping")
        def ping(self):
            return {"ok": True}

    api = NinjaExtraAPI()
    api.register_controllers(UnthrottledController)

    for br in api._controller_routers:
        for pv in br.path_operations.values():
            for op in pv.operations:
                assert op.throttle_objects == [], (
                    "Operations should have no throttle when API has no throttle"
                )

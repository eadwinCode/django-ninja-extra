import typing as t
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from ninja.testing import TestClient

from ninja_extra import NinjaExtraAPI, api_controller, http_get
from ninja_extra.controllers.registry import controller_registry
from ninja_extra.controllers.utils import get_api_controller


@api_controller
class SomeAPIController:
    @http_get("/example")
    def example(self):
        pass


class InvalidSomeAPIController:
    pass


api = NinjaExtraAPI()
api.register_controllers(SomeAPIController)


@api.get("/global")
def global_op(request):
    pass


def test_api_instance():
    assert len(api._routers) == 2  # default + extra
    for _path, rtr in api._routers:
        for path_ops in rtr.path_operations.values():
            for op in path_ops.operations:
                assert op.api is api


def test_api_auto_discover_controller():
    ninja_extra_api = NinjaExtraAPI()
    assert str(SomeAPIController) in controller_registry.get_controllers()

    with mock.patch.object(
        ninja_extra_api, "register_controllers"
    ) as mock_register_controllers:
        ninja_extra_api.auto_discover_controllers()
    assert mock_register_controllers.call_count == 2

    assert (
        "<class 'ninja_extra.controllers.base.EventController'>"
        in controller_registry.get_controllers()
    )

    @api_controller
    class SomeAPI2Controller:
        auto_import = False

    assert str(SomeAPI2Controller) not in controller_registry.get_controllers()


def test_api_register_controller_works(reflect_context):
    @api_controller("/another")
    class AnotherAPIController:
        @http_get("/example")
        def example(self):
            return self.create_response("Create Response Works")

    ninja_extra_api = NinjaExtraAPI()
    assert len(ninja_extra_api._routers) == 1
    assert not get_api_controller(AnotherAPIController).is_registered(ninja_extra_api)

    ninja_extra_api.register_controllers(AnotherAPIController)
    assert get_api_controller(AnotherAPIController).is_registered(ninja_extra_api)
    assert len(ninja_extra_api._routers) == 2

    assert "/another" in dict(ninja_extra_api._routers)

    with pytest.raises(ImproperlyConfigured) as ex:
        ninja_extra_api.register_controllers(InvalidSomeAPIController)

    assert "class is not a controller" in str(ex.value)
    client = TestClient(ninja_extra_api)
    res = client.get("/another/example")
    assert res.status_code == 200
    assert res.content == b'"Create Response Works"'


def test_same_controller_two_apis_works():
    @api_controller("/ping")
    class P:
        @http_get("")
        def ping(self):
            return {"ok": True}

    a = NinjaExtraAPI(urls_namespace="a")
    b = NinjaExtraAPI(urls_namespace="b")

    a.register_controllers(P)
    b.register_controllers(P)  # triggers clone path

    assert TestClient(a).get("/ping").json() == {"ok": True}
    assert TestClient(b).get("/ping").json() == {"ok": True}


def test_openapi_schema_params_are_correct_on_two_apis():
    @api_controller("/")
    class ItemsController:
        @http_get("/items_1")
        def items_1(self, ordering: t.Optional[str] = None):
            return {"ok": True}

    # Two independent API instances
    api_a = NinjaExtraAPI(title="A")
    api_b = NinjaExtraAPI(title="B")

    api_a.register_controllers(ItemsController)
    api_b.register_controllers(ItemsController)

    expected_params = [
        {
            "in": "query",
            "name": "ordering",
            "required": False,
            "schema": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "title": "Ordering",
            },
        }
    ]

    # Check API A schema
    schema_a = api_a.get_openapi_schema()
    op_a = schema_a["paths"]["/api/items_1"]["get"]
    assert op_a["parameters"] == expected_params

    # Check API B schema
    schema_b = api_b.get_openapi_schema()
    op_b = schema_b["paths"]["/api/items_1"]["get"]
    assert op_b["parameters"] == expected_params

    # (Optional) also confirm the route actually works on both APIs
    ca = TestClient(api_a)
    cb = TestClient(api_b)
    assert ca.get("/items_1").status_code == 200
    assert cb.get("/items_1").status_code == 200


def test_clone_is_cached_per_api_not_recreated():
    """Register the same original class twice on the same API -> reuse cached clone, no new routers."""

    @api_controller("/x")
    class X:
        @http_get("")
        def ok(self):
            return {"ok": True}

    a = NinjaExtraAPI(urls_namespace="a")
    b = NinjaExtraAPI(urls_namespace="b")

    # Mount on A (original)
    a.register_controllers(X)
    # Mount on B (clone)
    b.register_controllers(X)
    # Re-register same original on B (should reuse the cached clone; no new routers added)
    before = len(b._routers)
    b.register_controllers(X)
    after = len(b._routers)
    assert before == after

    # Optional: ensure path exists and works
    assert TestClient(b).get("/x").json() == {"ok": True}

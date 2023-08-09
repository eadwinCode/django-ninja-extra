from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

from ninja_extra import NinjaExtraAPI, api_controller, http_get
from ninja_extra.controllers.registry import ControllerRegistry


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
    assert str(SomeAPIController) in ControllerRegistry.get_controllers()

    with mock.patch.object(
        ninja_extra_api, "register_controllers"
    ) as mock_register_controllers:
        ninja_extra_api.auto_discover_controllers()
    assert mock_register_controllers.call_count == 2
    assert "<class 'abc.EventController'>" in ControllerRegistry.get_controllers()

    @api_controller
    class SomeAPI2Controller:
        auto_import = False

    assert str(SomeAPI2Controller) not in ControllerRegistry.get_controllers()


def test_api_register_controller_works():
    @api_controller("/another")
    class AnotherAPIController:
        @http_get("/example")
        def example(self):
            pass

    ninja_extra_api = NinjaExtraAPI()
    assert len(ninja_extra_api._routers) == 1
    assert not AnotherAPIController.get_api_controller().registered

    ninja_extra_api.register_controllers(AnotherAPIController)
    assert AnotherAPIController.get_api_controller().registered
    assert len(ninja_extra_api._routers) == 2

    assert "/another" in dict(ninja_extra_api._routers)

    with pytest.raises(ImproperlyConfigured) as ex:
        ninja_extra_api.register_controllers(InvalidSomeAPIController)

    assert "class is not a controller" in str(ex.value)

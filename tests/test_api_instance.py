from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

from ninja_extra import APIController, NinjaExtraAPI, route, router
from ninja_extra.controllers.router import ControllerRegistry


@router("")
class SomeAPIController(APIController):
    @route.get("/example")
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
    for path, rtr in api._routers:
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
    assert (
        "<class 'tests.controllers.EventController'>"
        in ControllerRegistry.get_controllers()
    )

    @router("")
    class SomeAPI2Controller(SomeAPIController):
        auto_import = False

    assert str(SomeAPI2Controller) not in ControllerRegistry.get_controllers()


def test_api_register_controller_works():
    @router("/another")
    class AnotherAPIController(APIController):
        @route.get("/example")
        def example(self):
            pass

    ninja_extra_api = NinjaExtraAPI()
    assert len(ninja_extra_api._routers) == 1
    assert not AnotherAPIController.registered

    ninja_extra_api.register_controllers(AnotherAPIController)
    assert AnotherAPIController.registered
    assert len(ninja_extra_api._routers) == 2

    assert "/another" in {k: v for k, v in ninja_extra_api._routers}

    with pytest.raises(ImproperlyConfigured) as ex:
        ninja_extra_api.register_controllers(InvalidSomeAPIController)

    assert "class is not a controller" in str(ex.value)

from unittest.mock import Mock, patch

import django
import pytest
from django.contrib.auth.models import Group

from ninja_extra import (
    NinjaExtraAPI,
    api_controller,
    exceptions,
    http_get,
    testing,
)
from ninja_extra.controllers import ControllerBase, RouteContext, RouteFunction
from ninja_extra.controllers.base import (
    APIController,
    MissingAPIControllerDecoratorException,
    get_route_functions,
)
from ninja_extra.helper import get_route_function
from ninja_extra.permissions.common import AllowAny

from .utils import AsyncFakeAuth, FakeAuth


@api_controller
class SomeController:
    pass


@api_controller
class Some2Controller(ControllerBase):
    pass


@api_controller
class SomeControllerWithInject:
    def __init__(self, a: str):
        pass


@api_controller
class SomeControllerWithRoute:
    @http_get("/example")
    def example(self):
        pass

    @http_get("/example/{ex_id}")
    def example2(self, ex_id: str):
        return self.create_response({"detail": ex_id}, status_code=302)

    @http_get("/example/{ex_id}/ok")
    def example_with_ok_response(self, ex_id: str):
        return {"detail": ex_id}

    @http_get("/example/{ex_id}/id")
    def example_with_id_response(self, ex_id: str):
        return {"id": ex_id}

    @http_get("/example/{uuid:ex_id}/generic")
    def example_with_id_uuid_response(self, ex_id: str):
        return {"id": ex_id}


@api_controller("", tags=["new tag"])
class DisableAutoImportController:
    auto_import = False  # disable auto_import of the controller


class TestAPIController:
    def test_api_controller_as_decorator(self):
        controller_type = api_controller("prefix", tags="new_tag", auth=FakeAuth())(
            type("Any", (), {})
        )
        api_controller_instance = controller_type.get_api_controller()

        assert not api_controller_instance.has_auth_async
        assert not api_controller_instance._prefix_has_route_param
        assert api_controller_instance.prefix == "prefix"
        assert api_controller_instance.tags == ["new_tag"]
        assert api_controller_instance.permission_classes == [AllowAny]

        controller_type = api_controller()(controller_type)
        api_controller_instance = controller_type.get_api_controller()
        assert api_controller_instance.prefix == ""
        assert api_controller_instance.tags == ["any"]
        assert "abc" in SomeController.__module__
        assert "tests.test_controller" in Some2Controller.__module__
        assert Some2Controller.get_api_controller()

    def test_controller_get_api_controller_raise_exception(self):
        class BController(ControllerBase):
            pass

        with pytest.raises(MissingAPIControllerDecoratorException):
            BController.get_api_controller()

    def test_api_controller_prefix_with_parameter(self):
        @api_controller("/{int:organisation_id}")
        class UsersController:
            @http_get("")
            def example_with_id_response(self, organisation_id: int):
                return {"organisation_id": organisation_id}

        _api_controller: APIController = UsersController.get_api_controller()
        assert _api_controller._prefix_has_route_param

        client = testing.TestClient(UsersController)
        response = client.get("452")

        assert response.json() == {"organisation_id": 452}
        assert [("", _api_controller)] == _api_controller.build_routers()

    def test_controller_should_have_preset_properties(self):
        api = NinjaExtraAPI()
        _api_controller = SomeController.get_api_controller()
        assert _api_controller.tags == ["some"]
        assert _api_controller._path_operations == {}
        assert _api_controller.permission_classes == [AllowAny]
        assert SomeController.api is None
        assert _api_controller.registered is False
        assert ControllerBase in SomeController.__bases__

        api.register_controllers(SomeController)
        assert _api_controller.registered

    def test_controller_should_wrap_with_inject(self):
        assert not hasattr(SomeController.__init__, "__bindings__")
        assert hasattr(SomeControllerWithInject.__init__, "__bindings__")

    def test_controller_should_have_path_operation_list(self):
        _api_controller = SomeControllerWithRoute.get_api_controller()
        assert len(_api_controller._path_operations) == 5

        route_function: RouteFunction = get_route_function(
            SomeControllerWithRoute().example
        )
        path_view = _api_controller._path_operations.get(str(route_function))
        assert path_view, "route doesn't exist in controller"
        assert len(path_view.operations) == 1

        operation = path_view.operations[0]
        assert operation.methods == route_function.route.route_params.methods
        assert operation.operation_id == route_function.route.route_params.operation_id

    def test_get_route_function_should_return_instance_route_definitions(self):
        for route_definition in get_route_functions(SomeControllerWithRoute):
            assert isinstance(route_definition, RouteFunction)

    def test_compute_api_route_function_works(self):
        @api_controller()
        class AnyClassTypeWithRoute:
            @http_get("/example")
            def example(self):
                pass

        api_controller_instance = AnyClassTypeWithRoute.get_api_controller()
        assert len(api_controller_instance.path_operations) == 1
        route_function = get_route_function(AnyClassTypeWithRoute().example)
        path_view = api_controller_instance.path_operations.get(str(route_function))
        assert path_view

    @pytest.mark.django_db
    def test_controller_base_get_object_or_exception_works(self):
        group_instance = Group.objects.create(name="_groupowner")

        controller_object = SomeController()
        context = RouteContext(request=Mock(), permission_classes=[AllowAny])
        controller_object.context = context
        with patch.object(
            AllowAny, "has_object_permission", return_value=True
        ) as c_cop:
            group = controller_object.get_object_or_exception(
                Group, id=group_instance.id
            )
            c_cop.assert_called()
            assert group == group_instance

        with pytest.raises(Exception) as ex:
            controller_object.get_object_or_exception(Group, id=1000)
            assert isinstance(ex, exceptions.NotFound)

        with pytest.raises(Exception) as ex:
            with patch.object(AllowAny, "has_object_permission", return_value=False):
                controller_object.get_object_or_exception(Group, id=group_instance.id)
                assert isinstance(ex, exceptions.PermissionDenied)

    @pytest.mark.django_db
    def test_controller_base_get_object_or_none_works(self):
        group_instance = Group.objects.create(name="_groupowner2")

        controller_object = SomeController()
        context = RouteContext(request=Mock(), permission_classes=[AllowAny])
        controller_object.context = context
        with patch.object(
            AllowAny, "has_object_permission", return_value=True
        ) as c_cop:
            group = controller_object.get_object_or_none(Group, id=group_instance.id)
            c_cop.assert_called()
            assert group == group_instance

        assert controller_object.get_object_or_none(Group, id=1000) is None

        with pytest.raises(Exception) as ex:
            with patch.object(AllowAny, "has_object_permission", return_value=False):
                controller_object.get_object_or_none(Group, id=group_instance.id)
                assert isinstance(ex, exceptions.PermissionDenied)


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
def test_async_controller():
    api_controller_decorator = api_controller(
        "prefix", tags="any_Tag", auth=AsyncFakeAuth()
    )

    with pytest.raises(Exception) as ex:

        @api_controller_decorator
        class NonAsyncRouteInControllerWithAsyncAuth:
            @http_get("/example")
            def example(self):
                pass

    assert "NonAsyncRouteInControllerWithAsyncAuth" in str(ex) and "example" in str(ex)

    @api_controller_decorator
    class AsyncRouteInControllerWithAsyncAuth:
        @http_get("/example")
        async def example(self):
            pass

    example_route_function = get_route_function(
        AsyncRouteInControllerWithAsyncAuth().example
    )
    assert AsyncRouteInControllerWithAsyncAuth.get_api_controller().has_auth_async
    assert isinstance(
        example_route_function.operation.auth_callbacks[0],
        AsyncFakeAuth,
    )

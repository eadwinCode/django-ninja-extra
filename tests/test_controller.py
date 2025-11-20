from unittest.mock import Mock, patch

import django
import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

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


@api_controller
class SomeControllerWithSingleRoute:
    @http_get("/example")
    def example(self):
        pass


@api_controller(append_unique_op_id=False)
class SomeControllerWithoutUniqueSuffix:
    @http_get("/example")
    def example(self):
        pass


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
        assert "ninja_extra.controllers.base" in SomeController.__module__
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

    def test_controller_should_append_unique_op_id_to_operation_id(self):
        _api_controller = SomeControllerWithSingleRoute.get_api_controller()
        controller_name = (
            str(_api_controller.controller_class.__name__)
            .lower()
            .replace("controller", "")
        )
        route_view_func_name: RouteFunction = get_route_function(
            SomeControllerWithRoute().example
        ).route.view_func.__name__

        operation_id = (
            _api_controller._path_operations.get("/example").operations[0].operation_id
        )
        raw_operation_id = "_".join(operation_id.split("_")[:-1])
        op_id_postfix = operation_id.split("_")[-1]

        assert raw_operation_id == f"{controller_name}_{route_view_func_name}"
        assert len(op_id_postfix) == 8

    def test_controller_should_not_add_unique_suffix_following_params(self):
        _api_controller = SomeControllerWithoutUniqueSuffix.get_api_controller()
        controller_name = (
            str(_api_controller.controller_class.__name__)
            .lower()
            .replace("controller", "")
        )
        route_view_func_name: RouteFunction = get_route_function(
            SomeControllerWithRoute().example
        ).route.view_func.__name__

        operation_id = (
            _api_controller._path_operations.get("/example").operations[0].operation_id
        )

        assert operation_id == f"{controller_name}_{route_view_func_name}"

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
        context = RouteContext(
            request=Mock(),
            permission_classes=[AllowAny],
            response=None,
            args=[],
            kwargs={},
            api=None,
            view_signature=None,
        )
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

    @pytest.mark.skipif(django.VERSION < (4, 2), reason="requires django 4.2 or higher")
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_controller_base_aget_object_or_exception_works(self):
        group_instance = await Group.objects.acreate(name="_async_groupowner")

        controller_object = SomeController()
        context = RouteContext(request=Mock(), permission_classes=[AllowAny])
        controller_object.context = context
        with patch.object(
            AllowAny, "has_object_permission", return_value=True
        ) as c_cop:
            group = await controller_object.aget_object_or_exception(
                Group, id=group_instance.id
            )
            c_cop.assert_called()
            assert group == group_instance

        with pytest.raises(Exception) as ex:
            await controller_object.aget_object_or_exception(Group, id=1000)
            assert isinstance(ex, exceptions.NotFound)

        with pytest.raises(Exception) as ex:
            with patch.object(AllowAny, "has_object_permission", return_value=False):
                await controller_object.aget_object_or_exception(
                    Group, id=group_instance.id
                )
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

    @pytest.mark.skipif(django.VERSION < (4, 2), reason="requires django 4.2 or higher")
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_controller_base_aget_object_or_none_works(self):
        group_instance = await Group.objects.acreate(name="_async_groupowner2")

        controller_object = SomeController()
        context = RouteContext(request=Mock(), permission_classes=[AllowAny])
        controller_object.context = context
        with patch.object(
            AllowAny, "has_object_permission", return_value=True
        ) as c_cop:
            group = await controller_object.aget_object_or_none(
                Group, id=group_instance.id
            )
            c_cop.assert_called()
            assert group == group_instance

        assert await controller_object.aget_object_or_none(Group, id=1000) is None

        with pytest.raises(Exception) as ex:
            with patch.object(AllowAny, "has_object_permission", return_value=False):
                await controller_object.aget_object_or_none(Group, id=group_instance.id)
                assert isinstance(ex, exceptions.PermissionDenied)


def test_controller_registration_through_string():
    assert DisableAutoImportController.get_api_controller().registered is False

    api = NinjaExtraAPI()
    api.register_controllers("tests.test_controller.DisableAutoImportController")

    assert DisableAutoImportController.get_api_controller().registered


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


def test_namespaced_controller_list(client):
    response = client.get("/api/inventory-items")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "sample"}]
    assert reverse("api-1.0.0:inventory:inventory-item-list") == "/api/inventory-items"


def test_namespaced_controller_detail(client):
    response = client.get("/api/inventory-items/5")
    assert response.status_code == 200
    assert response.json() == {"id": 5, "name": "sample-5"}
    assert reverse("api-1.0.0:inventory:inventory-item-detail", kwargs={"item_id": 5}) == "/api/inventory-items/5"


def test_default_url_name(client):
    assert reverse("api-1.0.0:get_event", kwargs={"id": 5}) == "/api/events/5"

from unittest.mock import Mock

import django
import pytest
from django.contrib.auth.models import AnonymousUser, User

from ninja_extra import APIController, permissions, route, router
from ninja_extra.controllers import AsyncRouteFunction, Route, RouteFunction
from ninja_extra.exceptions import PermissionDenied

anonymous_request = Mock()
anonymous_request.user = AnonymousUser()


@router(
    "permission", permissions=[permissions.IsAuthenticated & permissions.IsAdminUser]
)
class PermissionController(APIController):
    @route.get("/example")
    def example(self):
        return {"message": "OK"}

    @route.get("/example", permissions=[permissions.AllowAny])
    def example_allow_any(self):
        return {"message": "OK"}


class SomeTestController(APIController):
    @route.get("/example")
    def example(self):
        pass

    @route.post("/example")
    def example_post(self):
        pass

    @route.get("/example/{ex_id}")
    def example_get(self, ex_id: str):
        pass

    @route.put("/example/{ex_id}")
    def example_put(self, ex_id: str):
        pass

    @route.delete("/example/{ex_id}")
    def example_delete(self, ex_id: str):
        pass

    @route.generic("/example/list", methods=["POST", "GET"])
    def example_list_create(self, ex_id: str):
        pass


class TestControllerRoutes:
    @pytest.mark.parametrize(
        "path,operation_count",
        [
            ("/example", 2),
            ("/example/{ex_id}", 3),
            ("/example/list", 1),
        ],
    )
    def test_controller_route_build_accurate_operations_list(
        self, path, operation_count
    ):
        path_view = SomeTestController.get_path_operations().get(path)
        assert len(path_view.operations) == operation_count

    def test_controller_route_should_have_an_operation(self):
        for route_func in SomeTestController.get_route_functions():
            path_view = SomeTestController.get_path_operations().get(str(route_func))
            operations = list(
                filter(
                    lambda n: n.operation_id
                    == route_func.route.route_params.operation_id,
                    path_view.operations,
                )
            )
            assert len(operations) == 1
            assert route_func.route.route_params.methods == operations[0].methods

    def test_controller_route_should_right_view_func_type(self):
        assert isinstance(SomeTestController.example, RouteFunction)


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
def test_async_route_function():
    class AsyncSomeTestController(SomeTestController):
        @route.get("/example_async")
        async def example_async(self, ex_id: str):
            pass

    assert isinstance(AsyncSomeTestController.example, RouteFunction)
    assert isinstance(AsyncSomeTestController.example_async, AsyncRouteFunction)


class TestRouteFunction:
    def api_func_with_has_request_param(self, request):
        pass

    def api_func(self):
        pass

    def api_func_with_param(self, example_id: str):
        pass

    async def async_api_func(self):
        pass

    def test_get_required_api_func_signature_return_filtered_signature(self):
        route_function = route.get("")(self.api_func)
        assert not route_function.has_request_param
        sig_inspect, sig_parameter = route_function._get_required_api_func_signature()
        assert len(sig_parameter) == 0

        route_function = route.get("")(self.api_func_with_has_request_param)
        assert route_function.has_request_param
        sig_inspect, sig_parameter = route_function._get_required_api_func_signature()
        assert len(sig_parameter) == 0

        route_function = route.get("")(self.api_func_with_param)
        sig_inspect, sig_parameter = route_function._get_required_api_func_signature()
        assert len(sig_parameter) == 1
        assert str(sig_parameter[0]).replace(" ", "") == "example_id:str"

    def test_from_route_returns_route_function_instance(self):
        route_function = route.get("")(self.api_func)
        assert isinstance(route_function, RouteFunction)

        route_function = route.get("")(self.async_api_func)
        assert isinstance(route_function, AsyncRouteFunction)

    def test_get_controller_init_kwargs(self):
        route_function = route.get("")(self.api_func)
        route_function.controller = Mock()
        route_function.controller.permission_classes = []

        controller_init_kwargs = route_function._get_controller_init_kwargs(
            anonymous_request, "arg1", "arg2", extra="extra"
        )
        assert isinstance(controller_init_kwargs, dict)
        expected_keywords = ("permission_classes", "request", "args", "kwargs")
        for key in expected_keywords:
            assert key in controller_init_kwargs

    def test_get_controller_instance_return_controller_instance(self):
        route_function: RouteFunction = SomeTestController.example
        controller_instance = route_function._get_controller_instance(
            anonymous_request, "arg1", "arg2", extra="extra"
        )
        assert isinstance(controller_instance, SomeTestController)
        assert controller_instance.args == ("arg1", "arg2")
        assert controller_instance.kwargs == {"extra": "extra"}
        assert controller_instance.request == anonymous_request


@pytest.mark.django_db
class TestAPIControllerRoutePermission:
    @classmethod
    def get_real_user_request(cls):
        _request = Mock()
        user = User.objects.create_user(
            username="eadwin",
            email="eadwin@example.com",
            password="password",
            is_staff=True,
        )
        _request.user = user
        return _request

    def test_route_is_protected_by_global_controller_permission(self):
        with pytest.raises(PermissionDenied) as pex:
            PermissionController.example(anonymous_request)
        assert "You do not have permission to perform this action." in str(
            pex.value.message
        )

    def test_route_protected_by_global_controller_permission_works(self):
        request = self.get_real_user_request()
        response = PermissionController.example(request)
        assert response == {"message": "OK"}

    def test_route_is_protected_by_its_permissions(self):
        response = PermissionController.example_allow_any(anonymous_request)
        assert response == {"message": "OK"}

from unittest.mock import Mock

import django
import pytest
from django.contrib.auth.models import AnonymousUser, User
from ninja import Schema

from ninja_extra import APIController, permissions, route, router
from ninja_extra.controllers import (
    AsyncRouteFunction,
    Detail,
    Id,
    Ok,
    Route,
    RouteFunction,
    RouteInvalidParameterException,
)
from ninja_extra.controllers.route.context import RouteContext
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.permissions import AllowAny

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
        assert SomeTestController.example.as_view
        assert hasattr(SomeTestController.example.as_view, "get_route_function")
        assert (
            SomeTestController.example.as_view.get_route_function()
            == SomeTestController.example
        )

    def test_route_generic_invalid_parameters(self):
        with pytest.raises(RouteInvalidParameterException) as ex:

            @route.generic("/example/list", methods=["SOMETHING", "GET"])
            def example_list_create(self, ex_id: str):
                pass

        assert "SOMETHING" in str(ex)

        with pytest.raises(RouteInvalidParameterException) as ex:

            @route.generic("/example/list", methods="SOMETHING")
            def example_list_create(self, ex_id: str):
                pass

        assert "methods must be a list" in str(ex)

    def test_route_response_invalid_parameters(self):
        with pytest.raises(RouteInvalidParameterException) as ex:

            @route.get("/example/list", response=[dict(), ""])
            def example_list_create(self, ex_id: str):
                pass

        assert "Invalid response configuration" in str(ex)

    def test_route_response_parameters_computed_correctly(self):
        unique_response = [Ok, Id, {302: Schema}, (401, Schema)]
        non_unique_response = [
            Ok,
            Id,
            {201: Schema},
        ]  # Id status_code == 201 so it should be replaced by the dict response

        @route.get("/example/list", response=unique_response)
        def example_unique_response(self, ex_id: str):
            pass

        @route.get("/example/list", response=non_unique_response)
        def example_non_unique_response(self, ex_id: str):
            pass

        assert len(example_unique_response.route.route_params.response) == 4
        assert len(example_non_unique_response.route.route_params.response) == 2

    @pytest.mark.parametrize(
        "func, methods, kwargs",
        [
            (
                "get",
                ["GET"],
                dict(
                    auth="Something",
                    response=dict(),
                    operation_id="operation_id",
                ),
            ),
            (
                "post",
                ["POST"],
                dict(summary="summary", description="description", tags=["dsd"]),
            ),
            (
                "delete",
                ["DELETE"],
                dict(by_alias=True, exclude_unset=True, exclude_defaults=True),
            ),
            ("patch", ["PATCH"], dict(url_name="url_name", include_in_schema=True)),
            ("put", ["PUT"], dict(deprecated=True, exclude_none=True)),
            (
                "generic",
                ["PUT", "PATCH"],
                dict(
                    auth="Something",
                    response=dict(),
                    operation_id="operation_id",
                ),
            ),
        ],
    )
    def test_route_generates_required_route_definitions(self, func, methods, kwargs):
        route_method = getattr(route, func)
        route_instance: Route = (
            route_method("/", methods=methods, **kwargs)
            if func == "generic"
            else route_method("/", **kwargs)
        )
        assert route_instance.route_params.methods == methods
        for k, v in kwargs.items():
            assert getattr(route_instance.route_params, k) == v


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
def test_async_route_function():
    class AsyncSomeTestController(SomeTestController):
        @route.get("/example_async")
        async def example_async(self, ex_id: str):
            pass

    assert isinstance(AsyncSomeTestController.example, RouteFunction)
    assert isinstance(AsyncSomeTestController.example_async, AsyncRouteFunction)
    assert AsyncSomeTestController.example_async.as_view
    assert hasattr(AsyncSomeTestController.example_async.as_view, "get_route_function")
    assert (
        AsyncSomeTestController.example_async.as_view.get_route_function()
        == AsyncSomeTestController.example_async
    )


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

    def test_get_route_execution_context(self):
        route_function = route.get("")(self.api_func)
        route_function.controller = Mock()
        route_function.controller.permission_classes = [AllowAny]

        route_context = route_function.get_route_execution_context(
            anonymous_request, "arg1", "arg2", extra="extra"
        )
        assert isinstance(route_context, RouteContext)
        expected_keywords = ("permission_classes", "request", "args", "kwargs")
        for key in expected_keywords:
            assert getattr(route_context, key)

    def test_get_controller_instance_return_controller_instance(self):
        route_function: RouteFunction = SomeTestController.example
        controller_instance = route_function._get_controller_instance()
        assert isinstance(controller_instance, SomeTestController)
        assert isinstance(controller_instance, SomeTestController)
        assert controller_instance.context is None

    def test_process_view_function_result_return_tuple_or_input(self):
        route_function: RouteFunction = SomeTestController.example
        mock_result = Detail("Some Message", status_code=302)
        response = route_function._process_view_function_result(mock_result)
        assert isinstance(response, tuple)
        assert response[1] == mock_result.convert_to_schema()
        assert response[0] == mock_result.status_code

        mock_result = dict(status=302, message="Some Message")
        response = route_function._process_view_function_result(mock_result)
        assert not isinstance(response, tuple)
        assert response == mock_result


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

    def test_route_prep_controller_route_execution_context_works(self):
        route_function: RouteFunction = SomeTestController.example
        context = route_function.get_route_execution_context(request=anonymous_request)
        with route_function._prep_controller_route_execution(context=context) as ctx:
            assert isinstance(ctx.controller_instance, SomeTestController)
            assert ctx.controller_instance.context
        assert ctx.controller_instance.context is None

    def test_route_prep_controller_route_execution_context_cleans_controller_after_route_execution(
        self,
    ):
        route_function: RouteFunction = SomeTestController.example
        context = route_function.get_route_execution_context(request=anonymous_request)
        with pytest.raises(Exception):
            with route_function._prep_controller_route_execution(
                context=context
            ) as ctx:
                assert isinstance(ctx.controller_instance, SomeTestController)
                assert ctx.controller_instance.context
                raise Exception("Should raise an exception")

        assert ctx.controller_instance.context is None

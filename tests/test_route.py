from unittest.mock import Mock

import django
import pytest
from django.contrib.auth.models import AnonymousUser, User
from ninja import Schema
from ninja.constants import NOT_SET

from ninja_extra import api_controller, permissions, route
from ninja_extra.controllers import (
    AsyncRouteFunction,
    Detail,
    Id,
    Ok,
    RouteFunction,
    RouteInvalidParameterException,
)
from ninja_extra.controllers.base import get_all_controller_route_function
from ninja_extra.controllers.route.context import (
    RouteContext,
    get_route_execution_context,
)
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.helper import get_route_function
from ninja_extra.permissions import AllowAny

from .schemas import UserSchema
from .utils import FakeAuth

anonymous_request = Mock()
anonymous_request.user = AnonymousUser()


@api_controller(
    "permission",
    auth=FakeAuth(),
    permissions=[permissions.IsAuthenticated & permissions.IsAdminUser],
)
class PermissionController:
    @route.post("/example_post", auth=None)
    def example(self):
        return {"message": "OK"}

    @route.get("/example_get", auth=None, permissions=[permissions.AllowAny])
    def example_allow_any(self):
        return {"message": "OK"}


@api_controller
class SomeTestController:
    @route.get("/example")
    def example(self):
        pass

    @route.post("/example")
    def example_post(self):
        pass

    @route.patch("/example/{ex_id}")
    def example_patch(self, ex_id: str):
        pass

    @route.patch("/example/{ex_id}")
    def example_put(self, ex_id: str):
        pass

    @route.delete("/example/{ex_id}")
    def example_delete(self, ex_id: str):
        pass

    @route.generic("/example/list", methods=["POST", "GET"])
    def example_list_create(self, ex_id: str):
        pass

    @route.post("/example/operation-id", operation_id="example_post_operation_id")
    def example_post_operation_id(self):
        pass

    @route.get("/example/return-response-as-schema")
    def function_return_as_response_schema(self) -> UserSchema:
        pass


class TestControllerRoute:
    @pytest.mark.parametrize(
        "path,operation_count",
        [
            ("/example", 2),
            ("/example/{ex_id}", 3),
            ("/example/list", 1),
        ],
    )
    def test_api_controller_builds_accurate_operations_list(
        self, path, operation_count
    ):
        api_controller_instance = SomeTestController.get_api_controller()
        path_view = api_controller_instance.path_operations.get(path)
        assert len(path_view.operations) == operation_count

    def test_controller_route_should_have_an_operation(self):
        for route_func in get_all_controller_route_function(SomeTestController):
            path_view = SomeTestController.get_api_controller().path_operations.get(
                str(route_func)
            )
            operations = list(
                filter(
                    lambda n: n.operation_id
                    == route_func.route.route_params.operation_id,
                    path_view.operations,
                )
            )
            assert len(operations) == 1
            if str(route_func) == "/example/operation-id":
                assert operations[0].operation_id == "example_post_operation_id"
            assert route_func.route.route_params.methods == operations[0].methods

    def test_controller_route_should_right_view_func_type(self):
        controller = SomeTestController()
        route_function = get_route_function(controller.example)
        assert isinstance(route_function, RouteFunction)
        assert route_function.as_view
        assert hasattr(route_function.as_view, "get_route_function")
        assert route_function.as_view.get_route_function() == route_function

    def test_controller_route_should_use_userschema_as_response(self):
        controller = SomeTestController()
        route_function = get_route_function(controller.example)
        assert route_function.route.route_params.response == NOT_SET
        route_function: RouteFunction = get_route_function(
            controller.function_return_as_response_schema
        )
        assert route_function.route.route_params.response == UserSchema

    def test_route_generic_invalid_parameters(self):
        with pytest.raises(RouteInvalidParameterException) as ex:

            @route.generic("/example/list", methods=["SOMETHING", "GET"])
            def example_list_create_case_1(self, ex_id: str):
                pass

        assert "SOMETHING" in str(ex)

        with pytest.raises(RouteInvalidParameterException) as ex:

            @route.generic("/example/list", methods="SOMETHING")
            def example_list_create_case_2(self, ex_id: str):
                pass

        assert "methods must be a list" in str(ex)

    def test_route_response_invalid_parameters(self):
        with pytest.raises(RouteInvalidParameterException) as ex:

            @route.get("/example/list", response=[{}, ""])
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

        assert (
            len(get_route_function(example_unique_response).route.route_params.response)
            == 4
        )
        assert (
            len(
                get_route_function(
                    example_non_unique_response
                ).route.route_params.response
            )
            == 2
        )

    @pytest.mark.parametrize(
        "func, methods, kwargs",
        [
            (
                "get",
                ["GET"],
                {
                    "auth": "Something",
                    "response": {},
                    "operation_id": "operation_id",
                },
            ),
            (
                "post",
                ["POST"],
                {"summary": "summary", "description": "description", "tags": ["dsd"]},
            ),
            (
                "delete",
                ["DELETE"],
                {"by_alias": True, "exclude_unset": True, "exclude_defaults": True},
            ),
            ("patch", ["PATCH"], {"url_name": "url_name", "include_in_schema": True}),
            ("put", ["PUT"], {"deprecated": True, "exclude_none": True}),
            (
                "generic",
                ["PUT", "PATCH"],
                {
                    "auth": "Something",
                    "response": {},
                    "operation_id": "operation_id",
                },
            ),
        ],
    )
    def test_route_generates_required_route_definitions(self, func, methods, kwargs):
        def view_func(request):
            pass

        route_method = getattr(route, func)
        (
            route_method("/", methods=methods, **kwargs)
            if func == "generic"
            else route_method("/", **kwargs)
        )(view_func)
        route_function = get_route_function(view_func)
        assert route_function.route.route_params.methods == methods
        for k, v in kwargs.items():
            assert getattr(route_function.route.route_params, k) == v


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
async def test_async_route_function():
    @api_controller()
    class AsyncSomeTestController(SomeTestController):
        @route.get("/example_async")
        async def example_async(self, ex_id: str):
            return {"message": "Okay", "ex_id": ex_id}

    controller = AsyncSomeTestController()
    example_route_function = get_route_function(controller.example)
    example_async_route_function = get_route_function(controller.example_async)

    assert isinstance(example_route_function, RouteFunction)
    assert isinstance(example_async_route_function, AsyncRouteFunction)

    assert example_async_route_function.as_view
    assert hasattr(example_async_route_function.as_view, "get_route_function")
    assert (
        example_async_route_function.as_view.get_route_function()
        == example_async_route_function
    )
    assert await example_async_route_function(anonymous_request, ex_id="some id") == {
        "message": "Okay",
        "ex_id": "some id",
    }


class TestRouteFunction:
    @staticmethod
    def api_func_with_has_request_param(self, request):
        pass

    @staticmethod
    def api_func(self):
        pass

    @staticmethod
    def api_func_with_param(self, example_id: str):
        pass

    @staticmethod
    async def async_api_func(self):
        pass

    def test_get_required_api_func_signature_return_filtered_signature(self):
        route.get("")(self.api_func)
        route_function = get_route_function(self.api_func)
        assert not route_function.has_request_param
        sig_inspect, sig_parameter = route_function._get_required_api_func_signature()
        assert len(sig_parameter) == 0

        route.get("")(self.api_func_with_has_request_param)
        route_function = get_route_function(self.api_func_with_has_request_param)
        assert route_function.has_request_param
        sig_inspect, sig_parameter = route_function._get_required_api_func_signature()
        assert len(sig_parameter) == 0

        route.get("")(self.api_func_with_param)
        route_function = get_route_function(self.api_func_with_param)
        sig_inspect, sig_parameter = route_function._get_required_api_func_signature()
        assert len(sig_parameter) == 1
        assert str(sig_parameter[0]).replace(" ", "") == "example_id:str"

    def test_from_route_returns_route_function_instance(self):
        route.get("")(self.api_func)
        route_function = get_route_function(self.api_func)
        assert isinstance(route_function, RouteFunction)

        route.get("")(self.async_api_func)
        route_function = get_route_function(self.async_api_func)
        assert isinstance(route_function, AsyncRouteFunction)

    def test_get_route_execution_context(self):
        route.get("")(self.api_func)
        route_function = get_route_function(self.api_func)
        with pytest.raises(AssertionError):
            route_function.get_route_execution_context(
                anonymous_request, "arg1", "arg2", extra="extra"
            )
        route_function.api_controller = Mock()
        route_function.api_controller.permission_classes = [AllowAny]

        route_context = route_function.get_route_execution_context(
            anonymous_request, "arg1", "arg2", extra="extra"
        )
        assert isinstance(route_context, RouteContext)
        expected_keywords = ("permission_classes", "request", "args", "kwargs")
        for key in expected_keywords:
            assert getattr(route_context, key)

    def test_get_controller_instance_return_controller_instance(self):
        route_function: RouteFunction = get_route_function(SomeTestController().example)
        controller_instance = route_function._get_controller_instance()
        assert isinstance(controller_instance, SomeTestController)
        assert isinstance(controller_instance, SomeTestController)
        assert controller_instance.context is None

    def test_process_view_function_result_return_tuple_or_input(self):
        route_function: RouteFunction = get_route_function(SomeTestController().example)
        mock_result = Detail("Some Message", status_code=302)
        response = route_function._process_view_function_result(mock_result)
        assert isinstance(response, tuple)
        assert response[1] == mock_result.convert_to_schema()
        assert response[0] == mock_result.status_code

        mock_result = {"status": 302, "message": "Some Message"}
        response = route_function._process_view_function_result(mock_result)
        assert not isinstance(response, tuple)
        assert response == mock_result


@pytest.mark.django_db
class TestAPIControllerRoutePermission:
    def setup(self):
        self.controller = PermissionController()

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

    def test_permission_controller_example_allow_any_auth_is_none(self):
        example_allow_any_route_function = get_route_function(
            self.controller.example_allow_any
        )
        route_params = example_allow_any_route_function.route.route_params
        assert route_params.auth is None

        response = example_allow_any_route_function(anonymous_request)
        assert response == {"message": "OK"}
        assert response == self.controller.example_allow_any()

    def test_route_is_protected_by_global_controller_permission(self):
        example_route_function = get_route_function(self.controller.example)
        with pytest.raises(PermissionDenied) as pex:
            example_route_function(anonymous_request)
        assert "You do not have permission to perform this action." in str(
            pex.value.detail
        )

    def test_route_protected_by_global_controller_permission_works(self):
        example_route_function = get_route_function(self.controller.example)
        request = self.get_real_user_request()
        response = example_route_function(request)
        assert response == {"message": "OK"}

    def test_route_is_protected_by_its_permissions_paramater(self):
        example_allow_any_route_function = get_route_function(
            self.controller.example_allow_any
        )
        response = example_allow_any_route_function(anonymous_request)
        assert response == {"message": "OK"}

    def test_route_prep_controller_route_execution_context_works(self):
        route_function: RouteFunction = get_route_function(SomeTestController().example)
        context = get_route_execution_context(request=anonymous_request)
        with route_function._prep_controller_route_execution(context=context) as ctx:
            assert isinstance(ctx.controller_instance, SomeTestController)
            assert ctx.controller_instance.context
        assert ctx.controller_instance.context is None

    def test_route_prep_controller_route_execution_context_cleans_controller_after_route_execution(
        self,
    ):
        route_function: RouteFunction = get_route_function(SomeTestController().example)
        context = get_route_execution_context(request=anonymous_request)
        with route_function._prep_controller_route_execution(context=context) as ctx:
            assert isinstance(ctx.controller_instance, SomeTestController)
            assert ctx.controller_instance.context

        assert ctx.controller_instance.context is None

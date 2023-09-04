import django
import pytest

from ninja_extra import api_controller, route
from ninja_extra.controllers import AsyncRouteFunction, RouteFunction
from ninja_extra.helper import get_route_function
from ninja_extra.operation import AsyncOperation, Operation
from ninja_extra.testing import TestAsyncClient, TestClient

from .utils import AsyncFakeAuth, FakeAuth, mock_log_call


class CustomException(Exception):
    pass


class TestOperation:
    @api_controller
    class SomeTestController:
        @route.get("/example")
        def example(self):
            return {"message": "example"}

        @route.get("/example_exception")
        def example_exception(self):
            raise CustomException()

    # @mock_signal_call("route_context_started")
    # @mock_signal_call("route_context_finished")
    @mock_log_call("info")
    def test_route_operation_execution_works(self):
        client = TestClient(self.SomeTestController)
        response = client.get("/example")
        assert response.json() == {"message": "example"}

    # @mock_signal_call("route_context_started")
    # @mock_signal_call("route_context_finished")
    @mock_log_call("error")
    def test_route_operation_execution_should_log_execution(self):
        client = TestClient(self.SomeTestController)
        with pytest.raises(CustomException):
            client.get("/example_exception")


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
def test_operation_auth_configs():
    @api_controller("prefix", tags="any_Tag")
    class AController:
        pass

    api_controller_instance = AController.get_api_controller()

    async def async_endpoint(self, request):
        pass

    def sync_endpoint(self, request):
        pass

    sync_auth_http_get = route.get("/example", auth=[FakeAuth()])
    async_auth_http_get = route.get("/example/async", auth=[AsyncFakeAuth()])

    sync_auth_http_get(async_endpoint)
    async_route_function = get_route_function(async_endpoint)
    assert isinstance(async_route_function, AsyncRouteFunction)

    api_controller_instance._add_operation_from_route_function(async_route_function)
    assert isinstance(async_route_function.operation, AsyncOperation)
    api_controller_instance._add_operation_from_route_function(async_route_function)
    assert isinstance(async_route_function.operation, AsyncOperation)

    sync_auth_http_get(sync_endpoint)
    sync_route_function = get_route_function(sync_endpoint)
    api_controller_instance._add_operation_from_route_function(sync_route_function)
    assert isinstance(sync_route_function.operation, Operation)
    assert isinstance(sync_route_function, RouteFunction)

    with pytest.raises(Exception) as ex:
        new_sync_endpoint = async_auth_http_get(sync_endpoint)
        new_sync_route_function = get_route_function(new_sync_endpoint)
        api_controller_instance._add_operation_from_route_function(
            new_sync_route_function
        )
    assert "sync_endpoint" in str(ex) and "AsyncFakeAuth" in str(ex)


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
class TestAsyncOperations:
    if not django.VERSION < (3, 1):

        @api_controller
        class SomeTestController:
            @route.get("/example")
            async def example(self):
                return {"message": "example"}

            @route.get("/example_exception")
            async def example_exception(self):
                raise CustomException()

        # @mock_signal_call("route_context_started")
        # @mock_signal_call("route_context_finished")
        @mock_log_call("info")
        async def test_async_route_operation_execution_works(self):
            client = TestAsyncClient(self.SomeTestController)
            response = await client.get("/example")
            assert response.json() == {"message": "example"}

        # @mock_signal_call("route_context_started")
        # @mock_signal_call("route_context_finished")
        @mock_log_call("error")
        async def test_async_route_operation_execution_should_log_execution(self):
            client = TestAsyncClient(self.SomeTestController)
            with pytest.raises(CustomException):
                await client.get("/example_exception")

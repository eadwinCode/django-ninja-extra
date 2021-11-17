import django
import pytest

from ninja_extra import APIController, route, router
from ninja_extra.testing import TestAsyncClient, TestClient

from .utils import mock_log_call, mock_signal_call


class TestOperation:
    @router("")
    class SomeTestController(APIController):
        @route.get("/example")
        def example(self):
            return {"message": "example"}

        @route.get("/example_exception")
        def example_exception(self):
            raise Exception()

    @mock_signal_call("route_context_started")
    @mock_signal_call("route_context_finished")
    @mock_log_call("info")
    def test_route_operation_execution_works(self):
        client = TestClient(self.SomeTestController)
        response = client.get(str(self.SomeTestController.example))
        assert response.json() == {"message": "example"}

    @mock_signal_call("route_context_started")
    @mock_signal_call("route_context_finished")
    @mock_log_call("error")
    def test_route_operation_execution_should_log_execution(self):
        client = TestClient(self.SomeTestController)
        with pytest.raises(Exception):
            client.get(str(self.SomeTestController.example_exception))


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
class TestAsyncOperations:
    if not django.VERSION < (3, 1):

        @router("")
        class SomeTestController(APIController):
            @route.get("/example")
            async def example(self):
                return {"message": "example"}

            @route.get("/example_exception")
            async def example_exception(self):
                raise Exception()

        @mock_signal_call("route_context_started")
        @mock_signal_call("route_context_finished")
        @mock_log_call("info")
        async def test_async_route_operation_execution_works(self):
            client = TestAsyncClient(self.SomeTestController)
            response = await client.get(str(self.SomeTestController.example))
            assert response.json() == {"message": "example"}

        @mock_signal_call("route_context_started")
        @mock_signal_call("route_context_finished")
        @mock_log_call("error")
        async def test_async_route_operation_execution_should_log_execution(self):
            client = TestAsyncClient(self.SomeTestController)
            with pytest.raises(Exception):
                await client.get(str(self.SomeTestController.example_exception))

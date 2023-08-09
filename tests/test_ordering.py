import inspect
import operator
from typing import List

import django
import pytest
from ninja import Schema

from ninja_extra import NinjaExtraAPI, api_controller, route
from ninja_extra.controllers import RouteFunction
from ninja_extra.ordering import (
    AsyncOrderatorOperation,
    OrderatorOperation,
    Ordering,
    OrderingBase,
    ordering,
)
from ninja_extra.testing import TestAsyncClient, TestClient

from .models import Category

if not django.VERSION < (3, 1):
    from asgiref.sync import sync_to_async


class CustomOrdering(OrderingBase):
    class Input(Schema):
        order_by: str

    def ordering_queryset(self, items, ordering_input):
        field = ordering_input.order_by
        if field:
            if isinstance(items, list):
                return sorted(
                    items,
                    key=operator.attrgetter(field[int(field.startswith("-")) :]),
                    reverse=field.startswith("-"),
                )
            return items.order_by(ordering_input.order_by)
        return items


class CategorySchema(Schema):
    title: str


@api_controller
class SomeAPIController:
    @route.get("/items_1", response=List[CategorySchema])
    @ordering  # WITHOUT brackets (should use default pagination)
    def items_1(self):
        return Category.objects.all()

    @route.get("/items_2", response=List[CategorySchema])
    @ordering()  # with brackets (should use default pagination)
    def items_2(self, someparam: int = 0):
        # also having custom param `someparam` - that should not be lost
        return Category.objects.all()

    @route.get("/items_3", response=List[CategorySchema])
    @ordering(CustomOrdering, pass_parameter="pass_kwargs")
    def items_3(self, **kwargs):
        return Category.objects.all()

    @route.get("/items_4", response=List[CategorySchema])
    @ordering(Ordering, ordering_fields=["title"], pass_parameter="pass_kwargs")
    def items_4(self, **kwargs):
        return Category.objects.all()

    @route.get("/items_5", response=List[CategorySchema])
    @ordering(Ordering, ordering_fields=["title"])
    def items_5(self, **kwargs):
        return list(Category.objects.all())

    @route.get("/items_6", response=List[CategorySchema])
    @ordering
    def items_6(self):
        return [CategorySchema(title=f"title_{i}") for i in range(3)]

    @route.get("/items_7", response=List[CategorySchema])
    @ordering
    def items_7(self):
        return []

    @route.get("/items_8", response=List[CategorySchema])
    @ordering
    def items_8(self):
        return [{"title": f"title_{i}"} for i in range(3)]

    @route.get("/items_9", response=List[int])
    @ordering
    def items_9(self):
        return list(range(3))


api = NinjaExtraAPI()
api.register_controllers(SomeAPIController)

client = TestClient(SomeAPIController)


@pytest.mark.django_db
class TestOrdering:
    def test_orderator_operation_used(self):
        some_api_route_functions = dict(
            inspect.getmembers(
                SomeAPIController, lambda member: isinstance(member, RouteFunction)
            )
        )
        has_kwargs = ("items_3", "items_4")
        for name, route_function in some_api_route_functions.items():
            assert hasattr(route_function.as_view, "orderator_operation")
            orderator_operation = route_function.as_view.orderator_operation
            assert isinstance(orderator_operation, OrderatorOperation)
            if name in has_kwargs:
                assert orderator_operation.view_func_has_kwargs

    def test_case1(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_1?ordering=-title").json()
        assert response[0]["title"] == "title_2"

        schema = api.get_openapi_schema()["paths"]["/api/items_1"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "ordering",
                "schema": {"title": "Ordering", "type": "string"},
                "required": False,
            }
        ]
        response = client.get("/items_1?ordering=").json()
        assert response[0]["title"] == "title_0"

    def test_case2(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_2?ordering=-title,-id").json()
        assert response[0]["title"] == "title_2"

        schema = api.get_openapi_schema()["paths"]["/api/items_2"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "someparam",
                "schema": {"title": "Someparam", "default": 0, "type": "integer"},
                "required": False,
            },
            {
                "in": "query",
                "name": "ordering",
                "schema": {"title": "Ordering", "type": "string"},
                "required": False,
            },
        ]

    def test_case3(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_3?order_by=-title").json()
        assert response[0]["title"] == "title_2"

        schema = api.get_openapi_schema()["paths"]["/api/items_3"]["get"]
        # print(schema["parameters"])
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "order_by",
                "schema": {"title": "Order By", "type": "string"},
                "required": True,
            }
        ]

    def test_case4(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_4?ordering=-title").json()
        assert response[0]["title"] == "title_2"

        schema = api.get_openapi_schema()["paths"]["/api/items_4"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "ordering",
                "schema": {"title": "Ordering", "type": "string"},
                "required": False,
            }
        ]

    def test_case5(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_5?ordering=-title").json()
        assert response[0]["title"] == "title_2"

    def test_case_with_empty_items5(self):
        response = client.get("/items_5?ordering=-title").json()
        assert len(response) == 0

    def test_case6(self):
        response = client.get("/items_6?ordering=-title").json()
        assert response[0]["title"] == "title_2"

    def test_case_with_empty(self):
        response = client.get("/items_7?ordering=-title").json()
        assert len(response) == 0

    def test_case8(self):
        response = client.get("/items_8?ordering=-title").json()
        assert response[0]["title"] == "title_2"

    def test_case9(self):
        response = client.get("/items_9?ordering=-title").json()
        assert response[0] == 0


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
@pytest.mark.django_db
class TestAsyncOrdering:
    if not django.VERSION < (3, 1):

        @api_controller
        class AsyncSomeAPIController:
            @route.get("/items_1", response=List[CategorySchema])
            @ordering  # WITHOUT brackets (should use default pagination)
            async def items_1(self):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_2", response=List[CategorySchema])
            @ordering()  # with brackets (should use default pagination)
            async def items_2(self, someparam: int = 0):
                # also having custom param `someparam` - that should not be lost
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_3", response=List[CategorySchema])
            @ordering(CustomOrdering, pass_parameter="pass_kwargs")
            async def items_3(self, **kwargs):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_4", response=List[CategorySchema])
            @ordering(Ordering, ordering_fields=["title"], pass_parameter="pass_kwargs")
            async def items_4(self, **kwargs):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_6", response=List[CategorySchema])
            @ordering
            async def items_6(self):
                return await sync_to_async(list)(
                    [CategorySchema(title=f"title_{i}") for i in range(3)]
                )

            @route.get("/items_7", response=List[CategorySchema])
            @ordering
            async def items_7(self):
                return await sync_to_async(list)([])

            @route.get("/items_8", response=List[CategorySchema])
            @ordering
            async def items_8(self):
                return await sync_to_async(list)(
                    [{"title": f"title_{i}"} for i in range(3)]
                )

            @route.get("/items_9", response=List[int])
            @ordering
            async def items_9(self):
                return await sync_to_async(list)(list(range(3)))

        api_async = NinjaExtraAPI()
        api_async.register_controllers(AsyncSomeAPIController)
        client = TestAsyncClient(AsyncSomeAPIController)

        async def test_orderator_operation_used(self):
            some_api_route_functions = dict(
                inspect.getmembers(
                    self.AsyncSomeAPIController,
                    lambda member: isinstance(member, RouteFunction),
                )
            )
            has_kwargs = ("items_3", "items_4")
            for name, route_function in some_api_route_functions.items():
                assert hasattr(route_function.as_view, "orderator_operation")
                orderator_operation = route_function.as_view.orderator_operation
                assert isinstance(orderator_operation, AsyncOrderatorOperation)
                if name in has_kwargs:
                    assert orderator_operation.view_func_has_kwargs

        async def test_case1(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_1?ordering=-title")
            data = response.json()
            assert data[0]["title"] == "title_2"

            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_1"]["get"]
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "ordering",
                    "schema": {"title": "Ordering", "type": "string"},
                    "required": False,
                }
            ]
            response = await self.client.get("/items_1?ordering=")
            data = response.json()
            assert data[0]["title"] == "title_0"

        async def test_case2(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_2?ordering=-title,-id")
            data = response.json()
            assert data[0]["title"] == "title_2"

            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_2"]["get"]
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "someparam",
                    "schema": {"title": "Someparam", "default": 0, "type": "integer"},
                    "required": False,
                },
                {
                    "in": "query",
                    "name": "ordering",
                    "schema": {"title": "Ordering", "type": "string"},
                    "required": False,
                },
            ]

        async def test_case3(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_3?order_by=-title")
            data = response.json()
            assert data[0]["title"] == "title_2"

            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_3"]["get"]
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "order_by",
                    "schema": {"title": "Order By", "type": "string"},
                    "required": True,
                }
            ]

        async def test_case4(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_4?ordering=-title")
            data = response.json()
            assert data[0]["title"] == "title_2"

            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_4"]["get"]
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "ordering",
                    "schema": {"title": "Ordering", "type": "string"},
                    "required": False,
                }
            ]

        async def test_case6(self):
            response = await self.client.get("/items_6?ordering=-title")
            data = response.json()
            assert data[0]["title"] == "title_2"

        async def test_case_with_empty(self):
            response = await self.client.get("/items_7?ordering=-title")
            data = response.json()
            assert len(data) == 0

        async def test_case8(self):
            response = await self.client.get("/items_8?ordering=-title")
            data = response.json()
            assert data[0]["title"] == "title_2"

        async def test_case9(self):
            response = await self.client.get("/items_9?ordering=-title")
            data = response.json()
            assert data[0] == 0

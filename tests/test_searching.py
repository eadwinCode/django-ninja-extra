import inspect
import operator
from typing import List

import django
import pytest
from ninja import Schema

from ninja_extra import NinjaExtraAPI, api_controller, route
from ninja_extra.controllers import RouteFunction
from ninja_extra.searching import (
    AsyncSearcheratorOperation,
    SearcheratorOperation,
    Searching,
    SearchingBase,
    searching,
)
from ninja_extra.testing import TestAsyncClient, TestClient

from .models import Category

if not django.VERSION < (3, 1):
    from asgiref.sync import sync_to_async


class CustomSearch(SearchingBase):
    class Input(Schema):
        srch: str

    def searching_queryset(self, items, searching_input):
        if searching_input.srch:
            if isinstance(items, list):
                return [
                    item
                    for item in items
                    if searching_input.srch.lower()
                    in operator.attrgetter("title")(item).lower()
                ]
            return items.filter(title__icontains=searching_input.srch)
        return items


class CategorySchema(Schema):
    title: str


@api_controller
class SomeAPIController:
    @route.get("/items_1", response=List[CategorySchema])
    @searching  # WITHOUT brackets (should use default pagination)
    def items_1(self):
        return Category.objects.all()

    @route.get("/items_2", response=List[CategorySchema])
    @searching()  # with brackets (should use default pagination)
    def items_2(self, someparam: int = 0):
        # also having custom param `someparam` - that should not be lost
        return Category.objects.all()

    @route.get("/items_3", response=List[CategorySchema])
    @searching(CustomSearch, pass_parameter="pass_kwargs")
    def items_3(self, **kwargs):
        return Category.objects.all()

    @route.get("/items_4", response=List[CategorySchema])
    @searching(Searching, search_fields=["title"], pass_parameter="pass_kwargs")
    def items_4(self, **kwargs):
        return Category.objects.all()

    @route.get("/items_5", response=List[CategorySchema])
    @searching(search_fields=["=title"], pass_parameter="pass_kwargs")
    def items_5(self, **kwargs):
        return Category.objects.all()


api = NinjaExtraAPI()
api.register_controllers(SomeAPIController)

client = TestClient(SomeAPIController)


@pytest.mark.django_db
class TestSearch:
    def test_Search_operation_used(self):
        some_api_route_functions = dict(
            inspect.getmembers(
                SomeAPIController, lambda member: isinstance(member, RouteFunction)
            )
        )
        has_kwargs = ("items_3", "items_4")
        for name, route_function in some_api_route_functions.items():
            assert hasattr(route_function.as_view, "searcherator_operation")
            searcherator_operation = route_function.as_view.searcherator_operation
            assert isinstance(searcherator_operation, SearcheratorOperation)
            if name in has_kwargs:
                assert searcherator_operation.view_func_has_kwargs

    def test_case1(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_1?search=2").json()
        assert response[0]["title"] == "title_0"

        schema = api.get_openapi_schema()["paths"]["/api/items_1"]["get"]
        # print(schema["parameters"])
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "search",
                "schema": {"title": "Search", "type": "string"},
                "required": False,
            }
        ]
        response = client.get("/items_1?search=").json()
        assert response[0]["title"] == "title_0"

    def test_case2(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_2?search=2").json()
        assert response[0]["title"] == "title_0"

        schema = api.get_openapi_schema()["paths"]["/api/items_2"]["get"]

        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "someparam",
                "schema": {"title": "Someparam", "default": 0, "type": "integer"},
                "required": False,
            },
            {
                "in": "query",
                "name": "search",
                "schema": {"title": "Search", "type": "string"},
                "required": False,
            },
        ]

    def test_case3(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_3?srch=_2").json()
        assert response[0]["title"] == "title_2"

        schema = api.get_openapi_schema()["paths"]["/api/items_3"]["get"]
        # print(schema["parameters"])
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "srch",
                "schema": {"title": "Srch", "type": "string"},
                "required": True,
            }
        ]

    def test_case4(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_4?search=2").json()
        assert response[0]["title"] == "title_2"

        schema = api.get_openapi_schema()["paths"]["/api/items_4"]["get"]

        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "search",
                "schema": {"title": "Search", "type": "string"},
                "required": False,
            }
        ]

    def test_case5(self):
        for i in range(3):
            Category.objects.create(title=f"title_{i}")
        response = client.get("/items_5?search=title_2").json()
        assert response[0]["title"] == "title_2"

        schema = api.get_openapi_schema()["paths"]["/api/items_5"]["get"]

        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "search",
                "schema": {"title": "Search", "type": "string"},
                "required": False,
            }
        ]


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
@pytest.mark.django_db
class TestAsyncSearch:
    if not django.VERSION < (3, 1):

        @api_controller
        class AsyncSomeAPIController:
            @route.get("/items_1", response=List[CategorySchema])
            @searching  # WITHOUT brackets (should use default pagination)
            async def items_1(self):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_2", response=List[CategorySchema])
            @searching()  # with brackets (should use default pagination)
            async def items_2(self, someparam: int = 0):
                # also having custom param `someparam` - that should not be lost
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_3", response=List[CategorySchema])
            @searching(CustomSearch, pass_parameter="pass_kwargs")
            async def items_3(self, **kwargs):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_4", response=List[CategorySchema])
            @searching(Searching, search_fields=["title"], pass_parameter="pass_kwargs")
            async def items_4(self, **kwargs):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_5", response=List[CategorySchema])
            @searching(search_fields=["=title"], pass_parameter="pass_kwargs")
            async def items_5(self, **kwargs):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_6", response=List[CategorySchema])
            @searching(search_fields=["^title"], pass_parameter="pass_kwargs")
            async def items_6(self, **kwargs):
                return await sync_to_async(list)(Category.objects.all())

            @route.get("/items_7", response=List[CategorySchema])
            @searching(search_fields=["$title"], pass_parameter="pass_kwargs")
            async def items_7(self, **kwargs):
                return await sync_to_async(list)(Category.objects.all())

        api_async = NinjaExtraAPI()
        api_async.register_controllers(AsyncSomeAPIController)
        client = TestAsyncClient(AsyncSomeAPIController)

        async def test_Search_operation_used(self):
            some_api_route_functions = dict(
                inspect.getmembers(
                    self.AsyncSomeAPIController,
                    lambda member: isinstance(member, RouteFunction),
                )
            )
            has_kwargs = ("items_3", "items_4")
            for name, route_function in some_api_route_functions.items():
                assert hasattr(route_function.as_view, "searcherator_operation")
                searcherator_operation = route_function.as_view.searcherator_operation
                assert isinstance(searcherator_operation, AsyncSearcheratorOperation)
                if name in has_kwargs:
                    assert searcherator_operation.view_func_has_kwargs

        async def test_case1(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_1?search=2")
            data = response.json()
            assert data[0]["title"] == "title_0"

            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_1"]["get"]
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "search",
                    "schema": {"title": "Search", "type": "string"},
                    "required": False,
                }
            ]
            response = await self.client.get("/items_1?search=")
            data = response.json()
            assert data[0]["title"] == "title_0"

        async def test_case2(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_2?search=2")
            data = response.json()
            assert data[0]["title"] == "title_0"

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
                    "name": "search",
                    "schema": {"title": "Search", "type": "string"},
                    "required": False,
                },
            ]

        async def test_case3(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_3?srch=2")
            data = response.json()
            assert data[0]["title"] == "title_2"

            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_3"]["get"]
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "srch",
                    "schema": {"title": "Srch", "type": "string"},
                    "required": True,
                }
            ]

        async def test_case4(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_4?search=2")
            data = response.json()
            assert data[0]["title"] == "title_2"
            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_4"]["get"]
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "search",
                    "schema": {"title": "Search", "type": "string"},
                    "required": False,
                }
            ]

        async def test_case5(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_5?search=title_2")
            data = response.json()
            assert data[0]["title"] == "title_2"
            schema = api.get_openapi_schema()["paths"]["/api/items_5"]["get"]

            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "search",
                    "schema": {"title": "Search", "type": "string"},
                    "required": False,
                }
            ]

        async def test_case6(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_6?search=title_2")
            data = response.json()
            assert data[0]["title"] == "title_2"

        async def test_case7(self):
            for i in range(3):
                await sync_to_async(Category.objects.create)(title=f"title_{i}")
            response = await self.client.get("/items_7?search=_2")
            data = response.json()
            assert data[0]["title"] == "title_2"

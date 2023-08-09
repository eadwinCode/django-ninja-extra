import inspect
import typing

import django
import pytest
from ninja import Schema

from ninja_extra import NinjaExtraAPI, api_controller, route
from ninja_extra.controllers import RouteFunction
from ninja_extra.pagination import (
    AsyncPaginatorOperation,
    PageNumberPagination,
    PageNumberPaginationExtra,
    PaginationBase,
    PaginatorOperation,
    paginate,
)
from ninja_extra.schemas import NinjaPaginationResponseSchema
from ninja_extra.testing import TestAsyncClient, TestClient

ITEMS = list(range(100))


class FakeQuerySet(typing.Sequence):
    def __init__(self, items=None):
        self.items = ITEMS if items is None else items

    def __getitem__(self, index: int) -> typing.Any:
        return FakeQuerySet(self.items[index])

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        for item in self.items:
            yield item


class CustomPagination(PaginationBase):
    # only offset param, defaults to 5 per page
    class Input(Schema):
        skip: int

    def paginate_queryset(self, items, request, **params):
        skip = params["pagination"].skip
        return items[skip : skip + 5]


@api_controller
class SomeAPIController:
    @route.get("/items_1")
    @paginate  # WITHOUT brackets (should use default pagination)
    def items_1(self):
        return ITEMS

    @route.get("/items_2", response=NinjaPaginationResponseSchema[int])
    @paginate()  # with brackets (should use default pagination)
    def items_2(self, someparam: int = 0):
        # also having custom param `someparam` - that should not be lost
        return FakeQuerySet()

    @route.get("/items_3")
    @paginate(CustomPagination, pass_parameter="pass_kwargs")
    def items_3(self, **kwargs):
        return ITEMS

    @route.get("/items_4", response=PageNumberPaginationExtra.get_response_schema(int))
    @paginate(PageNumberPaginationExtra, page_size=10, pass_parameter="pass_kwargs")
    def items_4(self, **kwargs):
        return ITEMS

    @route.get("/items_5")
    @paginate(PageNumberPagination, page_size=10)
    def items_5_without_kwargs(self):
        return ITEMS

    @route.get("/items_6", response=NinjaPaginationResponseSchema[int])
    @paginate()
    def items_6_empty_query_set(self):
        return FakeQuerySet([])


api = NinjaExtraAPI()
api.register_controllers(SomeAPIController)

client = TestClient(SomeAPIController)


class TestPagination:
    def test_paginator_operation_used(self):
        some_api_route_functions = dict(
            inspect.getmembers(
                SomeAPIController, lambda member: isinstance(member, RouteFunction)
            )
        )
        has_kwargs = ("items_3", "items_4")
        for name, route_function in some_api_route_functions.items():
            assert hasattr(route_function.as_view, "paginator_operation")
            paginator_operation = route_function.as_view.paginator_operation
            assert isinstance(paginator_operation, PaginatorOperation)
            if name in has_kwargs:
                assert paginator_operation.view_func_has_kwargs

    def test_case1(self):
        response = client.get("/items_1?limit=10").json()
        assert response.get("items")
        assert response["items"] == ITEMS[:10]

        schema = api.get_openapi_schema()["paths"]["/api/items_1"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "limit",
                "schema": {
                    "title": "Limit",
                    "default": 100,
                    "minimum": 1,
                    "type": "integer",
                },
                "required": False,
            },
            {
                "in": "query",
                "name": "offset",
                "schema": {
                    "title": "Offset",
                    "default": 0,
                    "minimum": 0,
                    "type": "integer",
                },
                "required": False,
            },
        ]

    def test_case2(self):
        response = client.get("/items_2?limit=10").json()
        assert response.get("items")
        assert response["items"] == ITEMS[:10]

        schema = api.get_openapi_schema()["paths"]["/api/items_2"]["get"]
        # print(schema["parameters"])
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "someparam",
                "schema": {"title": "Someparam", "default": 0, "type": "integer"},
                "required": False,
            },
            {
                "in": "query",
                "name": "limit",
                "schema": {
                    "title": "Limit",
                    "default": 100,
                    "minimum": 1,
                    "type": "integer",
                },
                "required": False,
            },
            {
                "in": "query",
                "name": "offset",
                "schema": {
                    "title": "Offset",
                    "default": 0,
                    "minimum": 0,
                    "type": "integer",
                },
                "required": False,
            },
        ]

    def test_case3(self):
        response = client.get("/items_3?skip=5").json()
        assert response == ITEMS[5:10]

        schema = api.get_openapi_schema()["paths"]["/api/items_3"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "skip",
                "schema": {"title": "Skip", "type": "integer"},
                "required": True,
            }
        ]

    def test_case4_no_previous(self):
        response = client.get("/items_4").json()
        assert response.get("previous") is None

    def test_case4_negative_page_number(self):
        response = client.get("/items_4?page=-1").json()
        assert response == {
            "detail": [
                {
                    "loc": ["query", "page"],
                    "msg": "ensure this value is greater than 0",
                    "type": "value_error.number.not_gt",
                    "ctx": {"limit_value": 0},
                }
            ]
        }

    def test_case_4_can_t_exceed_page_number(self):
        response = client.get("/items_4?page=10").json()
        assert response == {
            "count": 100,
            "next": None,
            "previous": "http://testlocation/?page=9",
            "results": [90, 91, 92, 93, 94, 95, 96, 97, 98, 99],
        }

    def test_case4(self):
        response = client.get("/items_4?page=2").json()
        assert response.get("results") == ITEMS[10:20]
        assert response.get("count") == 100
        assert response.get("next") == "http://testlocation/?page=3"
        assert response.get("previous") == "http://testlocation/"

        schema = api.get_openapi_schema()["paths"]["/api/items_4"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "page",
                "schema": {
                    "title": "Page",
                    "default": 1,
                    "exclusiveMinimum": 0,
                    "type": "integer",
                },
                "required": False,
            },
            {
                "in": "query",
                "name": "page_size",
                "schema": {
                    "title": "Page Size",
                    "default": 10,
                    "exclusiveMaximum": 200,
                    "type": "integer",
                },
                "required": False,
            },
        ]

    def test_case5(self):
        response = client.get("/items_5?page=2").json()
        assert response.get("items")
        assert response["items"] == ITEMS[10:20]

        schema = api.get_openapi_schema()["paths"]["/api/items_5"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "page",
                "schema": {
                    "title": "Page",
                    "default": 1,
                    "minimum": 1,
                    "type": "integer",
                },
                "required": False,
            }
        ]

    def test_case6(self):
        response = client.get("/items_6?page=1").json()
        assert response.get("items") is not None
        assert response["items"] == []


@pytest.mark.skipif(django.VERSION < (3, 1), reason="requires django 3.1 or higher")
@pytest.mark.asyncio
class TestAsyncOperations:
    if not django.VERSION < (3, 1):

        @api_controller
        class AsyncSomeAPIController:
            @route.get("/items_1")
            @paginate  # WITHOUT brackets (should use default pagination)
            async def items_1(self, **kwargs):
                return ITEMS

            @route.get("/items_2")
            @paginate()  # with brackets (should use default pagination)
            async def items_2(self, someparam: int = 0):
                # also having custom param `someparam` - that should not be lost
                return ITEMS

            @route.get("/items_3")
            @paginate(CustomPagination, pass_parameter="pass_kwargs")
            async def items_3(self, **kwargs):
                return ITEMS

            @route.get("/items_4")
            @paginate(
                PageNumberPaginationExtra, page_size=10, pass_parameter="pass_kwargs"
            )
            async def items_4(self, **kwargs):
                return ITEMS

            @route.get("/items_5")
            @paginate(PageNumberPagination, page_size=10)
            async def items_5_without_kwargs(self):
                return ITEMS

        api_async = NinjaExtraAPI()
        api_async.register_controllers(AsyncSomeAPIController)
        client = TestAsyncClient(AsyncSomeAPIController)

        async def test_paginator_operation_used(self):
            some_api_route_functions = dict(
                inspect.getmembers(
                    self.AsyncSomeAPIController,
                    lambda member: isinstance(member, RouteFunction),
                )
            )
            has_kwargs = ("items_3", "items_4")
            for name, route_function in some_api_route_functions.items():
                assert hasattr(route_function.as_view, "paginator_operation")
                paginator_operation = route_function.as_view.paginator_operation
                assert isinstance(paginator_operation, AsyncPaginatorOperation)
                if name in has_kwargs:
                    assert paginator_operation.view_func_has_kwargs

        async def test_case1(self):
            response = await self.client.get("/items_1?limit=10")
            data = response.json()
            assert data.get("items")
            assert data["items"] == ITEMS[:10]

            schema = self.api_async.get_openapi_schema()["paths"]["/api/items_1"]["get"]
            # print(schema)
            assert schema["parameters"] == [
                {
                    "in": "query",
                    "name": "limit",
                    "schema": {
                        "title": "Limit",
                        "default": 100,
                        "minimum": 1,
                        "type": "integer",
                    },
                    "required": False,
                },
                {
                    "in": "query",
                    "name": "offset",
                    "schema": {
                        "title": "Offset",
                        "default": 0,
                        "minimum": 0,
                        "type": "integer",
                    },
                    "required": False,
                },
            ]

        async def test_case2(self):
            response = await self.client.get("/items_2?limit=10")
            data = response.json()
            assert data.get("items")
            assert data["items"] == ITEMS[:10]

        async def test_case3(self):
            response = await self.client.get("/items_3?skip=5")
            assert response.json() == ITEMS[5:10]

        async def test_case4(self):
            response = await self.client.get("/items_4?page=2")
            response = response.json()
            assert response.get("results") == ITEMS[10:20]
            assert response.get("count") == 100
            assert response.get("next") == "http://testlocation/?page=3"
            assert response.get("previous") == "http://testlocation/"

        async def test_case5(self):
            response = await self.client.get("/items_5?page=2")
            data = response.json()
            assert data.get("items")
            assert data["items"] == ITEMS[10:20]


def test_pagination_extra_get_schema():
    pass

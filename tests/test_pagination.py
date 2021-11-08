from ninja import Schema

from ninja_extra import APIController, NinjaExtraAPI, route, router
from ninja_extra.pagination import (
    PageNumberPagination,
    PageNumberPaginationExtra,
    PaginationBase,
    paginate,
)
from ninja_extra.testing import TestClient

ITEMS = list(range(100))


class CustomPagination(PaginationBase):
    # only offset param, defaults to 5 per page
    class Input(Schema):
        skip: int

    def paginate_queryset(self, items, request, **params):
        skip = params["pagination"].skip
        return items[skip : skip + 5]


@router("")
class SomeAPIController(APIController):
    @route.get("/items_1")
    @paginate  # WITHOUT brackets (should use default pagination)
    def items_1(self, **kwargs):
        return ITEMS

    @route.get("/items_2")
    @paginate()  # with brackets (should use default pagination)
    def items_2(self, someparam: int = 0, **kwargs):
        # also having custom param `someparam` - that should not be lost
        return ITEMS

    @route.get("/items_3")
    @paginate(CustomPagination)
    def items_3(self, **kwargs):
        return ITEMS

    @route.get("/items_4")
    @paginate(PageNumberPaginationExtra, page_size=10)
    def items_4(self, **kwargs):
        return ITEMS

    @route.get("/items_5")
    @paginate(PageNumberPagination, page_size=10)
    def items_5_without_kwargs(self):
        return ITEMS


api = NinjaExtraAPI()
api.register_controllers(SomeAPIController)

client = TestClient(SomeAPIController)


class TestPagination:
    def test_case1(self):
        response = client.get("/items_1?limit=10").json()
        assert response == ITEMS[:10]

        schema = api.get_openapi_schema()["paths"]["/api/items_1"]["get"]
        # print(schema)
        assert schema["parameters"] == [
            {
                "in": "query",
                "name": "limit",
                "schema": {
                    "title": "Limit",
                    "default": 100,
                    "exclusiveMinimum": 0,
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
                    "exclusiveMinimum": -1,
                    "type": "integer",
                },
                "required": False,
            },
        ]

    def test_case2(self):
        response = client.get("/items_2?limit=10").json()
        assert response == ITEMS[:10]

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
                    "exclusiveMinimum": 0,
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
                    "exclusiveMinimum": -1,
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
        assert response == ITEMS[10:20]

        schema = api.get_openapi_schema()["paths"]["/api/items_5"]["get"]
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
            }
        ]

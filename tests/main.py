from typing import List, Optional
from uuid import UUID

from django.urls import register_converter
from ninja import Field, Path, Query, Schema

from ninja_extra import api_controller, route


class CustomPathConverter1:
    regex = "[0-9]+"

    def to_python(self, value) -> "int":
        """reverse the string and convert to int"""
        return int(value[::-1])

    def to_url(self, value):
        return str(value)


class CustomPathConverter2:
    regex = "[0-9]+"

    def to_python(self, value):
        """reverse the string and convert to float like"""
        return f"0.{value[::-1]}"

    def to_url(self, value):
        return str(value)


register_converter(CustomPathConverter1, "custom-int")
register_converter(CustomPathConverter2, "custom-float")


@api_controller("/path")
class PathParamController:
    @route.get("/param-django-custom-int/{custom-int:item_id}")
    def get_path_param_django_custom_int(self, request, item_id: int):
        return item_id

    @route.get("/param-django-custom-float/{custom-float:item_id}")
    def get_path_param_django_custom_float(self, request, item_id: float):
        return item_id

    @route.get("/text")
    def get_text(self, request):
        return "Hello World"

    @route.get("/{item_id}")
    def get_id(self, request, item_id):
        return item_id

    @route.get("/str/{item_id}")
    def get_str_id(self, request, item_id: str):
        return item_id

    @route.get("/int/{item_id}")
    def get_int_id(self, request, item_id: int):
        return item_id

    @route.get("/float/{item_id}")
    def get_float_id(self, request, item_id: float):
        return item_id

    @route.get("/bool/{item_id}")
    def get_bool_id(self, request, item_id: bool):
        return item_id

    @route.get("/param/{item_id}")
    def get_path_param_id(self, request, item_id: str = Path(None)):
        return item_id

    @route.get("/param-required/{item_id}")
    def get_path_param_required_id(self, request, item_id: str = Path(...)):
        return item_id

    @route.get("/param-minlength/{item_id}")
    def get_path_param_min_length(
        self, request, item_id: str = Path(..., min_length=3)
    ):
        return item_id

    @route.get("/param-maxlength/{item_id}")
    def get_path_param_max_length(
        self, request, item_id: str = Path(..., max_length=3)
    ):
        return item_id

    @route.get("/param-min_maxlength/{item_id}")
    def get_path_param_min_max_length(
        self, request, item_id: str = Path(..., max_length=3, min_length=2)
    ):
        return item_id

    @route.get("/param-gt/{item_id}")
    def get_path_param_gt(self, request, item_id: float = Path(..., gt=3)):
        return item_id

    @route.get("/param-gt0/{item_id}")
    def get_path_param_gt0(self, request, item_id: float = Path(..., gt=0)):
        return item_id

    @route.get("/param-ge/{item_id}")
    def get_path_param_ge(self, request, item_id: float = Path(..., ge=3)):
        return item_id

    @route.get("/param-lt/{item_id}")
    def get_path_param_lt(self, request, item_id: float = Path(..., lt=3)):
        return item_id

    @route.get("/param-lt0/{item_id}")
    def get_path_param_lt0(self, request, item_id: float = Path(..., lt=0)):
        return item_id

    @route.get("/param-le/{item_id}")
    def get_path_param_le(self, request, item_id: float = Path(..., le=3)):
        return item_id

    @route.get("/param-lt-gt/{item_id}")
    def get_path_param_lt_gt(self, request, item_id: float = Path(..., lt=3, gt=1)):
        return item_id

    @route.get("/param-le-ge/{item_id}")
    def get_path_param_le_ge(self, request, item_id: float = Path(..., le=3, ge=1)):
        return item_id

    @route.get("/param-lt-int/{item_id}")
    def get_path_param_lt_int(self, request, item_id: int = Path(..., lt=3)):
        return item_id

    @route.get("/param-gt-int/{item_id}")
    def get_path_param_gt_int(self, request, item_id: int = Path(..., gt=3)):
        return item_id

    @route.get("/param-le-int/{item_id}")
    def get_path_param_le_int(self, request, item_id: int = Path(..., le=3)):
        return item_id

    @route.get("/param-ge-int/{item_id}")
    def get_path_param_ge_int(self, request, item_id: int = Path(..., ge=3)):
        return item_id

    @route.get("/param-lt-gt-int/{item_id}")
    def get_path_param_lt_gt_int(self, request, item_id: int = Path(..., lt=3, gt=1)):
        return item_id

    @route.get("/param-le-ge-int/{item_id}")
    def get_path_param_le_ge_int(self, request, item_id: int = Path(..., le=3, ge=1)):
        return item_id

    @route.get("/param-pattern/{item_id}")
    def get_path_param_pattern(self, request, item_id: str = Path(..., pattern="^foo")):
        return item_id

    @route.get("/param-django-str/{str:item_id}")
    def get_path_param_django_str(self, request, item_id):
        return item_id

    @route.get("/param-django-int/{int:item_id}")
    def get_path_param_django_int(self, request, item_id: int):
        assert isinstance(item_id, int)
        return item_id

    @route.get("/param-django-int/not-an-int")
    def get_path_param_django_not_an_int(self, request):
        """Verify that url resolution for get_path_param_django_int passes non-ints forward"""
        return "Found not-an-int"

    @route.get("/param-django-int-str/{int:item_id}")
    def get_path_param_django_int_str(self, request, item_id: str):
        assert isinstance(item_id, str)
        return item_id

    @route.get("/param-django-slug/{slug:item_id}")
    def get_path_param_django_slug(self, request, item_id):
        return item_id

    @route.get("/param-django-uuid/{uuid:item_id}")
    def get_path_param_django_uuid(self, request, item_id: UUID):
        assert isinstance(item_id, UUID)
        return item_id

    @route.get("/param-django-uuid-str/{uuid:item_id}")
    def get_path_param_django_uuid_str(self, request, item_id):
        assert isinstance(item_id, str)
        return item_id

    @route.get("/param-django-path/{path:item_id}/after")
    def get_path_param_django_path(self, request, item_id):
        return item_id


class AliasedSchema(Schema):
    query: str = Field(..., alias="aliased.-_~name")


@api_controller("/query")
class QueryParamController:
    @route.get("/")
    def get_query(self, request, query):
        return f"foo bar {query}"

    @route.get("/optional")
    def get_query_optional(self, request, query=None):
        if query is None:
            return "foo bar"
        return f"foo bar {query}"

    @route.get("/int")
    def get_query_type(self, request, query: int):
        return f"foo bar {query}"

    @route.get("/int/optional")
    def get_query_type_optional(self, request, query: int = None):
        if query is None:
            return "foo bar"
        return f"foo bar {query}"

    @route.get("/int/default")
    def get_query_type_optional_10(self, request, query: int = 10):
        return f"foo bar {query}"

    @route.get("/list")
    def get_query_list(self, request, query: List[str] = Query(...)):
        return ",".join(query)

    @route.get("/list-optional")
    def get_query_optional_list(
        self, request, query: Optional[List[str]] = Query(None)
    ):
        if query:
            return ",".join(query)
        return query

    @route.get("/param")
    def get_query_param(self, request, query=Query(None)):
        if query is None:
            return "foo bar"
        return f"foo bar {query}"

    @route.get("/param-required")
    def get_query_param_required(self, request, query=Query(...)):
        return f"foo bar {query}"

    @route.get("/param-required/int")
    def get_query_param_required_type(self, request, query: int = Query(...)):
        return f"foo bar {query}"

    @route.get("/aliased-name")
    def get_query_aliased_name(self, request, query: AliasedSchema = Query(...)):
        return f"foo bar {query.query}"

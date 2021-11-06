import sys
from typing import Any, Generic, List, Optional, Type, TypeVar

from ninja import Schema
from ninja.constants import NOT_SET
from pydantic.generics import GenericModel
from pydantic.main import BaseModel
from pydantic.networks import AnyHttpUrl

T = TypeVar("T")

PaginatedResponseSchema = None


class BasePaginatedResponseSchema(Schema):
    count: int
    next: Optional[AnyHttpUrl]
    previous: Optional[AnyHttpUrl]
    results: List[Any]


if sys.version_info >= (3, 8):

    class PaginatedResponseSchema(
        GenericModel, Generic[T], BasePaginatedResponseSchema
    ):
        results: List[T]


def get_paginated_response_schema(
    item_schema: Type[Schema],
) -> Type[BasePaginatedResponseSchema]:
    # fix for paginatedResponseSchema for python 3.6 and 3.7 which doesn't support generic typing
    class ListResponseSchema(BasePaginatedResponseSchema):
        results: List[item_schema]  # type: ignore

    ListResponseSchema.__name__ = f"List{str(item_schema.__name__).capitalize()}"
    return ListResponseSchema


class RouteParameter(BaseModel):
    path: str
    methods: List[str]
    auth: Any = NOT_SET
    response: Any = NOT_SET
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    deprecated: Optional[bool] = None
    by_alias: bool = False
    exclude_unset: bool = False
    exclude_defaults: bool = False
    exclude_none: bool = False
    url_name: Optional[str] = None
    include_in_schema: bool = True

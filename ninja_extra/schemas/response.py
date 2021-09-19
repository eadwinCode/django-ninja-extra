import sys
from typing import Any, TypeVar, Optional, List, Generic
from ninja.constants import NOT_SET
from pydantic.main import BaseModel
from pydantic.networks import AnyHttpUrl
from pydantic.generics import GenericModel

T = TypeVar('T')

PaginatedResponseSchema = None

if sys.version_info >= (3, 8):
    class PaginatedResponseSchema(GenericModel, Generic[T]):
        count: int
        next: Optional[AnyHttpUrl]
        previous: Optional[AnyHttpUrl]
        results: List[T]


def get_paginated_response_schema(item_schema):
    # fix for paginatedResponseSchema for python 3.6 and 3.7 which doesn't support generic typing
    class ListResponseSchema(BaseModel):
        count: int
        next: Optional[AnyHttpUrl]
        previous: Optional[AnyHttpUrl]
        results: List[item_schema]
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

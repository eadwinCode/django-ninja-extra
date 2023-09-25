from typing import Any, Dict, Generic, List, Optional, TypeVar

from ninja import Schema
from ninja.constants import NOT_SET
from pydantic import validator
from pydantic.generics import GenericModel
from pydantic.networks import AnyHttpUrl

T = TypeVar("T")


class BasePaginatedResponseSchema(Schema):
    count: int
    next: Optional[AnyHttpUrl]
    previous: Optional[AnyHttpUrl]
    results: List[Any]


class BaseNinjaResponseSchema(Schema):
    count: int
    items: List[Any]


class PaginatedResponseSchema(GenericModel, Generic[T], BasePaginatedResponseSchema):
    results: List[T]


# Pydantic GenericModels has not way of identifying the _orig
# __generic_model__ is more like a fix for that
PaginatedResponseSchema.__generic_model__ = (  # type:ignore[attr-defined]
    PaginatedResponseSchema
)


class NinjaPaginationResponseSchema(GenericModel, Generic[T], BaseNinjaResponseSchema):
    items: List[T]

    @validator("items", pre=True)
    def validate_items(cls, value: Any) -> Any:
        if value is not None and not isinstance(value, list):
            value = list(value)
        return value


NinjaPaginationResponseSchema.__generic_model__ = (  # type:ignore[attr-defined]
    NinjaPaginationResponseSchema
)


class RouteParameter(Schema):
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
    openapi_extra: Optional[Dict[str, Any]]


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name in [
        "IdSchema",
        "OkSchema",
        "DetailSchema",
    ]:
        raise RuntimeError(f"'{name}' is no longer available")

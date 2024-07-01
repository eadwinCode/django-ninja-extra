import dataclasses
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from ninja import Schema
from ninja.constants import NOT_SET, NOT_SET_TYPE
from ninja.throttling import BaseThrottle
from pydantic import BeforeValidator, TypeAdapter, field_validator
from pydantic.networks import HttpUrl
from typing_extensions import Annotated

T = TypeVar("T")

Url = Annotated[
    str, BeforeValidator(lambda value: str(TypeAdapter(HttpUrl).validate_python(value)))
]


class BasePaginatedResponseSchema(Schema):
    count: int
    next: Optional[Url]
    previous: Optional[Url]
    results: List[Any]


class BaseNinjaResponseSchema(Schema):
    count: int
    items: List[Any]


class PaginatedResponseSchema(BasePaginatedResponseSchema, Generic[T]):
    results: List[T]


# Pydantic GenericModels has not way of identifying the _orig
# __generic_model__ is more like a fix for that
# PaginatedResponseSchema.__generic_model__ = (  # type:ignore[attr-defined]
#     PaginatedResponseSchema
# )


class NinjaPaginationResponseSchema(BaseNinjaResponseSchema, Generic[T]):
    items: List[T]

    @field_validator("items", mode="before")
    def validate_items(cls, value: Any) -> Any:
        if value is not None and not isinstance(value, list):
            value = list(value)
        return value


# NinjaPaginationResponseSchema.__generic_model__ = (  # type:ignore[attr-defined]
#     NinjaPaginationResponseSchema
# )


@dataclasses.dataclass
class RouteParameter:
    path: str
    methods: List[str]
    openapi_extra: Optional[Dict[str, Any]]
    auth: Optional[Union[Type, Any]] = None
    throttle: Union[BaseThrottle, List[BaseThrottle], NOT_SET_TYPE] = NOT_SET
    response: Optional[Union[Type, Any]] = None
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

    def dict(self) -> dict:
        return dataclasses.asdict(self)


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name in [
        "IdSchema",
        "OkSchema",
        "DetailSchema",
    ]:
        raise RuntimeError(f"'{name}' is no longer available")

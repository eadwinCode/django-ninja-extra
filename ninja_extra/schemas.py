from typing import TypeVar, Optional, List, Generic
from pydantic.generics import GenericModel
from ninja import Schema
from pydantic.networks import AnyHttpUrl

from typing import Generic, TypeVar, Type, Any, Tuple

from pydantic.generics import GenericModel

T = TypeVar('T')


class PaginatedResponseSchema(GenericModel, Generic[T]):
    count: int
    next: Optional[AnyHttpUrl]
    previous: Optional[AnyHttpUrl]
    results: List[T]


class PaginatedFilters(Schema):
    page: int = 1
    page_size: int = None

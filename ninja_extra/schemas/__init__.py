import typing as t

from .response import (
    NinjaPaginationResponseSchema,
    PaginatedResponseSchema,
    RouteParameter,
)

__all__ = ["PaginatedResponseSchema", "RouteParameter", "NinjaPaginationResponseSchema"]


def __getattr__(name: str) -> t.Any:  # pragma: no cover
    if name in [
        "IdSchema",
        "OkSchema",
        "DetailSchema",
    ]:
        raise RuntimeError(f"'{name}' is no longer available")

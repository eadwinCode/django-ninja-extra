import inspect
import logging
from typing import Any, Callable, Type, cast, overload

from ninja.constants import NOT_SET
from ninja.pagination import PaginationBase
from ninja.signature import is_async

from ninja_extra.lazy import settings_lazy
from ninja_extra.pagination.operations import (
    AsyncPaginatorOperation,
    PaginatorOperation,
)

logger = logging.getLogger()


@overload
def paginate() -> Callable[..., Any]:  # pragma: no cover
    ...


@overload
def paginate(
    func_or_pgn_class: Any = NOT_SET, **paginator_params: Any
) -> Callable[..., Any]:  # pragma: no cover
    ...


def paginate(
    func_or_pgn_class: Any = NOT_SET, **paginator_params: Any
) -> Callable[..., Any]:
    isfunction = inspect.isfunction(func_or_pgn_class)
    is_not_set = func_or_pgn_class == NOT_SET

    pagination_class: Type[PaginationBase] = cast(
        Type[PaginationBase], settings_lazy().PAGINATION_CLASS
    )

    if isfunction:
        return _inject_pagination(func_or_pgn_class, pagination_class)

    if not is_not_set:
        pagination_class = func_or_pgn_class

    def wrapper(func: Callable[..., Any]) -> Any:
        return _inject_pagination(func, pagination_class, **paginator_params)

    return wrapper


def _inject_pagination(
    func: Callable[..., Any],
    paginator_class: Type[PaginationBase],
    **paginator_params: Any,
) -> Callable[..., Any]:
    paginator: PaginationBase = paginator_class(**paginator_params)
    paginator_kwargs_name = "pagination"
    paginator_operation_class = PaginatorOperation

    if is_async(func):
        paginator_operation_class = AsyncPaginatorOperation
    paginator_operation = paginator_operation_class(
        paginator=paginator, view_func=func, paginator_kwargs_name=paginator_kwargs_name
    )

    return paginator_operation.as_view

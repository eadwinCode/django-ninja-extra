import inspect
import typing as t

from ninja.constants import NOT_SET
from ninja.signature import is_async

from ninja_extra.interfaces.searching import SearchingBase
from ninja_extra.lazy import settings_lazy

from .operations import (
    AsyncSearcheratorOperation,
    SearcheratorOperation,
)


@t.overload
def searching() -> t.Callable[..., t.Any]:  # pragma: no cover
    ...


@t.overload
def searching(
    func_or_searching_class: t.Any = NOT_SET, **searching_params: t.Any
) -> t.Callable[..., t.Any]:  # pragma: no cover
    ...


def searching(
    func_or_searching_class: t.Any = NOT_SET, **searching_params: t.Any
) -> t.Callable[..., t.Any]:
    isfunction = inspect.isfunction(func_or_searching_class)
    isnotset = func_or_searching_class == NOT_SET

    searching_class: t.Type[SearchingBase] = t.cast(
        t.Type[SearchingBase], settings_lazy().SEARCHING_CLASS
    )

    if isfunction:
        return _inject_searcherator(func_or_searching_class, searching_class)

    if not isnotset:
        searching_class = func_or_searching_class

    def wrapper(func: t.Callable[..., t.Any]) -> t.Any:
        return _inject_searcherator(func, searching_class, **searching_params)

    return wrapper


def _inject_searcherator(
    func: t.Callable[..., t.Any],
    searching_class: t.Type[SearchingBase],
    **searching_params: t.Any,
) -> t.Callable[..., t.Any]:
    searcherator: SearchingBase = searching_class(**searching_params)
    searcherator_kwargs_name = "searching"
    searcherator_operation_class = SearcheratorOperation
    if is_async(func):
        searcherator_operation_class = AsyncSearcheratorOperation
    searcherator_operation = searcherator_operation_class(
        searcherator=searcherator,
        view_func=func,
        searcherator_kwargs_name=searcherator_kwargs_name,
    )

    return searcherator_operation.as_view

import inspect
import logging
import typing as t

from ninja.constants import NOT_SET
from ninja.signature import is_async

from ninja_extra.interfaces.ordering import OrderingBase
from ninja_extra.lazy import settings_lazy

from .operation import AsyncOrderatorOperation, OrderatorOperation

logger = logging.getLogger()


@t.overload
def ordering() -> t.Callable[..., t.Any]:  # pragma: no cover
    ...


@t.overload
def ordering(
    func_or_ordering_class: t.Any = NOT_SET, **paginator_params: t.Any
) -> t.Callable[..., t.Any]:  # pragma: no cover
    ...


def ordering(
    func_or_ordering_class: t.Any = NOT_SET, **ordering_params: t.Any
) -> t.Callable[..., t.Any]:
    isfunction = inspect.isfunction(func_or_ordering_class)
    isnotset = func_or_ordering_class == NOT_SET

    ordering_class: t.Type[OrderingBase] = t.cast(
        t.Type[OrderingBase], settings_lazy().ORDERING_CLASS
    )

    if isfunction:
        return _inject_orderator(func_or_ordering_class, ordering_class)

    if not isnotset:
        ordering_class = func_or_ordering_class

    def wrapper(func: t.Callable[..., t.Any]) -> t.Any:
        return _inject_orderator(func, ordering_class, **ordering_params)

    return wrapper


def _inject_orderator(
    func: t.Callable[..., t.Any],
    ordering_class: t.Type[OrderingBase],
    **ordering_params: t.Any,
) -> t.Callable[..., t.Any]:
    orderator: OrderingBase = ordering_class(**ordering_params)
    orderator_kwargs_name = "ordering"
    orderator_operation_class = OrderatorOperation
    if is_async(func):
        orderator_operation_class = AsyncOrderatorOperation
    orderator_operation = orderator_operation_class(
        orderator=orderator, view_func=func, orderator_kwargs_name=orderator_kwargs_name
    )

    return orderator_operation.as_view

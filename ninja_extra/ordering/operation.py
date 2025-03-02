import logging
import typing as t
from functools import wraps

from asgiref.sync import sync_to_async
from django.http import HttpRequest

from ninja_extra.interfaces.ordering import OrderingBase
from ninja_extra.shortcuts import add_ninja_contribute_args

logger = logging.getLogger()

if t.TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers.base import ControllerBase


class OrderatorOperation:
    def __init__(
        self,
        *,
        orderator: OrderingBase,
        view_func: t.Callable,
        orderator_kwargs_name: str = "ordering",
    ) -> None:
        self.orderator = orderator
        self.orderator_kwargs_name = orderator_kwargs_name
        self.view_func = view_func

        orderator_view = self.get_view_function()
        self.as_view = wraps(view_func)(orderator_view)
        add_ninja_contribute_args(
            self.as_view,
            (
                self.orderator_kwargs_name,
                self.orderator.Input,
                self.orderator.InputSource,
            ),
        )
        orderator_view.orderator_operation = self  # type:ignore[attr-defined]

    @property
    def view_func_has_kwargs(self) -> bool:  # pragma: no cover
        return self.orderator.pass_parameter is not None

    def get_view_function(self) -> t.Callable:
        def as_view(
            request_or_controller: t.Union["ControllerBase", HttpRequest],
            *args: t.Any,
            **kw: t.Any,
        ) -> t.Any:
            func_kwargs = dict(**kw)
            ordering_params = func_kwargs.pop(self.orderator_kwargs_name)
            if self.orderator.pass_parameter:
                func_kwargs[self.orderator.pass_parameter] = ordering_params

            items = self.view_func(request_or_controller, *args, **func_kwargs)
            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items
            return self.orderator.ordering_queryset(items, ordering_params)

        return as_view


class AsyncOrderatorOperation(OrderatorOperation):
    def get_view_function(self) -> t.Callable:
        async def as_view(
            request_or_controller: t.Union["ControllerBase", HttpRequest],
            *args: t.Any,
            **kw: t.Any,
        ) -> t.Any:
            func_kwargs = dict(**kw)
            ordering_params = func_kwargs.pop(self.orderator_kwargs_name)
            if self.orderator.pass_parameter:
                func_kwargs[self.orderator.pass_parameter] = ordering_params

            items = await self.view_func(request_or_controller, *args, **func_kwargs)

            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items

            ordering_queryset = t.cast(
                t.Callable, sync_to_async(self.orderator.ordering_queryset)
            )
            return await ordering_queryset(items, ordering_params)

        return as_view

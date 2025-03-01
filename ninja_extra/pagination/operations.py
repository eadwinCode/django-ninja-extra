from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Union,
    cast,
)

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from ninja.pagination import PaginationBase

from ninja_extra.context import RouteContext
from ninja_extra.shortcuts import add_ninja_contribute_args

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers import ControllerBase


class PaginatorOperation:
    def __init__(
        self,
        *,
        paginator: PaginationBase,
        view_func: Callable,
        paginator_kwargs_name: str = "pagination",
    ) -> None:
        self.paginator = paginator
        self.paginator_kwargs_name = paginator_kwargs_name
        self.view_func = view_func

        paginator_view = self.get_view_function()
        self.as_view = wraps(view_func)(paginator_view)
        add_ninja_contribute_args(
            self.as_view,
            (
                self.paginator_kwargs_name,
                self.paginator.Input,
                self.paginator.InputSource,
            ),
        )
        paginator_view.paginator_operation = self  # type:ignore[attr-defined]

    @property
    def view_func_has_kwargs(self) -> bool:  # pragma: no cover
        return self.paginator.pass_parameter is not None

    def get_view_function(self) -> Callable:
        def as_view(
            request_or_controller: Union["ControllerBase", HttpRequest],
            *args: Any,
            **kw: Any,
        ) -> Any:
            func_kwargs = dict(**kw)
            pagination_params = func_kwargs.pop(self.paginator_kwargs_name)
            if self.paginator.pass_parameter:
                func_kwargs[self.paginator.pass_parameter] = pagination_params

            items = self.view_func(request_or_controller, *args, **func_kwargs)

            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items

            if hasattr(request_or_controller, "context") and isinstance(
                request_or_controller.context, RouteContext
            ):
                request = request_or_controller.context.request
                assert request, "Request object is None"
            else:
                request = request_or_controller
            params = dict(kw)
            params["request"] = request
            return self.paginator.paginate_queryset(items, **params)

        return as_view


class AsyncPaginatorOperation(PaginatorOperation):
    def get_view_function(self) -> Callable:
        async def as_view(
            request_or_controller: Union["ControllerBase", HttpRequest],
            *args: Any,
            **kw: Any,
        ) -> Any:
            func_kwargs = dict(**kw)
            pagination_params = func_kwargs.pop(self.paginator_kwargs_name)
            if self.paginator.pass_parameter:
                func_kwargs[self.paginator.pass_parameter] = pagination_params

            items = await self.view_func(request_or_controller, *args, **func_kwargs)

            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items

            if hasattr(request_or_controller, "context") and isinstance(
                request_or_controller.context, RouteContext
            ):
                request = request_or_controller.context.request
                assert request, "Request object is None"
            else:
                request = request_or_controller
            params = dict(kw)
            params["request"] = request
            paginate_queryset = cast(
                Callable, sync_to_async(self.paginator.paginate_queryset)
            )
            return await paginate_queryset(items, **params)

        return as_view

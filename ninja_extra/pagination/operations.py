from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Tuple,
    cast,
)

from asgiref.sync import sync_to_async
from ninja.pagination import PaginationBase

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
        _ninja_contribute_args: List[Tuple] = getattr(
            self.view_func, "_ninja_contribute_args", []
        )
        paginator_view._ninja_contribute_args = (  # type:ignore[attr-defined]
            _ninja_contribute_args
        )
        add_ninja_contribute_args(
            paginator_view,
            (
                self.paginator_kwargs_name,
                self.paginator.Input,
                self.paginator.InputSource,
            ),
        )
        paginator_view.paginator_operation = self  # type:ignore[attr-defined]
        self.as_view = wraps(view_func)(paginator_view)

    @property
    def view_func_has_kwargs(self) -> bool:  # pragma: no cover
        return self.paginator.pass_parameter is not None

    def get_view_function(self) -> Callable:
        def as_view(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
            func_kwargs = dict(**kw)
            pagination_params = func_kwargs.pop(self.paginator_kwargs_name)
            if self.paginator.pass_parameter:
                func_kwargs[self.paginator.pass_parameter] = pagination_params

            items = self.view_func(controller, *args, **func_kwargs)
            assert (
                controller.context and controller.context.request
            ), "Request object is None"
            params = dict(kw)
            params["request"] = controller.context.request
            return self.paginator.paginate_queryset(items, **params)

        return as_view


class AsyncPaginatorOperation(PaginatorOperation):
    def get_view_function(self) -> Callable:
        async def as_view(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
            func_kwargs = dict(**kw)
            pagination_params = func_kwargs.pop(self.paginator_kwargs_name)
            if self.paginator.pass_parameter:
                func_kwargs[self.paginator.pass_parameter] = pagination_params

            items = await self.view_func(controller, *args, **func_kwargs)
            assert (
                controller.context and controller.context.request
            ), "Request object is None"

            params = dict(kw)
            params["request"] = controller.context.request
            paginate_queryset = cast(
                Callable, sync_to_async(self.paginator.paginate_queryset)
            )
            return await paginate_queryset(items, **params)

        return as_view

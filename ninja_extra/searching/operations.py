import typing as t
from functools import wraps

from asgiref.sync import sync_to_async

from ninja_extra.interfaces.searching import SearchingBase
from ninja_extra.shortcuts import add_ninja_contribute_args

if t.TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers import ControllerBase


class SearcheratorOperation:
    def __init__(
        self,
        *,
        searcherator: SearchingBase,
        view_func: t.Callable,
        searcherator_kwargs_name: str = "searching",
    ) -> None:
        self.searcherator = searcherator
        self.searcherator_kwargs_name = searcherator_kwargs_name
        self.view_func = view_func

        searcherator_view = self.get_view_function()
        self.as_view = wraps(view_func)(searcherator_view)
        add_ninja_contribute_args(
            self.as_view,
            (
                self.searcherator_kwargs_name,
                self.searcherator.Input,
                self.searcherator.InputSource,
            ),
        )
        searcherator_view.searcherator_operation = self  # type:ignore[attr-defined]

    @property
    def view_func_has_kwargs(self) -> bool:  # pragma: no cover
        return self.searcherator.pass_parameter is not None

    def get_view_function(self) -> t.Callable:
        def as_view(controller: "ControllerBase", *args: t.Any, **kw: t.Any) -> t.Any:
            func_kwargs = dict(**kw)
            searching_params = func_kwargs.pop(self.searcherator_kwargs_name)
            if self.searcherator.pass_parameter:
                func_kwargs[self.searcherator.pass_parameter] = searching_params

            items = self.view_func(controller, *args, **func_kwargs)
            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items

            return self.searcherator.searching_queryset(items, searching_params)

        return as_view


class AsyncSearcheratorOperation(SearcheratorOperation):
    def get_view_function(self) -> t.Callable:
        async def as_view(
            controller: "ControllerBase", *args: t.Any, **kw: t.Any
        ) -> t.Any:
            func_kwargs = dict(**kw)
            searching_params = func_kwargs.pop(self.searcherator_kwargs_name)
            if self.searcherator.pass_parameter:
                func_kwargs[self.searcherator.pass_parameter] = searching_params

            items = await self.view_func(controller, *args, **func_kwargs)

            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items

            searching_queryset = t.cast(
                t.Callable, sync_to_async(self.searcherator.searching_queryset)
            )
            return await searching_queryset(items, searching_params)

        return as_view

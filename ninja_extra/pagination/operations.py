from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Type,
    Union,
    cast,
)

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from ninja import FilterSchema, Query
from ninja.pagination import AsyncPaginationBase, PaginationBase

from ninja_extra.constants import PAGINATOR_OBJECT
from ninja_extra.context import RouteContext
from ninja_extra.reflect import reflect
from ninja_extra.shortcuts import add_ninja_contribute_args

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers import ControllerBase

import django


class PaginatorOperation:
    def __init__(
        self,
        *,
        paginator: Union[PaginationBase, AsyncPaginationBase],
        view_func: Callable,
        paginator_kwargs_name: str = "pagination",
        filter_schema: Optional[Type[FilterSchema]] = None,
    ) -> None:
        self.paginator = paginator
        self.paginator_kwargs_name = paginator_kwargs_name
        self.view_func = view_func
        self.filter_schema = filter_schema
        self.filter_kwargs_name = "filters"

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
        # Add filter_schema as a contribute arg if provided
        if self.filter_schema:
            add_ninja_contribute_args(
                self.as_view,
                (
                    self.filter_kwargs_name,
                    self.filter_schema,
                    Query(...),
                ),
            )
        reflect.define_metadata(PAGINATOR_OBJECT, self, paginator_view)

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

            # Extract filter parameters if filter_schema is provided
            filter_params = None
            if self.filter_schema:
                filter_params = func_kwargs.pop(self.filter_kwargs_name, None)

            items = self.view_func(request_or_controller, *args, **func_kwargs)

            # Apply filters if filter_schema is provided and filter_params exist
            if self.filter_schema and filter_params:
                items = filter_params.filter(items)

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

            # Extract filter parameters if filter_schema is provided
            filter_params = None
            if self.filter_schema:
                filter_params = func_kwargs.pop(self.filter_kwargs_name, None)

            items = await self.view_func(request_or_controller, *args, **func_kwargs)

            # Apply filters if filter_schema is provided and filter_params exist
            if self.filter_schema and filter_params:
                items = filter_params.filter(items)

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
            is_supported_async_orm = django.VERSION >= (4, 2)
            if (
                isinstance(self.paginator, AsyncPaginationBase)
                and is_supported_async_orm
            ):
                paginate_queryset = self.paginator.apaginate_queryset
            else:
                paginate_queryset = cast(
                    Callable, sync_to_async(self.paginator.paginate_queryset)
                )
            return await paginate_queryset(items, **params)

        return as_view

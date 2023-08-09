import inspect
import logging
from collections import OrderedDict
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
    overload,
)

from asgiref.sync import sync_to_async
from django.core.paginator import InvalidPage, Page, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Schema
from ninja.constants import NOT_SET
from ninja.pagination import LimitOffsetPagination, PageNumberPagination, PaginationBase
from ninja.signature import is_async
from ninja.types import DictStrAny
from pydantic import Field

from ninja_extra.conf import settings
from ninja_extra.exceptions import NotFound
from ninja_extra.schemas import PaginatedResponseSchema
from ninja_extra.shortcuts import add_ninja_contribute_args
from ninja_extra.urls import remove_query_param, replace_query_param

logger = logging.getLogger()

if TYPE_CHECKING:  # pragma: no cover
    from .controllers import ControllerBase

__all__ = [
    "PageNumberPagination",
    "PageNumberPaginationExtra",
    "PaginationBase",
    "LimitOffsetPagination",
    "paginate",
    "PaginatedResponseSchema",
    "PaginatorOperation",
    "AsyncPaginatorOperation",
]


class PageNumberPaginationExtra(PaginationBase):
    class Input(Schema):
        page: int = Field(1, gt=0)
        page_size: int = Field(100, lt=200)

    page_query_param = "page"
    page_size_query_param = "page_size"

    max_page_size = 200
    paginator_class = Paginator

    def __init__(
        self,
        page_size: int = settings.PAGINATION_PER_PAGE,
        max_page_size: Optional[int] = None,
        pass_parameter: Optional[str] = None,
    ) -> None:
        super().__init__(pass_parameter=pass_parameter)
        self.page_size = page_size
        self.max_page_size = max_page_size or 200
        self.Input = self.create_input()  # type:ignore

    def create_input(self) -> Type[Input]:
        class DynamicInput(PageNumberPaginationExtra.Input):
            page: int = Field(1, gt=0)
            page_size: int = Field(self.page_size, lt=self.max_page_size)

        return DynamicInput

    def paginate_queryset(
        self,
        queryset: QuerySet,
        pagination: Input,
        request: Optional[HttpRequest] = None,
        **params: DictStrAny,
    ) -> Any:
        assert request, "request is required"
        current_page_number = pagination.page
        paginator = self.paginator_class(queryset, pagination.page_size)
        try:
            url = request.build_absolute_uri()
            page: Page = paginator.page(current_page_number)
            return self.get_paginated_response(base_url=url, page=page)
        except InvalidPage as exc:  # pragma: no cover
            msg = "Invalid page. {page_number} {message}".format(
                page_number=current_page_number, message=str(exc)
            )
            raise NotFound(msg) from exc

    def get_paginated_response(self, *, base_url: str, page: Page) -> DictStrAny:
        return OrderedDict(
            [
                ("count", page.paginator.count),
                ("next", self.get_next_link(base_url, page=page)),
                ("previous", self.get_previous_link(base_url, page=page)),
                ("results", list(page)),
            ]
        )

    @classmethod
    def get_response_schema(
        cls, response_schema: Union[Type[Schema], Type[Any]]
    ) -> Any:
        return PaginatedResponseSchema[response_schema]  # type: ignore[valid-type]

    def get_next_link(self, url: str, page: Page) -> Optional[str]:
        if not page.has_next():
            return None
        page_number = page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self, url: str, page: Page) -> Optional[str]:
        if not page.has_previous():
            return None
        page_number = page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)


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
    isnotset = func_or_pgn_class == NOT_SET

    pagination_class: Type[PaginationBase] = settings.PAGINATION_CLASS

    if isfunction:
        return _inject_pagination(func_or_pgn_class, pagination_class)

    if not isnotset:
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

import inspect
import sys
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Type, TYPE_CHECKING

from django.core.paginator import InvalidPage, Paginator, Page
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.module_loading import import_string
from ninja import Schema
from ninja_extra.exceptions import NotFound
from ninja.conf import settings
from ninja.constants import NOT_SET
from ninja.errors import ConfigError
from ninja.signature import has_kwargs
from ninja.types import DictStrAny
from ninja.pagination import PageNumberPagination, PaginationBase, LimitOffsetPagination
from ninja_extra.urls import replace_query_param, remove_query_param
from pydantic import Field
from ninja_extra.schemas import PaginatedResponseSchema, get_paginated_response_schema

if TYPE_CHECKING:
    from .controllers import APIController

__all__ = [
    "PageNumberPagination",
    "PageNumberPaginationExtra",
    "PaginationBase",
    "LimitOffsetPagination",
    "paginate"
]


def _positive_int(integer_string, strict=False, cutoff=None):
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret < 0 or (ret == 0 and strict):
        raise ValueError()
    if cutoff:
        return min(ret, cutoff)
    return ret


class PageNumberPaginationExtra(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'page_size'

    max_page_size = 200
    paginator_class: Paginator = Paginator

    def __init__(self, page_size=None, max_page_size=None) -> None:
        self.page_size = page_size or settings.PAGINATION_PER_PAGE
        self.max_page_size = max_page_size or 200
        super().__init__(page_size=page_size)
        self.Input = self.create_input()

    def create_input(self) -> Schema:
        class Input(Schema):
            page: int = Field(1, gt=0)
            page_size: int = Field(self.page_size, lt=self.max_page_size)
        return Input

    def paginate_queryset(
            self, items: QuerySet, request: HttpRequest, **params: DictStrAny
    ) -> QuerySet:

        pagination_input: "PageNumberPaginationExtra.Input" = params["pagination"]
        page_size = self.get_page_size(pagination_input.page_size)
        page = pagination_input.page
        paginator = self.paginator_class(items, page_size)
        try:
            url = request.build_absolute_uri()
            page = paginator.page(page)
            return self.get_paginated_response(base_url=url, page=page)
        except InvalidPage as exc:
            msg = 'Invalid page. {page_number} {message}'.format(
                page_number=page, message=str(exc)
            )
            raise NotFound(msg)

    def get_paginated_response(self, *, base_url: str, page: Page) -> DictStrAny:
        return OrderedDict([
            ('count', page.paginator.count),
            ('next', self.get_next_link(base_url, page=page)),
            ('previous', self.get_previous_link(base_url, page=page)),
            ('results', list(page))
        ])

    @classmethod
    def get_response_schema(cls, response_schema: Schema) -> Schema:
        if sys.version_info >= (3, 8):
            return PaginatedResponseSchema[response_schema]
        return get_paginated_response_schema(response_schema)

    def get_next_link(self, url: str, page: Page):
        if not page.has_next():
            return None
        page_number = page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self, url: str, page: Page):
        if not page.has_previous():
            return None
        page_number = page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)

    def get_page_size(self, page_size: int):
        if page_size:
            try:
                return _positive_int(
                    page_size,
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size


def paginate(
    func_or_pgn_class: Any = NOT_SET, **paginator_params: DictStrAny
) -> Callable:

    isfunction = inspect.isfunction(func_or_pgn_class)
    isnotset = func_or_pgn_class == NOT_SET

    pagination_class: Type[PaginationBase] = import_string(settings.PAGINATION_CLASS)

    if isfunction:
        return _inject_pagination(func_or_pgn_class, pagination_class)

    if not isnotset:
        pagination_class = func_or_pgn_class

    def wrapper(func: Callable) -> Any:
        return _inject_pagination(func, pagination_class, **paginator_params)

    return wrapper


def _inject_pagination(
    func: Callable,
    paginator_class: Type[PaginationBase],
    **paginator_params: DictStrAny,
) -> Callable:
    if not has_kwargs(func):
        raise ConfigError(
            f"function {func.__name__} must have **kwargs argument to be used with pagination"
        )

    paginator: PaginationBase = paginator_class(**paginator_params)

    @wraps(func)
    def view_with_pagination(controller: "APIController", *args, **kw: DictStrAny) -> Any:
        items = func(controller, *args, **kw)
        return paginator.paginate_queryset(items, controller.request, **kw)

    view_with_pagination._ninja_contribute_args = [  # type: ignore
        (
            "pagination",
            paginator.Input,
            paginator.InputSource,
        ),
    ]

    return view_with_pagination

import inspect
import operator
from abc import ABC, abstractmethod
from functools import reduce, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Optional,
    Tuple,
    Type,
    cast,
    overload,
)

from asgiref.sync import sync_to_async
from django.db.models import Q, QuerySet
from django.db.models.constants import LOOKUP_SEP
from ninja import Field, Query, Schema
from ninja.constants import NOT_SET
from ninja.signature import is_async

from ninja_extra.conf import settings
from ninja_extra.shortcuts import add_ninja_contribute_args

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers import ControllerBase

__all__ = [
    "SearchingBase",
    "Searching",
    "searching",
    "SearcheratorOperation",
    "AsyncSearcheratorOperation",
]


class SearchingBase(ABC):
    class Input(Schema):
        ...

    lookup_prefixes = {
        "^": "istartswith",
        "=": "iexact",
        "@": "search",
        "$": "iregex",
    }
    InputSource = Query(...)

    def __init__(self, *, pass_parameter: Optional[str] = None, **kwargs: Any) -> None:
        self.pass_parameter = pass_parameter

    @abstractmethod
    def searching_queryset(self, queryset: QuerySet, searching_input: Any) -> QuerySet:
        ...


class Searching(SearchingBase):
    class Input(Schema):
        search: Optional[str] = Field(None)

    def __init__(
        self,
        search_fields: Optional[List[str]] = None,
        pass_parameter: Optional[str] = None,
    ) -> None:
        self.search_fields = search_fields
        self.pass_parameter = pass_parameter
        self.Input = self.create_input()  # type:ignore

    def create_input(self) -> Type[Input]:
        class DynamicInput(Searching.Input):
            search: Optional[str] = Field(None)

        return DynamicInput

    def searching_queryset(
        self, queryset: QuerySet, searching_input: Input
    ) -> QuerySet:

        search_terms = self.get_search_terms(searching_input.search)

        if not self.search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field))
            for search_field in self.search_fields
        ]
        conditions = []
        for search_term in search_terms:
            queries = [Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups]
            conditions.append(reduce(operator.or_, queries))
        return queryset.filter(reduce(operator.and_, conditions))

    def get_search_terms(self, value: Optional[str]) -> List[str]:
        if value:
            value = value.replace("\x00", "")  # strip null characters
            value = value.replace(",", " ")
            return value.split()
        return []

    def construct_search(self, field_name: str) -> str:
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = "icontains"
        return LOOKUP_SEP.join([field_name, lookup])


@overload
def searching() -> Callable[..., Any]:  # pragma: no cover
    ...


@overload
def searching(
    func_or_searching_class: Any = NOT_SET, **searching_params: Any
) -> Callable[..., Any]:  # pragma: no cover
    ...


def searching(
    func_or_searching_class: Any = NOT_SET, **searching_params: Any
) -> Callable:
    isfunction = inspect.isfunction(func_or_searching_class)
    isnotset = func_or_searching_class == NOT_SET

    searching_class: Type[SearchingBase] = settings.SEARCHING_CLASS

    if isfunction:
        return _inject_searcherator(func_or_searching_class, searching_class)

    if not isnotset:
        searching_class = func_or_searching_class

    def wrapper(func: Callable[..., Any]) -> Any:
        return _inject_searcherator(func, searching_class, **searching_params)

    return wrapper


def _inject_searcherator(
    func: Callable[..., Any],
    searching_class: Type[SearchingBase],
    **searching_params: Any,
) -> Callable[..., Any]:
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


class SearcheratorOperation:
    def __init__(
        self,
        *,
        searcherator: SearchingBase,
        view_func: Callable,
        searcherator_kwargs_name: str = "searching",
    ) -> None:
        self.searcherator = searcherator
        self.searcherator_kwargs_name = searcherator_kwargs_name
        self.view_func = view_func

        searcherator_view = self.get_view_function()
        _ninja_contribute_args: List[Tuple] = getattr(
            self.view_func, "_ninja_contribute_args", []
        )
        setattr(searcherator_view, "_ninja_contribute_args", _ninja_contribute_args)
        add_ninja_contribute_args(
            searcherator_view,
            (
                self.searcherator_kwargs_name,
                self.searcherator.Input,
                self.searcherator.InputSource,
            ),
        )
        setattr(searcherator_view, "searcherator_operation", self)
        self.as_view = wraps(view_func)(searcherator_view)

    @property
    def view_func_has_kwargs(self) -> bool:  # pragma: no cover
        return self.searcherator.pass_parameter is not None

    def get_view_function(self) -> Callable:
        def as_view(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
            func_kwargs = dict(**kw)
            searching_params = func_kwargs.pop(self.searcherator_kwargs_name)
            if self.searcherator.pass_parameter:
                func_kwargs[self.searcherator.pass_parameter] = searching_params

            items = self.view_func(controller, *args, **func_kwargs)
            return self.searcherator.searching_queryset(items, searching_params)

        return as_view


class AsyncSearcheratorOperation(SearcheratorOperation):
    def get_view_function(self) -> Callable:
        async def as_view(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
            func_kwargs = dict(**kw)
            searching_params = func_kwargs.pop(self.searcherator_kwargs_name)
            if self.searcherator.pass_parameter:
                func_kwargs[self.searcherator.pass_parameter] = searching_params

            items = await self.view_func(controller, *args, **func_kwargs)
            searching_queryset = cast(
                Callable, sync_to_async(self.searcherator.searching_queryset)
            )
            return await searching_queryset(items, searching_params)

        return as_view

import inspect
import operator
import re
from abc import ABC, abstractmethod
from functools import reduce, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
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


def _istartswith(a: str, b: str) -> bool:
    return a.startswith(b)


def _isiexact(a: str, b: str) -> bool:
    return a.lower() == b.lower()


def _isiregex(a: str, b: str) -> bool:
    return bool(re.search(b, a, re.IGNORECASE))


def _isicontains(a: str, b: str) -> bool:
    return b.lower() in a.lower()


class SearchingBase(ABC):
    class Input(Schema): ...

    InputSource = Query(...)

    def __init__(self, *, pass_parameter: Optional[str] = None, **kwargs: Any) -> None:
        self.pass_parameter = pass_parameter

    @abstractmethod
    def searching_queryset(
        self, items: Union[QuerySet, List], searching_input: Any
    ) -> Union[QuerySet, List]: ...


class Searching(SearchingBase):
    class Input(Schema):
        search: Optional[str] = Field(None)

    lookup_prefixes = {
        "^": "istartswith",
        "=": "iexact",
        "@": "search",
        "$": "iregex",
    }

    lookup_prefixes_list = {
        "^": _istartswith,
        "=": _isiexact,
        "$": _isiregex,
    }

    def __init__(
        self,
        search_fields: Optional[List[str]] = None,
        pass_parameter: Optional[str] = None,
    ) -> None:
        super().__init__(pass_parameter=pass_parameter)
        self.search_fields = search_fields or []

    def searching_queryset(
        self, items: Union[QuerySet, List], searching_input: Input
    ) -> Union[QuerySet, List]:
        search_terms = self.get_search_terms(searching_input.search)

        if self.search_fields and search_terms:
            if isinstance(items, QuerySet):
                conditions_queryset = self.construct_conditions_for_queryset(
                    search_terms
                )
                return items.filter(reduce(operator.and_, conditions_queryset))
            elif isinstance(items, list):
                conditions_list = self.construct_conditions_for_list(search_terms)
                return [
                    item for item in items if self.filter_spec(item, conditions_list)
                ]
        return items

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

    def construct_conditions_for_queryset(self, search_terms: List[str]) -> List[Q]:
        orm_lookups = [
            self.construct_search(str(search_field))
            for search_field in self.search_fields
        ]
        conditions = []
        for search_term in search_terms:
            queries = [Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups]
            conditions.append(reduce(operator.or_, queries))
        return conditions

    def construct_conditions_for_list(
        self, search_terms: List[str]
    ) -> Dict[str, List[Tuple[Callable, str]]]:
        lookups = self.construct_search_for_list()
        conditions: Dict[str, List[Tuple[Callable, str]]] = {
            field_name: [] for field_name in lookups.keys()
        }
        for search_term in search_terms:
            for field_name, lookup in lookups.items():
                conditions[field_name].append((lookup, search_term))
        return conditions

    def construct_search_for_list(self) -> Dict[str, Callable]:
        def get_lookup(prefix: str) -> Callable:
            return self.lookup_prefixes_list.get(prefix, _isicontains)

        return {
            field_name[1:]
            if (self.lookup_prefixes_list.get(field_name[0]))
            else field_name: get_lookup(field_name[0])
            for field_name in self.search_fields
        }

    def filter_spec(
        self, item: Any, conditions: Dict[str, List[Tuple[Callable, str]]]
    ) -> bool:
        item_getter = (
            operator.itemgetter if isinstance(item, dict) else operator.attrgetter
        )
        for field, lookup in conditions.items():
            if not any(
                lookup_func(item_getter(field)(item), lookup_value)
                for lookup_func, lookup_value in lookup
            ):
                return False
        return True


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
) -> Callable[..., Any]:
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

    def get_view_function(self) -> Callable:
        def as_view(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
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
    def get_view_function(self) -> Callable:
        async def as_view(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
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

            searching_queryset = cast(
                Callable, sync_to_async(self.searcherator.searching_queryset)
            )
            return await searching_queryset(items, searching_params)

        return as_view

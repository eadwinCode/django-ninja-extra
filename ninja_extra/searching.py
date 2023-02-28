import inspect
import operator
from functools import reduce, wraps
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Type

from django.db.models import Q, QuerySet
from django.db.models.constants import LOOKUP_SEP
from ninja import Field, Query, Schema
from ninja.constants import NOT_SET

from ninja_extra.conf import settings

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers import ControllerBase


class Search:

    class Input(Schema):
        search: Optional[str] = Field(None)

    lookup_prefixes = {
        '^': 'istartswith',
        '=': 'iexact',
        '@': 'search',
        '$': 'iregex',
    }
    input_source = Query(...)

    def __init__(self, search_fields: List[str], pass_parameter: Optional[str] = None) -> None:
        self.search_fields = search_fields
        self.pass_parameter = pass_parameter

    def search_queryset(self, queryset: QuerySet, searching: Input):
        if searching.search:
            search_terms = self.get_search_terms(searching.search)

            if not self.search_fields or not search_terms:
                return queryset

            orm_lookups = [self.construct_search(str(search_field)) for search_field in self.search_fields]
            conditions = []
            for search_term in search_terms:
                queries = [Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups]
                conditions.append(reduce(operator.or_, queries))
            queryset = queryset.filter(reduce(operator.and_, conditions))
        return queryset

    def get_search_terms(self, value: str):
        if value:
            value = value.replace('\x00', '')  # strip null characters
            value = value.replace(',', ' ')
            return value.split()
        return ''

    def construct_search(self, field_name):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = 'icontains'
        return LOOKUP_SEP.join([field_name, lookup])


def searching(func_or_searching_class: Type[Search] = NOT_SET, **searching_params: Any) -> Callable:
    isfunction = inspect.isfunction(func_or_searching_class)
    isnotset = func_or_searching_class == NOT_SET
    searching_class: Type[Search] = settings.SEARCHING_CLASS
    if isfunction:
        return _inject_searcherator(func_or_searching_class, searching_class)
    if not isnotset:
        searching_class = func_or_searching_class

    def wrapper(func: Callable[..., Any]) -> Any:
        return _inject_searcherator(func, searching_class, **searching_params)

    return wrapper


def _inject_searcherator(
    func: Callable[..., Any],
    searching_class: Type[Search],
    **searching_params: Any,
) -> Callable[..., Any]:
    searcherator: Search = searching_class(**searching_params)
    searcherator_kwargs_name = "searching"
    _ninja_contribute_args: List[Tuple] = getattr(func, "_ninja_contribute_args", [])

    @wraps(func)
    def view_with_searching(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
        func_kwargs = dict(**kw)
        searching = func_kwargs.pop(searcherator_kwargs_name)
        if searcherator.pass_parameter:
            func_kwargs[searcherator.pass_parameter] = searching_params
        items = func(controller, *args, **func_kwargs)
        return searcherator.search_queryset(items, searching)

    _ninja_contribute_args.append((
        searcherator_kwargs_name,
        searcherator.Input,
        searcherator.input_source,
    ))
    view_with_searching._ninja_contribute_args = _ninja_contribute_args
    return view_with_searching

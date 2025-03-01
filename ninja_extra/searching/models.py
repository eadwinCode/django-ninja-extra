import operator
import re
import typing as t
from functools import reduce

from django.db.models import Q, QuerySet
from django.db.models.constants import LOOKUP_SEP
from ninja import Field, Schema

from ninja_extra.interfaces.searching import SearchingBase


def _istartswith(a: str, b: str) -> bool:
    return a.startswith(b)


def _isiexact(a: str, b: str) -> bool:
    return a.lower() == b.lower()


def _isiregex(a: str, b: str) -> bool:
    return bool(re.search(b, a, re.IGNORECASE))


def _isicontains(a: str, b: str) -> bool:
    return b.lower() in a.lower()


class Searching(SearchingBase):
    class Input(Schema):
        search: t.Optional[str] = Field(None)

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
        search_fields: t.Optional[t.List[str]] = None,
        pass_parameter: t.Optional[str] = None,
    ) -> None:
        super().__init__(pass_parameter=pass_parameter)
        self.search_fields = search_fields or []

    def searching_queryset(
        self, items: t.Union[QuerySet, t.List], searching_input: Input
    ) -> t.Union[QuerySet, t.List]:
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

    def get_search_terms(self, value: t.Optional[str]) -> t.List[str]:
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

    def construct_conditions_for_queryset(self, search_terms: t.List[str]) -> t.List[Q]:
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
        self, search_terms: t.List[str]
    ) -> t.Dict[str, t.List[t.Tuple[t.Callable, str]]]:
        lookups = self.construct_search_for_list()
        conditions: t.Dict[str, t.List[t.Tuple[t.Callable, str]]] = {
            field_name: [] for field_name in lookups.keys()
        }
        for search_term in search_terms:
            for field_name, lookup in lookups.items():
                conditions[field_name].append((lookup, search_term))
        return conditions

    def construct_search_for_list(self) -> t.Dict[str, t.Callable]:
        def get_lookup(prefix: str) -> t.Callable:
            return self.lookup_prefixes_list.get(prefix, _isicontains)

        return {
            field_name[1:]
            if (self.lookup_prefixes_list.get(field_name[0]))
            else field_name: get_lookup(field_name[0])
            for field_name in self.search_fields
        }

    def filter_spec(
        self, item: t.Any, conditions: t.Dict[str, t.List[t.Tuple[t.Callable, str]]]
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

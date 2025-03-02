import logging
import typing as t
from operator import attrgetter, itemgetter

from django.db.models import QuerySet
from ninja import Field, P, Query, Schema
from pydantic import BaseModel

from ninja_extra.interfaces.ordering import OrderingBase

logger = logging.getLogger()


class Ordering(OrderingBase):
    class Input(Schema):
        ordering: t.Optional[str] = Field(None)

    def __init__(
        self,
        ordering_fields: t.Optional[t.List[str]] = None,
        pass_parameter: t.Optional[str] = None,
    ) -> None:
        super().__init__(pass_parameter=pass_parameter)
        self.ordering_fields = ordering_fields or "__all__"
        self.Input = self.create_input(ordering_fields)  # type:ignore

    def create_input(self, ordering_fields: t.Optional[t.List[str]]) -> t.Type[Input]:
        if ordering_fields:

            class DynamicInput(Ordering.Input):
                ordering: Query[t.Optional[str], P(default=",".join(ordering_fields))]  # type:ignore[type-arg,valid-type]

            return DynamicInput
        return Ordering.Input

    def ordering_queryset(
        self, items: t.Union[QuerySet, t.List], ordering_input: Input
    ) -> t.Union[QuerySet, t.List]:
        ordering_ = self.get_ordering(items, ordering_input.ordering)
        if ordering_:
            if isinstance(items, QuerySet):
                return items.order_by(*ordering_)
            elif isinstance(items, list) and items:

                def multisort(xs: t.List, specs: t.List[t.Tuple[str, bool]]) -> t.List:
                    orerator = itemgetter if isinstance(xs[0], dict) else attrgetter
                    for key, reverse in reversed(specs):
                        xs.sort(key=orerator(key), reverse=reverse)
                    return xs

                return multisort(
                    items,
                    [
                        (o[int(o.startswith("-")) :], o.startswith("-"))
                        for o in ordering_
                    ],
                )
        return items

    def get_ordering(
        self, items: t.Union[QuerySet, t.List], value: t.Optional[str]
    ) -> t.List[str]:
        if value:
            fields = [param.strip() for param in value.split(",")]
            return self.remove_invalid_fields(items, fields)
        return []

    def remove_invalid_fields(
        self, items: t.Union[QuerySet, t.List], fields: t.List[str]
    ) -> t.List[str]:
        valid_fields = list(self.get_valid_fields(items))

        def term_valid(term: str) -> bool:
            if term.startswith("-"):
                term = term[1:]
            return term in valid_fields

        return [term for term in fields if term_valid(term)]

    def get_valid_fields(self, items: t.Union[QuerySet, t.List]) -> t.List[str]:
        valid_fields: t.List[str] = []
        if self.ordering_fields == "__all__":
            if isinstance(items, QuerySet):
                valid_fields = self.get_all_valid_fields_from_queryset(items)
            elif isinstance(items, list):
                valid_fields = self.get_all_valid_fields_from_list(items)
        else:
            valid_fields = list(self.ordering_fields)
        return valid_fields

    def get_all_valid_fields_from_queryset(self, items: QuerySet) -> t.List[str]:
        return [str(field.name) for field in items.model._meta.fields] + [
            str(key) for key in items.query.annotations
        ]

    def get_all_valid_fields_from_list(self, items: t.List) -> t.List[str]:
        if not items:
            return []
        item = items[0]
        if isinstance(item, BaseModel):
            return list(item.model_fields.keys())
        if isinstance(item, dict):
            return list(item.keys())
        if hasattr(item, "_meta") and hasattr(item._meta, "fields"):
            return [str(field.name) for field in item._meta.fields]
        return []

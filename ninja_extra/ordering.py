from functools import wraps
from inspect import isfunction as is_func
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from django.db.models import QuerySet
from ninja import Field, Query, Schema
from ninja.constants import NOT_SET

from ninja_extra.conf import settings

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers import ControllerBase


class Ordering:

    class Input(Schema):
        ordering: Optional[str] = Field(None)

    input_source = Query(...)

    def __init__(self, ordering_fields: Optional[Union[str, List[str]]] = None, pass_parameter: Optional[str] = None) -> None:
        self.ordering_fields = ordering_fields or '__all__'
        self.pass_parameter = pass_parameter

    def ordering_queryset(self, queryset: QuerySet, ordering: Input):
        ordering = self.get_ordering(queryset, ordering.ordering)
        if ordering:
            return queryset.order_by(*ordering)
        return queryset

    def get_ordering(self, queryset: QuerySet, value: Optional[str]) -> Optional[List[str]]:
        if value:
            fields = [param.strip() for param in value.split(',')]
            return self.remove_invalid_fields(queryset, fields)
        return []

    def remove_invalid_fields(self, queryset, fields):
        valid_fields = [item[0] for item in self.get_valid_fields(queryset)]

        def term_valid(term):
            if term.startswith("-"):
                term = term[1:]
            return term in valid_fields

        return [term for term in fields if term_valid(term)]

    def get_valid_fields(self, queryset):
        valid_fields = self.ordering_fields
        if valid_fields == '__all__':
            valid_fields = [(field.name, field.verbose_name) for field in queryset.model._meta.fields]
            valid_fields += [(key, key.title().split('__')) for key in queryset.query.annotations]
        else:
            valid_fields = [(item, item) if isinstance(item, str) else item for item in valid_fields]
        return valid_fields


def ordering(func_or_ordering_class: Type[Ordering] = NOT_SET, **ordering_params: Any) -> Callable:
    isfunction = is_func(func_or_ordering_class)
    isnotset = func_or_ordering_class == NOT_SET
    ordering_class: Type[Ordering] = settings.ORDERING_CLASS
    if isfunction:
        return _inject_orderator(func_or_ordering_class, ordering_class)
    if not isnotset:
        ordering_class = func_or_ordering_class

    def wrapper(func: Callable[..., Any]) -> Any:
        return _inject_orderator(func, ordering_class, **ordering_params)

    return wrapper


def _inject_orderator(
    func: Callable[..., Any],
    ordering_class: Type[Ordering],
    **ordering_params: Any,
) -> Callable[..., Any]:
    orderator: Ordering = ordering_class(**ordering_params)
    orderator_kwargs_name = "ordering"
    _ninja_contribute_args: List[Tuple] = getattr(func, "_ninja_contribute_args", [])

    @wraps(func)
    def view_with_ordering(controller: "ControllerBase", *args: Any, **kw: Any) -> Any:
        func_kwargs = dict(**kw)
        ordering = func_kwargs.pop(orderator_kwargs_name)
        if orderator.pass_parameter:
            func_kwargs[orderator.pass_parameter] = ordering_params
        items = func(controller, *args, **func_kwargs)
        return orderator.ordering_queryset(items, ordering)

    _ninja_contribute_args.append((
        orderator_kwargs_name,
        orderator.Input,
        orderator.input_source,
    ))
    view_with_ordering._ninja_contribute_args = _ninja_contribute_args
    return view_with_ordering

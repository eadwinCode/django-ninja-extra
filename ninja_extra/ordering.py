import inspect
import logging
from abc import ABC, abstractmethod
from functools import wraps
from operator import attrgetter, itemgetter
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
from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Field, P, Query, Schema
from ninja.constants import NOT_SET
from ninja.signature import is_async
from pydantic import BaseModel

from ninja_extra.conf import settings
from ninja_extra.shortcuts import add_ninja_contribute_args

logger = logging.getLogger()

if TYPE_CHECKING:  # pragma: no cover
    from .controllers import ControllerBase

__all__ = [
    "OrderingBase",
    "Ordering",
    "ordering",
    "OrderatorOperation",
    "AsyncOrderatorOperation",
]


class OrderingBase(ABC):
    class Input(Schema): ...

    InputSource = Query(...)

    def __init__(self, *, pass_parameter: Optional[str] = None, **kwargs: Any) -> None:
        self.pass_parameter = pass_parameter

    @abstractmethod
    def ordering_queryset(
        self, items: Union[QuerySet, List], ordering_input: Any
    ) -> Union[QuerySet, List]: ...


class Ordering(OrderingBase):
    class Input(Schema):
        ordering: Optional[str] = Field(None)

    def __init__(
        self,
        ordering_fields: Optional[List[str]] = None,
        pass_parameter: Optional[str] = None,
    ) -> None:
        super().__init__(pass_parameter=pass_parameter)
        self.ordering_fields = ordering_fields or "__all__"
        self.Input = self.create_input(ordering_fields)  # type:ignore

    def create_input(self, ordering_fields: Optional[List[str]]) -> Type[Input]:
        if ordering_fields:

            class DynamicInput(Ordering.Input):
                ordering: Query[Optional[str], P(default=",".join(ordering_fields))]  # type:ignore[type-arg,valid-type]

            return DynamicInput
        return Ordering.Input

    def ordering_queryset(
        self, items: Union[QuerySet, List], ordering_input: Input
    ) -> Union[QuerySet, List]:
        ordering_ = self.get_ordering(items, ordering_input.ordering)
        if ordering_:
            if isinstance(items, QuerySet):
                return items.order_by(*ordering_)
            elif isinstance(items, list) and items:

                def multisort(xs: List, specs: List[Tuple[str, bool]]) -> List:
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
        self, items: Union[QuerySet, List], value: Optional[str]
    ) -> List[str]:
        if value:
            fields = [param.strip() for param in value.split(",")]
            return self.remove_invalid_fields(items, fields)
        return []

    def remove_invalid_fields(
        self, items: Union[QuerySet, List], fields: List[str]
    ) -> List[str]:
        valid_fields = list(self.get_valid_fields(items))

        def term_valid(term: str) -> bool:
            if term.startswith("-"):
                term = term[1:]
            return term in valid_fields

        return [term for term in fields if term_valid(term)]

    def get_valid_fields(self, items: Union[QuerySet, List]) -> List[str]:
        valid_fields: List[str] = []
        if self.ordering_fields == "__all__":
            if isinstance(items, QuerySet):
                valid_fields = self.get_all_valid_fields_from_queryset(items)
            elif isinstance(items, list):
                valid_fields = self.get_all_valid_fields_from_list(items)
        else:
            valid_fields = list(self.ordering_fields)
        return valid_fields

    def get_all_valid_fields_from_queryset(self, items: QuerySet) -> List[str]:
        return [str(field.name) for field in items.model._meta.fields] + [
            str(key) for key in items.query.annotations
        ]

    def get_all_valid_fields_from_list(self, items: List) -> List[str]:
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


@overload
def ordering() -> Callable[..., Any]:  # pragma: no cover
    ...


@overload
def ordering(
    func_or_ordering_class: Any = NOT_SET, **paginator_params: Any
) -> Callable[..., Any]:  # pragma: no cover
    ...


def ordering(
    func_or_ordering_class: Any = NOT_SET, **ordering_params: Any
) -> Callable[..., Any]:
    isfunction = inspect.isfunction(func_or_ordering_class)
    isnotset = func_or_ordering_class == NOT_SET

    ordering_class: Type[OrderingBase] = settings.ORDERING_CLASS

    if isfunction:
        return _inject_orderator(func_or_ordering_class, ordering_class)

    if not isnotset:
        ordering_class = func_or_ordering_class

    def wrapper(func: Callable[..., Any]) -> Any:
        return _inject_orderator(func, ordering_class, **ordering_params)

    return wrapper


def _inject_orderator(
    func: Callable[..., Any],
    ordering_class: Type[OrderingBase],
    **ordering_params: Any,
) -> Callable[..., Any]:
    orderator: OrderingBase = ordering_class(**ordering_params)
    orderator_kwargs_name = "ordering"
    orderator_operation_class = OrderatorOperation
    if is_async(func):
        orderator_operation_class = AsyncOrderatorOperation
    orderator_operation = orderator_operation_class(
        orderator=orderator, view_func=func, orderator_kwargs_name=orderator_kwargs_name
    )

    return orderator_operation.as_view


class OrderatorOperation:
    def __init__(
        self,
        *,
        orderator: OrderingBase,
        view_func: Callable,
        orderator_kwargs_name: str = "ordering",
    ) -> None:
        self.orderator = orderator
        self.orderator_kwargs_name = orderator_kwargs_name
        self.view_func = view_func

        orderator_view = self.get_view_function()
        self.as_view = wraps(view_func)(orderator_view)
        add_ninja_contribute_args(
            self.as_view,
            (
                self.orderator_kwargs_name,
                self.orderator.Input,
                self.orderator.InputSource,
            ),
        )
        orderator_view.orderator_operation = self  # type:ignore[attr-defined]

    @property
    def view_func_has_kwargs(self) -> bool:  # pragma: no cover
        return self.orderator.pass_parameter is not None

    def get_view_function(self) -> Callable:
        def as_view(
            request_or_controller: Union["ControllerBase", HttpRequest],
            *args: Any,
            **kw: Any,
        ) -> Any:
            func_kwargs = dict(**kw)
            ordering_params = func_kwargs.pop(self.orderator_kwargs_name)
            if self.orderator.pass_parameter:
                func_kwargs[self.orderator.pass_parameter] = ordering_params

            items = self.view_func(request_or_controller, *args, **func_kwargs)
            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items
            return self.orderator.ordering_queryset(items, ordering_params)

        return as_view


class AsyncOrderatorOperation(OrderatorOperation):
    def get_view_function(self) -> Callable:
        async def as_view(
            request_or_controller: Union["ControllerBase", HttpRequest],
            *args: Any,
            **kw: Any,
        ) -> Any:
            func_kwargs = dict(**kw)
            ordering_params = func_kwargs.pop(self.orderator_kwargs_name)
            if self.orderator.pass_parameter:
                func_kwargs[self.orderator.pass_parameter] = ordering_params

            items = await self.view_func(request_or_controller, *args, **func_kwargs)

            if (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[0], int)
            ):
                return items

            ordering_queryset = cast(
                Callable, sync_to_async(self.orderator.ordering_queryset)
            )
            return await ordering_queryset(items, ordering_params)

        return as_view

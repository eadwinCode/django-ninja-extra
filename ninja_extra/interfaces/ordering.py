import typing as t
from abc import ABC, abstractmethod

from django.db.models import QuerySet
from ninja import Query, Schema


class OrderingBase(ABC):
    class Input(Schema): ...

    InputSource = Query(...)

    def __init__(
        self, *, pass_parameter: t.Optional[str] = None, **kwargs: t.Any
    ) -> None:
        self.pass_parameter = pass_parameter

    @abstractmethod
    def ordering_queryset(
        self, items: t.Union[QuerySet, t.List], ordering_input: t.Any
    ) -> t.Union[QuerySet, t.List]: ...

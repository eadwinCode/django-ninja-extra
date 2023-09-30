import typing as t
from abc import ABC, abstractmethod

from django.db.models import Model as DjangoModel
from django.db.models import QuerySet
from pydantic import BaseModel as PydanticModel


class ModelServiceBase(ABC):
    """
    Abstract service that handles Model Controller model CRUD operations
    """

    @abstractmethod
    def get_one(self, pk: t.Any, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    def get_all(self, **kwargs: t.Any) -> t.Union[QuerySet, t.List[t.Any]]:
        pass

    @abstractmethod
    def create(self, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    def update(
        self, instance: DjangoModel, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    def patch(
        self, instance: DjangoModel, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    def delete(self, instance: DjangoModel, **kwargs: t.Any) -> t.Any:
        pass

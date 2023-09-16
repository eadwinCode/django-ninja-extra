import typing as t
from abc import ABC, abstractmethod

from django.db.models import Model, QuerySet
from pydantic import BaseModel as PydanticModel


class ModelServiceBase(ABC):
    @abstractmethod
    def get_one(self, pk: t.Any) -> t.Any:
        pass

    @abstractmethod
    def get_all(self) -> t.Union[QuerySet, t.List[t.Any]]:
        pass

    @abstractmethod
    def create(self, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    def update(self, instance: Model, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    def patch(self, instance: Model, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    def delete(self, instance: Model) -> t.Any:
        pass

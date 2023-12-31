import typing as t
from abc import ABC, abstractmethod

from django.db.models import Model as DjangoModel
from django.db.models import QuerySet
from pydantic import BaseModel as PydanticModel


class AsyncModelServiceBase(ABC):
    @abstractmethod
    async def get_one_async(self, pk: t.Any, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    async def get_all_async(self, **kwargs: t.Any) -> t.Union[QuerySet, t.List[t.Any]]:
        pass

    @abstractmethod
    async def create_async(self, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    async def update_async(
        self, instance: DjangoModel, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    async def patch_async(
        self, instance: DjangoModel, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    async def delete_async(self, instance: DjangoModel, **kwargs: t.Any) -> t.Any:
        pass


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

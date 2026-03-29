import typing as t
from abc import ABC, abstractmethod

from django.db.models import Model as DjangoModel
from django.db.models import QuerySet
from pydantic import BaseModel as PydanticModel

from ninja_extra.exceptions import APIException, NotFound

ModelType = t.TypeVar("ModelType", bound=DjangoModel)


class AsyncModelServiceBase(ABC, t.Generic[ModelType]):
    @abstractmethod
    async def get_one_async(
        self,
        pk: t.Any,
        queryset: t.Optional[QuerySet] = None,
        error_message: t.Optional[str] = None,
        exception: t.Type[APIException] = NotFound,
        **kwargs: t.Any,
    ) -> t.Any:
        pass

    @abstractmethod
    async def get_all_async(self, **kwargs: t.Any) -> t.Union[QuerySet, t.List[t.Any]]:
        pass

    @abstractmethod
    async def create_async(self, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    async def update_async(
        self, instance: ModelType, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    async def patch_async(
        self, instance: ModelType, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    async def delete_async(self, instance: ModelType, **kwargs: t.Any) -> t.Any:
        pass


class ModelServiceBase(ABC, t.Generic[ModelType]):
    """
    Abstract service that handles Model Controller model CRUD operations
    """

    @abstractmethod
    def get_one(
        self,
        pk: t.Any,
        queryset: t.Optional[QuerySet] = None,
        error_message: t.Optional[str] = None,
        exception: t.Type[APIException] = NotFound,
        **kwargs: t.Any,
    ) -> t.Any:
        pass

    @abstractmethod
    def get_all(self, **kwargs: t.Any) -> t.Union[QuerySet, t.List[t.Any]]:
        pass

    @abstractmethod
    def create(self, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    def update(
        self, instance: ModelType, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    def patch(
        self, instance: ModelType, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        pass

    @abstractmethod
    def delete(self, instance: ModelType, **kwargs: t.Any) -> t.Any:
        pass

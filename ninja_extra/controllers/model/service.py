import traceback
import typing as t
from functools import wraps

import django
from asgiref.sync import sync_to_async
from django.db.models import Model, QuerySet
from pydantic import BaseModel as PydanticModel

from ninja_extra.exceptions import NotFound
from ninja_extra.shortcuts import aget_object_or_exception, get_object_or_exception

from .interfaces import AsyncModelServiceBase, ModelServiceBase

django_version_greater_than_4_2 = django.VERSION > (4, 2)


def _async_django_support(sync_method_name: str) -> t.Callable[..., t.Any]:
    """
    Ensures that django version supports async orm methods.
    If not, it will use sync_to_async to call the sync method with thread_sensitive=True.
    """

    def decorator(func: t.Callable[..., t.Coroutine]) -> t.Callable[..., t.Coroutine]:
        @wraps(func)
        async def wrapper(self: "ModelService", *args: t.Any, **kwargs: t.Any) -> t.Any:
            if not django_version_greater_than_4_2:
                alternate_method = getattr(self, sync_method_name)
                return await sync_to_async(alternate_method, thread_sensitive=True)(
                    *args, **kwargs
                )

            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


class ModelService(ModelServiceBase, AsyncModelServiceBase):
    """
    Model Service for Model Controller model CRUD operations with a simple logic for simple models.

    Its advised you override this class if you have a complex model.
    """

    def __init__(self, model: t.Type[Model]) -> None:
        self.model = model

    # --- Synchronous Methods ---

    def get_one(self, pk: t.Any, **kwargs: t.Any) -> t.Any:
        obj = get_object_or_exception(
            klass=self.model, error_message=None, exception=NotFound, pk=pk
        )
        return obj

    def get_all(self, **kwargs: t.Any) -> t.Union[QuerySet, t.List[t.Any]]:
        return self.model.objects.all()

    def create(self, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        data = schema.model_dump(by_alias=True)
        data.update(kwargs)

        try:
            instance = self.model._default_manager.create(**data)
            return instance
        except TypeError as tex:  # pragma: no cover
            tb = traceback.format_exc()
            msg = (
                "Got a `TypeError` when calling `%s.%s.create()`. "
                "This may be because you have a writable field on the "
                "serializer class that is not a valid argument to "
                "`%s.%s.create()`. You may need to make the field "
                "read-only, or override the %s.create() method to handle "
                "this correctly.\nOriginal exception was:\n %s"
                % (
                    self.model.__name__,
                    self.model._default_manager.name,
                    self.model.__name__,
                    self.model._default_manager.name,
                    self.__class__.__name__,
                    tb,
                )
            )
            raise TypeError(msg) from tex

    def update(self, instance: Model, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        data = schema.model_dump(exclude_unset=True)
        data.update(kwargs)
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def patch(self, instance: Model, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        return self.update(instance=instance, schema=schema, **kwargs)

    def delete(self, instance: Model, **kwargs: t.Any) -> t.Any:
        instance.delete()

    # --- Asynchronous Methods (using native async ORM where possible) ---

    @_async_django_support("get_one")
    async def get_one_async(self, pk: t.Any, **kwargs: t.Any) -> t.Any:
        obj = await aget_object_or_exception(
            klass=self.model, error_message=None, exception=NotFound, pk=pk
        )
        return obj

    async def get_all_async(self, **kwargs: t.Any) -> t.Union[QuerySet, t.List[t.Any]]:
        return await sync_to_async(self.get_all, thread_sensitive=True)(**kwargs)

    @_async_django_support("create")
    async def create_async(self, schema: PydanticModel, **kwargs: t.Any) -> t.Any:
        data = schema.model_dump(by_alias=True)
        data.update(kwargs)

        try:
            instance = await self.model._default_manager.acreate(**data)
            return instance
        except TypeError as tex:  # pragma: no cover
            tb = traceback.format_exc()
            msg = (
                "Got a `TypeError` when calling `%s.%s.create()`. "
                "This may be because you have a writable field on the "
                "serializer class that is not a valid argument to "
                "`%s.%s.create()`. You may need to make the field "
                "read-only, or override the %s.create() method to handle "
                "this correctly.\nOriginal exception was:\n %s"
                % (
                    self.model.__name__,
                    self.model._default_manager.name,
                    self.model.__name__,
                    self.model._default_manager.name,
                    self.__class__.__name__,
                    tb,
                )
            )
            raise TypeError(msg) from tex

    @_async_django_support("update")
    async def update_async(
        self, instance: Model, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        data = schema.model_dump(exclude_none=True)
        data.update(kwargs)
        for attr, value in data.items():
            setattr(instance, attr, value)
        await instance.asave()
        return instance

    @_async_django_support("patch")
    async def patch_async(
        self, instance: Model, schema: PydanticModel, **kwargs: t.Any
    ) -> t.Any:
        return await self.update_async(instance=instance, schema=schema, **kwargs)

    @_async_django_support("delete")
    async def delete_async(self, instance: Model, **kwargs: t.Any) -> t.Any:
        await instance.adelete()

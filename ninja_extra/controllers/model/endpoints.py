import typing as t
import uuid

from django.db.models import Model as DjangoModel
from django.db.models import QuerySet
from ninja.pagination import PaginationBase
from ninja.params import Body
from ninja.signature import is_async
from pydantic import BaseModel as PydanticModel

from ninja_extra import status
from ninja_extra.controllers.model.path_resolver import (
    AsyncPathResolverOperation,
    PathResolverOperation,
)
from ninja_extra.controllers.route import route
from ninja_extra.exceptions import NotFound
from ninja_extra.pagination import (
    PageNumberPaginationExtra,
    PaginatedResponseSchema,
    paginate,
)
from ninja_extra.permissions import BasePermission

if t.TYPE_CHECKING:
    from ninja_extra.controllers.base import ModelControllerBase


async def _check_if_coroutine(func_result: t.Union[t.Any, t.Coroutine]) -> t.Any:
    if isinstance(func_result, t.Coroutine):
        return await func_result
    return func_result


def _path_resolver(path: str, func: t.Callable) -> t.Callable:
    resolver_class = PathResolverOperation
    if is_async(func):
        resolver_class = AsyncPathResolverOperation

    instance = resolver_class(path, func)
    return instance.as_view


class ModelEndpointFactory:
    """
    Factory for creating CRUD operations of a model controller and for adding custom route functions to controllers.

    example:
    ```python

    api_controller
    class SampleModelController(ModelControllerBase):

        create_sample = ModelEndpointFactory.create()
        update_sample = ModelEndpointFactory.update()

        delete_sample = ModelEndpointFactory.delete()
        patch_sample = ModelEndpointFactory.patch()

        get_sample = ModelEndpointFactory.get()
        list_samples = ModelEndpointFactory.list()
    ```
    """

    @classmethod
    def _clean_path(cls, path: str) -> str:
        working_path = path.split("?")
        return working_path[0]

    @classmethod
    def _change_name(cls, name_prefix: str) -> str:
        unique = str(uuid.uuid4())[:6]
        return f"{name_prefix}_{unique}"

    @classmethod
    def create(
        cls,
        schema_in: t.Type[PydanticModel],
        schema_out: t.Type[PydanticModel],
        path: str = "/",
        status_code: int = status.HTTP_201_CREATED,
        url_name: t.Optional[str] = None,
        custom_handler: t.Optional[t.Callable[..., t.Any]] = None,
        description: t.Optional[str] = None,
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = "Create new item",
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        include_in_schema: bool = True,
        permissions: t.Optional[
            t.List[t.Union[t.Type[BasePermission], BasePermission, t.Any]]
        ] = None,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Callable:
        """
        Creates a POST Action
        """
        working_path = cls._clean_path(path)

        create_item = _path_resolver(
            path,
            cls._create_handler(schema_in=schema_in, custom_handler=custom_handler),
        )
        return route.post(
            working_path,
            response={status_code: schema_out},
            url_name=url_name,
            description=description,
            operation_id=operation_id,
            summary=summary,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            include_in_schema=include_in_schema,
            permissions=permissions,
            openapi_extra=openapi_extra,
        )(create_item)

    @classmethod
    def update(
        cls,
        path: str,
        lookup_param: str,
        schema_in: t.Type[PydanticModel],
        schema_out: t.Type[PydanticModel],
        status_code: int = status.HTTP_200_OK,
        url_name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        object_getter: t.Optional[t.Callable[..., DjangoModel]] = None,
        custom_handler: t.Optional[t.Callable[..., t.Any]] = None,
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = "Update an item",
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        include_in_schema: bool = True,
        permissions: t.Optional[
            t.List[t.Union[t.Type[BasePermission], BasePermission, t.Any]]
        ] = None,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Callable:
        """
        Creates a PUT Action
        """
        working_path = cls._clean_path(path)
        update_item = _path_resolver(
            path,
            cls._update_handler(
                schema_in=schema_in,
                object_getter=object_getter,
                lookup_param=lookup_param,
                custom_handler=custom_handler,
            ),
        )
        return route.put(
            working_path,
            response={status_code: schema_out},
            url_name=url_name,
            description=description,
            operation_id=operation_id,
            summary=summary,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            include_in_schema=include_in_schema,
            permissions=permissions,
            openapi_extra=openapi_extra,
        )(update_item)

    @classmethod
    def patch(
        cls,
        path: str,
        lookup_param: str,
        schema_in: t.Type[PydanticModel],
        schema_out: t.Type[PydanticModel],
        status_code: int = status.HTTP_200_OK,
        url_name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        object_getter: t.Optional[t.Callable[..., DjangoModel]] = None,
        custom_handler: t.Optional[t.Callable[..., t.Any]] = None,
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = "Patch Item Update",
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        include_in_schema: bool = True,
        permissions: t.Optional[
            t.List[t.Union[t.Type[BasePermission], BasePermission, t.Any]]
        ] = None,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Callable:
        """
        Creates a PATCH Action
        """
        working_path = cls._clean_path(path)
        patch_item = _path_resolver(
            path,
            cls._patch_handler(
                object_getter=object_getter,
                custom_handler=custom_handler,
                lookup_param=lookup_param,
                schema_in=schema_in,
            ),
        )
        return route.patch(
            working_path,
            response={status_code: schema_out},
            url_name=url_name,
            description=description,
            operation_id=operation_id,
            summary=summary,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            include_in_schema=include_in_schema,
            permissions=permissions,
            openapi_extra=openapi_extra,
        )(patch_item)

    @classmethod
    def find_one(
        cls,
        path: str,
        lookup_param: str,
        schema_out: t.Type[PydanticModel],
        status_code: int = status.HTTP_200_OK,
        url_name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        object_getter: t.Optional[t.Callable[..., DjangoModel]] = None,
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = "Find a specific item",
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        include_in_schema: bool = True,
        permissions: t.Optional[
            t.List[t.Union[t.Type[BasePermission], BasePermission, t.Any]]
        ] = None,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Callable:
        """
        Creates a GET Action
        """
        working_path = cls._clean_path(path)
        get_item = _path_resolver(
            path,
            cls._find_one_handler(
                object_getter=object_getter, lookup_param=lookup_param
            ),
        )
        return route.get(
            working_path,
            response={status_code: schema_out},
            url_name=url_name,
            description=description,
            operation_id=operation_id,
            summary=summary,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            include_in_schema=include_in_schema,
            permissions=permissions,
            openapi_extra=openapi_extra,
        )(get_item)

    @classmethod
    def list(
        cls,
        schema_out: t.Type[PydanticModel],
        path: str = "/",
        status_code: int = status.HTTP_200_OK,
        url_name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = "List of Items",
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        include_in_schema: bool = True,
        permissions: t.Optional[
            t.List[t.Union[t.Type[BasePermission], BasePermission, t.Any]]
        ] = None,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
        queryset_getter: t.Optional[t.Callable[..., QuerySet]] = None,
        pagination_response_schema: t.Optional[
            t.Type[PydanticModel]
        ] = PaginatedResponseSchema,
        pagination_class: t.Optional[
            t.Type[PaginationBase]
        ] = PageNumberPaginationExtra,
        **paginate_kwargs: t.Any,
    ) -> t.Callable:
        """
        Creates a GET Action to list Items
        """
        working_path = cls._clean_path(path)
        list_items = _path_resolver(
            path, cls._list_handler(queryset_getter=queryset_getter)
        )

        if pagination_response_schema and pagination_class:
            list_items = paginate(pagination_class, **paginate_kwargs)(list_items)
            return route.get(
                working_path,
                response={
                    status_code: pagination_response_schema[schema_out]  # type:ignore[index]
                },
                url_name=url_name,
                description=description,
                operation_id=operation_id,
                summary=summary,
                tags=tags,
                deprecated=deprecated,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                include_in_schema=include_in_schema,
                permissions=permissions,
                openapi_extra=openapi_extra,
            )(list_items)

        return route.get(
            working_path,
            response={status_code: t.List[schema_out]},  # type:ignore[valid-type]
            url_name=url_name,
            description=description,
            operation_id=operation_id,
            summary=summary,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            include_in_schema=include_in_schema,
            permissions=permissions,
            openapi_extra=openapi_extra,
        )(list_items)

    @classmethod
    def delete(
        cls,
        path: str,
        lookup_param: str,
        status_code: int = status.HTTP_204_NO_CONTENT,
        url_name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        object_getter: t.Optional[t.Callable[..., DjangoModel]] = None,
        custom_handler: t.Optional[t.Callable[..., t.Any]] = None,
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = "Delete An Item",
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        include_in_schema: bool = True,
        permissions: t.Optional[
            t.List[t.Union[t.Type[BasePermission], BasePermission, t.Any]]
        ] = None,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Callable:
        """
        Creates a DELETE Action to list Items
        """
        working_path = cls._clean_path(path)
        delete_item = _path_resolver(
            path,
            cls._delete_handler(
                object_getter=object_getter,
                lookup_param=lookup_param,
                custom_handler=custom_handler,
                status_code=status_code,
            ),
        )
        return route.delete(
            working_path,
            url_name=url_name,
            response={status_code: str},
            description=description,
            operation_id=operation_id,
            summary=summary,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            include_in_schema=include_in_schema,
            permissions=permissions,
            openapi_extra=openapi_extra,
        )(delete_item)

    @classmethod
    def _list_handler(
        cls, *, queryset_getter: t.Optional[t.Callable[..., QuerySet]]
    ) -> t.Callable:
        def list_items(self: "ModelControllerBase", **kwargs: t.Any) -> t.Any:
            """List Items of testing"""
            if queryset_getter:
                return queryset_getter(self, **kwargs)
            return self.service.get_all(**kwargs)

        list_items.__name__ = cls._change_name("list_items")
        return list_items

    @classmethod
    def _delete_handler(
        cls,
        *,
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
        custom_handler: t.Optional[t.Callable[..., t.Any]],
        status_code: int,
    ) -> t.Callable:
        def delete_item(self: "ModelControllerBase", **kwargs: t.Any) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one(pk=pk, **kwargs)
            )
            if not obj:  # pragma: no cover
                raise NotFound()
            self.check_object_permissions(obj)
            custom_handler(
                self, instance=obj, **kwargs
            ) if custom_handler else self.service.delete(instance=obj, **kwargs)
            return self.create_response(message="", status_code=status_code)

        delete_item.__name__ = cls._change_name("delete_item")
        return delete_item

    @classmethod
    def _find_one_handler(
        cls,
        *,
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
    ) -> t.Callable:
        def get_item(self: "ModelControllerBase", **kwargs: t.Any) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one(pk=pk, **kwargs)
            )
            if not obj:  # pragma: no cover
                raise NotFound()
            self.check_object_permissions(obj)
            return obj

        get_item.__name__ = cls._change_name("get_item")
        return get_item

    @classmethod
    def _patch_handler(
        cls,
        *,
        schema_in: t.Type[PydanticModel],
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
        custom_handler: t.Optional[t.Callable[..., t.Any]],
    ) -> t.Callable:
        def patch_item(
            self: "ModelControllerBase",
            data: schema_in = Body(default=...),  # type:ignore[valid-type]
            **kwargs: t.Any,
        ) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one(pk=pk, **kwargs)
            )
            if not obj:  # pragma: no cover
                raise NotFound()
            self.check_object_permissions(obj)
            instance = (
                custom_handler(self, instance=obj, schema=data, **kwargs)
                if custom_handler
                else self.service.patch(instance=obj, schema=data, **kwargs)
            )
            assert instance, "`service.patch()` or `custom_handler` must return a value"
            return instance

        patch_item.__name__ = cls._change_name("patch_item")
        return patch_item

    @classmethod
    def _update_handler(
        cls,
        *,
        schema_in: t.Type[PydanticModel],
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
        custom_handler: t.Optional[t.Callable[..., t.Any]],
    ) -> t.Callable:
        def update_item(
            self: "ModelControllerBase",
            data: schema_in = Body(default=...),  # type:ignore[valid-type]
            **kwargs: t.Any,
        ) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one(pk=pk, **kwargs)
            )

            if not obj:  # pragma: no cover
                raise NotFound()

            self.check_object_permissions(obj)
            instance = (
                custom_handler(self, instance=obj, schema=data, **kwargs)
                if custom_handler
                else self.service.update(instance=obj, schema=data, **kwargs)
            )
            assert instance, "`service.update` or `custom_handler` must return a value"
            return instance

        update_item.__name__ = cls._change_name("update_item")
        return update_item

    @classmethod
    def _create_handler(
        cls,
        *,
        schema_in: t.Type[PydanticModel],
        custom_handler: t.Optional[t.Callable[..., t.Any]],
    ) -> t.Callable:
        def create_item(
            self: "ModelControllerBase",
            data: schema_in = Body(default=...),  # type:ignore[valid-type]
            **kwargs: t.Any,
        ) -> t.Any:
            instance = (
                custom_handler(self, data, **kwargs)
                if custom_handler
                else self.service.create(data, **kwargs)
            )
            assert instance, "`service.create` or  `custom_handler` must return a value"
            return instance

        create_item.__name__ = cls._change_name("create_item")
        return create_item


class ModelAsyncEndpointFactory(ModelEndpointFactory):
    """
    Factory for creating asynchronous CRUD operations of a model controller
    and for adding custom asynchronous route functions to controllers

    example:
    ```python

    api_controller
    class SampleModelController(ModelControllerBase):

        create_sample = ModelAsyncEndpointFactory.create()
        update_sample = ModelAsyncEndpointFactory.update()

        delete_sample = ModelAsyncEndpointFactory.delete()
        patch_sample = ModelAsyncEndpointFactory.patch()

        get_sample = ModelAsyncEndpointFactory.get()
        list_samples = ModelAsyncEndpointFactory.list()
    ```
    """

    @classmethod
    def _list_handler(
        cls, *, queryset_getter: t.Optional[t.Callable[..., QuerySet]]
    ) -> t.Callable:
        async def list_items(self: "ModelControllerBase", **kwargs: t.Any) -> t.Any:
            """List Items of testing"""
            if queryset_getter:
                res = queryset_getter(self, **kwargs)
            else:
                res = self.service.get_all_async(**kwargs)  # type:ignore[assignment]

            return await _check_if_coroutine(res)

        list_items.__name__ = cls._change_name("list_items")
        return list_items

    @classmethod
    def _delete_handler(
        cls,
        *,
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
        custom_handler: t.Optional[t.Callable[..., t.Any]],
        status_code: int,
    ) -> t.Callable:
        async def delete_item(self: "ModelControllerBase", **kwargs: t.Any) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one_async(pk=pk, **kwargs)
            )
            obj = await _check_if_coroutine(obj)
            if not obj:  # pragma: no cover
                raise NotFound()
            self.check_object_permissions(obj)

            res = (
                custom_handler(self, instance=obj, **kwargs)
                if custom_handler
                else self.service.delete_async(instance=obj, **kwargs)  # type:ignore[arg-type]
            )

            await _check_if_coroutine(res)
            return self.create_response(message="", status_code=status_code)

        delete_item.__name__ = cls._change_name("delete_item")
        return delete_item

    @classmethod
    def _find_one_handler(
        cls,
        *,
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
    ) -> t.Callable:
        async def get_item(self: "ModelControllerBase", **kwargs: t.Any) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one_async(pk=pk, **kwargs)
            )
            obj = await _check_if_coroutine(obj)

            if not obj:  # pragma: no cover
                raise NotFound()

            self.check_object_permissions(obj)
            return obj

        get_item.__name__ = cls._change_name("get_item")
        return get_item

    @classmethod
    def _patch_handler(
        cls,
        *,
        schema_in: t.Type[PydanticModel],
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
        custom_handler: t.Optional[t.Callable[..., t.Any]],
    ) -> t.Callable:
        async def patch_item(
            self: "ModelControllerBase",
            data: schema_in = Body(default=...),  # type:ignore[valid-type]
            **kwargs: t.Any,
        ) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one_async(pk=pk, **kwargs)
            )
            obj = await _check_if_coroutine(obj)

            if not obj:  # pragma: no cover
                raise NotFound()
            self.check_object_permissions(obj)

            instance = (
                custom_handler(self, instance=obj, schema=data, **kwargs)
                if custom_handler
                else self.service.patch_async(instance=obj, schema=data, **kwargs)  # type:ignore[arg-type]
            )
            instance = await _check_if_coroutine(instance)

            assert instance, (
                "`service.patch_async()` or `custom_handler` must return a value"
            )
            return instance

        patch_item.__name__ = cls._change_name("patch_item")
        return patch_item

    @classmethod
    def _update_handler(
        cls,
        *,
        schema_in: t.Type[PydanticModel],
        object_getter: t.Optional[t.Callable[..., DjangoModel]],
        lookup_param: str,
        custom_handler: t.Optional[t.Callable[..., t.Any]],
    ) -> t.Callable:
        async def update_item(
            self: "ModelControllerBase",
            data: schema_in = Body(default=...),  # type:ignore[valid-type]
            **kwargs: t.Any,
        ) -> t.Any:
            pk = kwargs.pop(lookup_param)
            obj = (
                object_getter(self, pk=pk, **kwargs)
                if object_getter
                else self.service.get_one_async(pk=pk, **kwargs)
            )
            obj = await _check_if_coroutine(obj)

            if not obj:  # pragma: no cover
                raise NotFound()

            self.check_object_permissions(obj)
            instance = (
                custom_handler(self, instance=obj, schema=data, **kwargs)
                if custom_handler
                else self.service.update_async(instance=obj, schema=data, **kwargs)  # type:ignore[arg-type]
            )
            instance = await _check_if_coroutine(instance)

            assert instance, (
                "`service.update_async` or `custom_handler` must return a value"
            )
            return instance

        update_item.__name__ = cls._change_name("update_item")
        return update_item

    @classmethod
    def _create_handler(
        cls,
        *,
        schema_in: t.Type[PydanticModel],
        custom_handler: t.Optional[t.Callable[..., t.Any]],
    ) -> t.Callable:
        async def create_item(
            self: "ModelControllerBase",
            data: schema_in = Body(default=...),  # type:ignore[valid-type]
            **kwargs: t.Any,
        ) -> t.Any:
            instance = (
                custom_handler(self, data, **kwargs)
                if custom_handler
                else self.service.create_async(data, **kwargs)
            )
            instance = await _check_if_coroutine(instance)

            assert instance, (
                "`service.create_async` or  `custom_handler` must return a value"
            )
            return instance

        create_item.__name__ = cls._change_name("create_item")
        return create_item

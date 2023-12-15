import datetime
import functools
import re
import typing as t
import uuid
from urllib.parse import parse_qs, urlparse

from django.db.models import Model as DjangoModel
from django.db.models import QuerySet
from ninja import Query, Schema
from ninja.pagination import PaginationBase
from ninja.params import Body, Path
from pydantic import UUID4, create_model
from pydantic import BaseModel as PydanticModel

from ninja_extra.permissions import BasePermission
from ninja_extra.shortcuts import add_ninja_contribute_args

from ... import status
from ...exceptions import NotFound
from ...pagination import PageNumberPaginationExtra, PaginatedResponseSchema, paginate
from ..route import route

if t.TYPE_CHECKING:
    from ..base import ModelControllerBase


# Match parameters in URL paths, eg. '{param}', and '{int:param}'
PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*:)?([a-zA-Z_][a-zA-Z0-9_]*)}")


class PathCompiledResult(t.NamedTuple):
    param_convertors: t.Dict[str, t.Any]
    query_parameters: t.Dict[str, t.Any]

    def has_any_parameter(self) -> bool:
        return len(self.param_convertors) > 0 or len(self.query_parameters) > 0


STRING_TYPES: t.Dict[str, t.Type] = {
    "int": int,
    "path": str,
    "slug": str,
    "str": str,
    "uuid": UUID4,
    "datetime": datetime.datetime,
    "date": datetime.date,
}


def compile_path(path: str) -> PathCompiledResult:
    """
    Given a path string, like: "/{str:username}"

    regex:      "/(?P<username>[^/]+)"
    format:     "/{username}"
    convertors: {str:"username"}
    """
    duplicated_params = set()
    param_convertors = {}

    parsed_url = urlparse(path)
    query_parameters = parse_qs(parsed_url.query)

    for match in PARAM_REGEX.finditer(path):
        convertor_type, param_name = match.groups("str")
        convertor = convertor_type.rstrip(":")

        if param_name in param_convertors:
            duplicated_params.add(param_name)

        param_convertors[param_name] = STRING_TYPES[convertor]

    if duplicated_params:
        names = ", ".join(sorted(duplicated_params))
        ending = "s" if len(duplicated_params) > 1 else ""
        raise ValueError(f"Duplicated param name{ending} {names} at path {path}")

    return PathCompiledResult(param_convertors, query_parameters)


class ModelEndpointFactory:
    @classmethod
    def _clean_path(cls, path: str) -> str:
        working_path = path.split("?")
        return working_path[0]

    @classmethod
    def _change_name(cls, name_prefix: str) -> str:
        unique = str(uuid.uuid4())[:6]
        return f"{name_prefix}_{unique}"

    @classmethod
    def _path_resolver(cls, path: str) -> t.Callable:
        """
        Create a decorator to parse `path` parameters and resolve them during endpoint.
        For example:
        path=/{int:id}/tags/{post_id}?query=int&query1=int
        this will create two path parameters `id` and `post_id` and two query parameters `query` and `query1`
        for the decorated endpoint
        """
        compiled_path = compile_path(path)

        def get_path_fields() -> t.Generator:
            for path_name, path_type in compiled_path.param_convertors.items():
                yield path_name, (path_type, ...)

        def get_query_fields() -> t.Generator:
            for path_name, path_type in compiled_path.query_parameters.items():
                path_type.append("str")
                yield path_name, (STRING_TYPES[path_type[0]], ...)

        def decorator(func: t.Callable) -> t.Callable:
            if not compiled_path.has_any_parameter():
                return func

            _ninja_contribute_args: t.List[t.Tuple] = getattr(
                func, "_ninja_contribute_args", []
            )

            unique_key = str(uuid.uuid4().hex)[:5]

            path_construct_name = f"PathModel{unique_key}"
            query_construct_name = f"QueryModel{unique_key}"

            path_fields = dict(get_path_fields())
            query_fields = dict(get_query_fields())

            if path_fields:
                dynamic_path_model = create_model(
                    path_construct_name, __base__=Schema, **path_fields
                )
                add_ninja_contribute_args(
                    func,
                    (path_construct_name, dynamic_path_model, Path(...)),
                )

            if query_fields:
                dynamic_query_model = create_model(
                    query_construct_name, __base__=Schema, **query_fields
                )

                add_ninja_contribute_args(
                    func,
                    (query_construct_name, dynamic_query_model, Query(...)),
                )

            @functools.wraps(func)
            def path_parameter_resolver(*args: t.Any, **kwargs: t.Any) -> t.Any:
                func_kwargs = dict(kwargs)

                if path_construct_name in func_kwargs:
                    dynamic_model_path_instance = func_kwargs.pop(path_construct_name)
                    func_kwargs.update(dynamic_model_path_instance.dict())

                if query_construct_name in func_kwargs:
                    dynamic_model_query_instance = func_kwargs.pop(query_construct_name)
                    func_kwargs.update(dynamic_model_query_instance.dict())

                return func(*args, **func_kwargs)

            return path_parameter_resolver

        return decorator

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

        @route.post(
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
        )
        @cls._path_resolver(path)
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
        return create_item  # type:ignore[no-any-return]

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

        @route.put(
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
        )
        @cls._path_resolver(path)
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
        return update_item  # type:ignore[no-any-return]

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

        @route.patch(
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
        )
        @cls._path_resolver(path)
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
        return patch_item  # type:ignore[no-any-return]

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

        @route.get(
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
        )
        @cls._path_resolver(path)
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
        return get_item  # type:ignore[no-any-return]

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

        @cls._path_resolver(path)
        def list_items(self: "ModelControllerBase", **kwargs: t.Any) -> t.Any:
            """List Items of testing"""
            if queryset_getter:
                return queryset_getter(self, **kwargs)
            return self.service.get_all(**kwargs)

        if pagination_response_schema and pagination_class:
            list_items = paginate(pagination_class, **paginate_kwargs)(list_items)
            list_items = route.get(
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
        else:
            list_items = route.get(
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

        list_items.__name__ = cls._change_name("list_items")
        return list_items  # type:ignore[no-any-return]

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
        summary: t.Optional[str] = None,
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

        @route.delete(
            working_path,
            url_name=url_name,
            response={status_code: str},
            description=description,
            operation_id=operation_id,
            summary="Delete An Item",
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            include_in_schema=include_in_schema,
            permissions=permissions,
            openapi_extra=openapi_extra,
        )
        @cls._path_resolver(path)
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
        return delete_item  # type:ignore[no-any-return]

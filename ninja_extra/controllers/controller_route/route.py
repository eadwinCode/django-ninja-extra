from typing import (
    Any,
    List,
    Optional, Dict, Union, TYPE_CHECKING
)
from django.db.models import QuerySet
from ninja.constants import NOT_SET
from ninja.schema import Schema
from ninja.types import TCallable

from ninja_extra.pagination import BasePagination, PageNumberPagination
from ninja_extra.permissions import BasePermission
from ninja_extra.controllers.controller_route.route_functions import (
    RouteFunction, PaginatedRouteFunction, RetrieveObjectRouteFunction
)

if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIController
    from .route_functions import APIContext

__all__ = ["route", 'Route']


class Route:
    route_params = {}
    owner = None

    route_function: RouteFunction = RouteFunction
    object_schema: Any = NOT_SET

    permission_classes: List[BasePermission] = None
    queryset: QuerySet = None
    lookup_field: str
    lookup_url_kwarg: Dict

    pagination_class: BasePagination
    page_size: int
    max_page_size: int

    def __new__(
            cls,
            path: str,
            methods: List[str],
            *,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            route_function: RouteFunction = None,
            **kwargs
    ) -> "Route":
        obj = super().__new__(cls)
        ninja_route_params = dict(
            path=path, methods=methods, auth=auth,
            response=response, operation_id=operation_id,
            summary=summary, description=description, tags=tags,
            deprecated=deprecated, by_alias=by_alias, exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults, exclude_none=exclude_none,
            url_name=url_name, include_in_schema=include_in_schema
        )
        obj.route_params = ninja_route_params
        obj.route_function = route_function or RouteFunction
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    def __call__(self, view_func: TCallable, *args, **kwargs):
        converted_api_func, route_func_instance = self.route_function.from_route(
            api_func=view_func, route_definition=self
        )
        self.view_func = converted_api_func
        return route_func_instance

    def get_paginator(self):
        if self.pagination_class and callable(self.pagination_class):
            return self.pagination_class(page_size=self.page_size, max_page_size=self.max_page_size)
        raise Exception('Please provide a valid pagination class')

    def resolve_queryset(self, controller_instance: "APIController", request_context: "APIContext"):
        if callable(self.queryset):
            return self.queryset(controller_instance, request_context)
        return self.queryset

    def create_view_func_instance(self):
        return self.owner(
            permission_classes=self.permission_classes or self.owner.permission_classes,
            queryset=self.queryset or self.owner.queryset,
            route_definition=self
        )

    @classmethod
    def get(
            cls,
            path: str,
            *,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            route_function: RouteFunction = None,
    ):
        return Route(
            path,
            ["GET"],
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            route_function=route_function,
            object_schema=response,
        )

    @classmethod
    def post(
            cls,
            path: str,
            *,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            route_function: RouteFunction = None,
    ):
        return Route(
            path,
            ["POST"],
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            route_function=route_function,
            object_schema=response
        )

    @classmethod
    def delete(
            cls,
            path: str,
            *,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            route_function: RouteFunction = None,
    ):
        return Route(
            path,
            ["DELETE"],
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            route_function=route_function,
            object_schema=response
        )

    @classmethod
    def patch(
            cls,
            path: str,
            *,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            route_function: RouteFunction = None,
    ):
        return Route(
            path,
            ["PATCH"],
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            route_function=route_function,
            object_schema=response
        )

    @classmethod
    def put(
            cls,
            path: str,
            *,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            route_function: RouteFunction = None,
    ):
        return Route(
            path,
            ["PUT"],
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            route_function=route_function,
            object_schema=response
        )

    @classmethod
    def retrieve(
            cls,
            path: str,
            query_set: Union[TCallable, QuerySet],
            *,
            methods: List[str] = None,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            route_function: RouteFunction = RetrieveObjectRouteFunction
    ):
        return Route(
            path,
            methods=methods or ['GET'],
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            queryset=query_set,
            lookup_field=lookup_field,
            lookup_url_kwarg=lookup_url_kwarg,
            route_function=route_function,
            object_schema=response
        )

    @classmethod
    def list(
            cls,
            path: str,
            query_set: Union[TCallable, QuerySet],
            response: Schema,
            *,
            methods: List[str] = None,
            auth: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            pagination_class: BasePagination = PageNumberPagination,
            page_size=50,
            page_size_max=100,
            route_function: RouteFunction = None
    ):
        if not pagination_class:
            raise Exception('pagination_class can not be None')

        response_schema = pagination_class.get_response_schema()
        return Route(
            path,
            methods=methods or ['GET'],
            auth=auth,
            response=response_schema[response or Any],
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            queryset=query_set,
            lookup_field=lookup_field,
            lookup_url_kwarg=lookup_url_kwarg,
            pagination_class=pagination_class,
            page_size=page_size,
            max_page_size=page_size_max,
            route_function=route_function or PaginatedRouteFunction,
            object_schema=response or NOT_SET
        )

    @classmethod
    def update(
            cls,
            path: str,
            query_set: Union[TCallable, QuerySet],
            *,
            methods: List[str] = None,
            auth: Any = NOT_SET,
            response: Any = NOT_SET,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            route_function: RouteFunction = RetrieveObjectRouteFunction
    ):
        return Route(
            path,
            methods=methods or ['PUT', 'PATCH'],
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            queryset=query_set,
            lookup_field=lookup_field,
            lookup_url_kwarg=lookup_url_kwarg,
            route_function=route_function
        )

    @classmethod
    def generic(
            cls,
            path: str,
            methods: List[str],
            query_set: Union[TCallable, QuerySet],
            *,
            auth: Any = NOT_SET,
            response: Any = None,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            url_name: Optional[str] = None,
            include_in_schema: bool = True,
            permission_classes: List[BasePermission] = None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            pagination_class: BasePagination = PageNumberPagination,
            page_size=50,
            page_size_max=100,
            route_function: RouteFunction = None,
            is_paginated=False,
            is_object_required=True,
    ):
        assert isinstance(methods, list), 'methods must be a list'
        assert not (is_paginated and is_object_required), 'Route can only retrieve object or list objects'

        if is_object_required:
            route_function = route_function or RetrieveObjectRouteFunction

        if is_paginated:
            route_function = route_function or PageNumberPagination
            if not pagination_class:
                raise Exception('pagination_class can not be None')

            response_schema = pagination_class.get_response_schema()
            response = response_schema[response or Any]

        return Route(
            path,
            methods=methods,
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            permission_classes=permission_classes,
            queryset=query_set,
            lookup_field=lookup_field,
            lookup_url_kwarg=lookup_url_kwarg,
            pagination_class=pagination_class,
            page_size=page_size,
            max_page_size=page_size_max,
            route_function=route_function or PaginatedRouteFunction,
            object_schema=response or NOT_SET
        )


route = Route

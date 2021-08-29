import uuid
from typing import (
    Any,
    List,
    Optional, Dict, Union, TYPE_CHECKING, Callable
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
from ninja_extra.schemas import RouteParameter, PaginatedResponseSchema

if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIContext, APIController

__all__ = ["route", 'Route']


class Route:
    route_params: RouteParameter = None
    controller: "APIController" = None

    route_function: RouteFunction = RouteFunction
    object_schema: Any = NOT_SET

    permissions: List[BasePermission] = None
    _queryset: Union[Callable[[Any, "APIContext"], QuerySet], QuerySet] = None
    lookup_field: str
    lookup_url_kwarg: Dict

    pagination_class: BasePagination
    page_size: int
    max_page_size: int

    @property
    def queryset(self) -> Union[Callable[[Any, "APIContext"], QuerySet], QuerySet]:
        return self._queryset

    @queryset.setter
    def queryset(self, value):
        self._queryset = value
        if value and not callable(value):
            self._queryset = lambda controller, context: value

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
        ninja_route_params = RouteParameter(
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
        self.route_params.operation_id = (
                self.route_params.operation_id or
                f"{uuid.uuid4()}_controller_{converted_api_func.__name__}"
        )
        return route_func_instance

    def create_view_func_instance(self, request, *args, **kwargs):
        return self.controller(
            permission_classes=self.permissions,
            queryset=self.queryset,
            route_definition=self,
            request=request, args=args, kwargs=kwargs
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
            permissions: List[BasePermission] = None,
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
            permissions=permissions,
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
            permissions: List[BasePermission] = None,
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
            permissions=permissions,
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
            permissions: List[BasePermission] = None,
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
            permissions=permissions,
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
            permissions: List[BasePermission] = None,
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
            permissions=permissions,
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
            permissions: List[BasePermission] = None,
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
            permissions=permissions,
            route_function=route_function,
            object_schema=response
        )

    @classmethod
    def retrieve(
            cls,
            path: str,
            *,
            query_set: Union[Callable[[Any, "APIContext"], QuerySet], QuerySet] = None,
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
            permissions: List[BasePermission] = None,
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
            permissions=permissions,
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
            query_set: Union[Callable[[Any, "APIContext"], QuerySet], QuerySet],
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
            permissions: List[BasePermission] = None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            pagination_class: BasePagination = PageNumberPagination,
            page_size=50,
            page_size_max=100,
            route_function: RouteFunction = None
    ):
        if not pagination_class:
            raise Exception('pagination_class can not be None')

        response_schema = cls.resolve_paginated_response_schema(pagination_class, response)

        return Route(
            path,
            methods=methods or ['GET'],
            auth=auth,
            response=response_schema,
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
            permissions=permissions,
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
            query_set: Union[Callable[[Any, "APIContext"], QuerySet], QuerySet],
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
            permissions: List[BasePermission] = None,
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
            permissions=permissions,
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
            query_set: Union[Callable[[Any, "APIContext"], QuerySet], QuerySet],
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
            permissions: List[BasePermission] = None,
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
        response_schema = None

        if is_object_required:
            route_function = route_function or RetrieveObjectRouteFunction

        if is_paginated:
            route_function = route_function or PageNumberPagination
            if not pagination_class:
                raise Exception('pagination_class can not be None')

            response_schema = cls.resolve_paginated_response_schema(pagination_class, response)

        return Route(
            path,
            methods=methods,
            auth=auth,
            response=response_schema or response,
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
            permissions=permissions,
            queryset=query_set,
            lookup_field=lookup_field,
            lookup_url_kwarg=lookup_url_kwarg,
            pagination_class=pagination_class,
            page_size=page_size,
            max_page_size=page_size_max,
            route_function=route_function or PaginatedRouteFunction,
            object_schema=response or NOT_SET
        )

    def resolve_paginated_request_schema(self):
        if not self.pagination_class:
            raise Exception('route_definition with pagination_class is required')
        return self.pagination_class.get_request_schema()

    @classmethod
    def resolve_paginated_response_schema(cls, pagination_class: BasePagination, item_schema: Schema):
        schema = pagination_class.get_response_schema()
        if not PaginatedResponseSchema and callable(schema):
            return schema(item_schema)
        return schema[item_schema]

    def create_paginator(self):
        """Create paginator from provided route pagination class"""
        if self.pagination_class and callable(self.pagination_class):
            return self.pagination_class(page_size=self.page_size, max_page_size=self.max_page_size)
        raise Exception('Please provide a valid pagination class')


route = Route

import uuid
from typing import (
    Any,
    List,
    Optional, Dict, Union, TYPE_CHECKING, Callable
)
from django.db.models import QuerySet
from ninja.constants import NOT_SET
from ninja.types import TCallable

from ninja_extra.pagination import BasePagination
from ninja_extra.permissions import BasePermission
from ninja_extra.controllers.controller_route.route_functions import (
    RouteFunction
)
from ninja_extra.schemas import RouteParameter

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
        obj.route_function = RouteFunction
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
                f"{str(uuid.uuid4())[:8]}_controller_{converted_api_func.__name__}"
        )
        return route_func_instance

    def create_view_func_instance(self, request, *args, **kwargs):
        return self.controller(
            permission_classes=self.permissions,
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
            object_schema=response
        )


route = Route

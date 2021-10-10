import uuid
from typing import Any, List, Optional, Type

from ninja.constants import NOT_SET
from ninja.signature import is_async
from ninja.types import TCallable

from ninja_extra.permissions import BasePermission
from ninja_extra.schemas import RouteParameter

from .route_functions import AsyncRouteFunction, RouteFunction

POST = "POST"
PUT = "PUT"
PATCH = "PATCH"
DELETE = "DELETE"
GET = "GET"
ROUTE_METHODS = [POST, PUT, DELETE, GET]


class RouteInvalidParameterException(Exception):
    pass


class Route(object):
    permissions: Optional[Optional[List[Type[BasePermission]]]] = None

    def __init__(
        self,
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
        permissions: Optional[List[Type[BasePermission]]] = None,
    ) -> None:
        ninja_route_params = RouteParameter(
            path=path,
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
        )
        self.route_params = ninja_route_params
        self.is_async = False
        self.permissions = permissions
        self.route_function_class = RouteFunction

    def __call__(self, view_func: TCallable) -> RouteFunction:
        if is_async(view_func):
            self.route_function_class = AsyncRouteFunction

        self.view_func = view_func
        self.route_params.operation_id = (
            self.route_params.operation_id
            or f"{str(uuid.uuid4())[:8]}_controller_{self.view_func.__name__}"
        )
        return self.route_function_class(route=self)

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
        permissions: Optional[List[Type[BasePermission]]] = None,
    ) -> "Route":
        return Route(
            path,
            [GET],
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
        permissions: Optional[List[Type[BasePermission]]] = None,
    ) -> "Route":
        return Route(
            path,
            [POST],
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
        permissions: Optional[List[Type[BasePermission]]] = None,
    ) -> "Route":
        return Route(
            path,
            [DELETE],
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
        permissions: Optional[List[Type[BasePermission]]] = None,
    ) -> "Route":
        return Route(
            path,
            [PATCH],
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
        permissions: Optional[List[Type[BasePermission]]] = None,
    ) -> "Route":
        return Route(
            path,
            [PUT],
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
        )

    @classmethod
    def generic(
        cls,
        path: str,
        *,
        methods: List[str],
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
        permissions: Optional[List[Type[BasePermission]]] = None,
    ) -> "Route":

        if not isinstance(methods, list):
            raise RouteInvalidParameterException("methods must be a list")

        methods = list(map(lambda m: m.upper(), methods))
        for _method in methods:
            if _method not in ROUTE_METHODS:
                raise RouteInvalidParameterException(f"Method {_method} not allowed")

        return Route(
            path,
            methods,
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
        )


route = Route

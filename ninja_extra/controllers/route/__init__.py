import inspect
from typing import Any, List, Optional, Type, Union, cast

from ninja.constants import NOT_SET
from ninja.signature import is_async
from ninja.types import TCallable

from ninja_extra.constants import DELETE, GET, PATCH, POST, PUT, ROUTE_METHODS
from ninja_extra.controllers.response import ControllerResponse, ControllerResponseMeta
from ninja_extra.permissions import BasePermission
from ninja_extra.schemas import RouteParameter

from .route_functions import AsyncRouteFunction, RouteFunction


class RouteInvalidParameterException(Exception):
    pass


def http_get(
    path: str = "",
    *,
    auth: Any = NOT_SET,
    response: Union[Any, List[Any]] = NOT_SET,
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
    """
    A GET Operation method decorator
     eg.

    ```python
    @http_get()
    def get_operation(self):
    ...
    ```
    :param path: uniques endpoint path string
    :param auth: endpoint authentication method. default: `NOT_SET`
    :param response: `dict[status_code, schema]` or `Schema` used validated returned response. default: `None`
    :param operation_id: unique id that distinguishes `operation` in path view. default: `None`
    :param summary: describes your endpoint. default: `None`
    :param description: other description of your endpoint. default: `None`
    :param tags: list of strings for grouping endpoints only for documentation purpose. default: `None`
    :param deprecated: declares an endpoint deprecated. default: `None`
    :param by_alias: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_unset: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_defaults: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_none: pydantic schema filters applied to `response` schema object. default: `False`
    :param url_name: a name to an endpoint which can be resolved using `reverse` function in django. default: `None`
    :param include_in_schema: indicates whether an endpoint should appear on the swagger documentation
    :param permissions: collection permission classes. default: `None`
    :return: Route[GET]
    """
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


def http_post(
    path: str = "",
    *,
    auth: Any = NOT_SET,
    response: Union[Any, List[Any]] = NOT_SET,
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
    """
    A POST Operation method decorator
    eg.

    ```python
     @http_post()
     def post_operation(self,  create_schema: Schema):
        ...
    ```
    :param path: uniques endpoint path string
    :param auth: endpoint authentication method. default: `NOT_SET`
    :param response: `dict[status_code, schema]` or `Schema` used validated returned response. default: `None`
    :param operation_id: unique id that distinguishes `operation` in path view. default: `None`
    :param summary: describes your endpoint. default: `None`
    :param description: other description of your endpoint. default: `None`
    :param tags: list of strings for grouping endpoints only for documentation purpose. default: `None`
    :param deprecated: declares an endpoint deprecated. default: `None`
    :param by_alias: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_unset: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_defaults: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_none: pydantic schema filters applied to `response` schema object. default: `False`
    :param url_name: a name to an endpoint which can be resolved using `reverse` function in django. default: `None`
    :param include_in_schema: indicates whether an endpoint should appear on the swagger documentation
    :param permissions: collection permission classes. default: `None`
    :return: Route[POST]
    """
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


def http_delete(
    path: str = "",
    *,
    auth: Any = NOT_SET,
    response: Union[Any, List[Any]] = NOT_SET,
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
    """
    A DELETE Operation method decorator
    eg.

    ```python
    @http_delete('/{int:some_id}')
    def delete_operation(self, some_id: int):
        ...
    ```
    :param path: uniques endpoint path string
    :param auth: endpoint authentication method. default: `NOT_SET`
    :param response: `dict[status_code, schema]` or `Schema` used validated returned response. default: `None`
    :param operation_id: unique id that distinguishes `operation` in path view. default: `None`
    :param summary: describes your endpoint. default: `None`
    :param description: other description of your endpoint. default: `None`
    :param tags: list of strings for grouping endpoints only for documentation purpose. default: `None`
    :param deprecated: declares an endpoint deprecated. default: `None`
    :param by_alias: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_unset: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_defaults: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_none: pydantic schema filters applied to `response` schema object. default: `False`
    :param url_name: a name to an endpoint which can be resolved using `reverse` function in django. default: `None`
    :param include_in_schema: indicates whether an endpoint should appear on the swagger documentation
    :param permissions: collection permission classes. default: `None`
    :return: Route[DELETE]
    """
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


def http_patch(
    path: str = "",
    *,
    auth: Any = NOT_SET,
    response: Union[Any, List[Any]] = NOT_SET,
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
    """
    A PATCH Operation method decorator
    eg.

    ```python

    @http_patch('/{int:some_id}')
    def patch_operation(self,  some_id: int):
        ...
    ```
    :param path: uniques endpoint path string
    :param auth: endpoint authentication method. default: `NOT_SET`
    :param response: `dict[status_code, schema]` or `Schema` used validated returned response. default: `None`
    :param operation_id: unique id that distinguishes `operation` in path view. default: `None`
    :param summary: describes your endpoint. default: `None`
    :param description: other description of your endpoint. default: `None`
    :param tags: list of strings for grouping endpoints only for documentation purpose. default: `None`
    :param deprecated: declares an endpoint deprecated. default: `None`
    :param by_alias: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_unset: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_defaults: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_none: pydantic schema filters applied to `response` schema object. default: `False`
    :param url_name: a name to an endpoint which can be resolved using `reverse` function in django. default: `None`
    :param include_in_schema: indicates whether an endpoint should appear on the swagger documentation
    :param permissions: collection permission classes. default: `None`
    :return: Route[PATCH]
    """
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


def http_put(
    path: str = "",
    *,
    auth: Any = NOT_SET,
    response: Union[Any, List[Any]] = NOT_SET,
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
    """
     A PUT Operation method decorator
    eg.

    ```python

    @http_put('/{int:some_id}')
    def put_operation(self, some_id: int):
        ...
    ```
     :param path: uniques endpoint path string
     :param auth: endpoint authentication method. default: `NOT_SET`
     :param response: `dict[status_code, schema]` or `Schema` used validated returned response. default: `None`
     :param operation_id: unique id that distinguishes `operation` in path view. default: `None`
     :param summary: describes your endpoint. default: `None`
     :param description: other description of your endpoint. default: `None`
     :param tags: list of strings for grouping endpoints only for documentation purpose. default: `None`
     :param deprecated: declares an endpoint deprecated. default: `None`
     :param by_alias: pydantic schema filters applied to `response` schema object. default: `False`
     :param exclude_unset: pydantic schema filters applied to `response` schema object. default: `False`
     :param exclude_defaults: pydantic schema filters applied to `response` schema object. default: `False`
     :param exclude_none: pydantic schema filters applied to `response` schema object. default: `False`
     :param url_name: a name to an endpoint which can be resolved using `reverse` function in django. default: `None`
     :param include_in_schema: indicates whether an endpoint should appear on the swagger documentation
     :param permissions: collection permission classes. default: `None`
     :return: Route[PUT]
    """
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


def http_generic(
    path: str = "",
    *,
    methods: List[str],
    auth: Any = NOT_SET,
    response: Union[Any, List[Any]] = NOT_SET,
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
    """
    A Custom Operation method decorator, for creating route with more than one operation
    eg.

    ```python

    @http_generic('', methods=['POST', 'GET'])
    def list_create(self, some_schema: Optional[Schema] = None):
       ...
    ```
    :param path: uniques endpoint path string
    :param methods: List of operations `GET, PUT, PATCH, DELETE, POST`
    :param auth: endpoint authentication method. default: `NOT_SET`
    :param response: `dict[status_code, schema]` or `Schema` used validated returned response. default: `None`
    :param operation_id: unique id that distinguishes `operation` in path view. default: `None`
    :param summary: describes your endpoint. default: `None`
    :param description: other description of your endpoint. default: `None`
    :param tags: list of strings for grouping endpoints only for documentation purpose. default: `None`
    :param deprecated: declares an endpoint deprecated. default: `None`
    :param by_alias: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_unset: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_defaults: pydantic schema filters applied to `response` schema object. default: `False`
    :param exclude_none: pydantic schema filters applied to `response` schema object. default: `False`
    :param url_name: a name to an endpoint which can be resolved using `reverse` function in django. default: `None`
    :param include_in_schema: indicates whether an endpoint should appear on the swagger documentation
    :param permissions: collection permission classes. default: `None`
    :return: Route[PATCH]
    """
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


class Route(object):
    """
    APIController Class Route definition method decorator
    That converts class instance methods to `RouteFunction(s) | AsyncRouteFunction(s)`
    """

    permissions: Optional[Optional[List[Type[BasePermission]]]] = None
    get = http_get
    patch = http_patch
    put = http_put
    delete = http_delete
    post = http_post
    generic = http_generic

    def __init__(
        self,
        path: str,
        methods: List[str],
        *,
        auth: Any = NOT_SET,
        response: Union[Any, List[Any]] = NOT_SET,
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

        if not isinstance(methods, list):
            raise RouteInvalidParameterException("methods must be a list")

        methods = list(map(lambda m: m.upper(), methods))
        not_valid_methods = list(set(methods) - set(ROUTE_METHODS))
        if not_valid_methods:
            raise RouteInvalidParameterException(
                f"Method {','.join(not_valid_methods)} not allowed"
            )

        _response = response
        if (
            inspect.isclass(response) and type(response) == ControllerResponseMeta
        ) or isinstance(response, ControllerResponse):
            response = cast(ControllerResponse, response)
            _response = {response.status_code: response.get_schema()}
        elif isinstance(response, list):
            _response_computed = dict()
            for item in response:
                if (
                    inspect.isclass(item) and type(item) == ControllerResponseMeta
                ) or isinstance(item, ControllerResponse):
                    item = cast(ControllerResponse, item)
                    _response_computed.update({item.status_code: item.get_schema()})
                elif isinstance(item, dict):
                    _response_computed.update(item)
                elif isinstance(item, tuple):
                    _response_computed.update({item[0]: item[1]})
            if not _response_computed:
                raise RouteInvalidParameterException(
                    f"Invalid response configuration: {response}"
                )
            _response = _response_computed

        ninja_route_params = RouteParameter(
            path=path,
            methods=methods,
            auth=auth,
            response=_response,
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

    def __call__(self, view_func: TCallable) -> RouteFunction:
        route_function_class = RouteFunction
        if is_async(view_func):
            route_function_class = AsyncRouteFunction

        self.view_func = view_func
        return route_function_class(route=self)


route = Route

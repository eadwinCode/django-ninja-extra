from abc import ABC, ABCMeta
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    cast,
    no_type_check,
)

from injector import inject, is_decorated_with_inject
from ninja import NinjaAPI
from ninja.constants import NOT_SET
from ninja.operation import Operation
from ninja.security.base import AuthBase

from ninja_extra.controllers.route import Route
from ninja_extra.operation import PathView
from ninja_extra.permissions.mixins import APIControllerPermissionMixin
from ninja_extra.shortcuts import fail_silently

from .route.route_functions import RouteFunction
from .router import ControllerRouter

__all__ = ["APIController", "MissingRouterDecoratorException"]


class MissingRouterDecoratorException(Exception):
    pass


class APIControllerModelSchemaMetaclass(ABCMeta):
    @no_type_check
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)
        if name == "APIController" and ABC in bases:
            return cls

        cls = cast(APIController, cls)
        cls._path_operations = {}
        cls.api = namespace.get("api", None)
        cls.registered = False
        cls.permission_classes = None

        if not namespace.get("tags"):
            tag = str(cls.__name__).lower().replace("controller", "")
            cls.tags = [tag]

        for method_route_func in cls.get_route_functions():
            method_route_func.controller = cls
            cls.add_operation_from_route_definition(method_route_func.route_definition)

        if not is_decorated_with_inject(cls.__init__):
            fail_silently(inject, constructor_or_class=cls)
        return cls


class APIController(
    ABC, APIControllerPermissionMixin, metaclass=APIControllerModelSchemaMetaclass
):
    # TODO: implement csrf on route function or on controller level. Which can override api csrf
    #   controller should have a csrf ON unless turned off by api instance
    _path_operations: Dict[str, PathView]
    api: Optional[NinjaAPI]
    args = []
    kwargs = dict()
    auth: AuthBase
    registered: bool
    _router: ControllerRouter = None

    @classmethod
    def get_router(cls):
        if not cls._router:
            raise MissingRouterDecoratorException("Could not register controller")
        return cls._router

    @classmethod
    def get_path_operations(cls):
        return cls._path_operations

    @classmethod
    def add_operation_from_route_definition(cls, route: Route):
        cls.add_api_operation(view_func=route.view_func, **route.route_params.dict())

    @classmethod
    def add_api_operation(
        cls,
        path: str,
        methods: List[str],
        view_func: Callable,
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
    ) -> Operation:
        if path not in cls._path_operations:
            path_view = PathView()
            cls._path_operations[path] = path_view
        else:
            path_view = cls._path_operations[path]
        operation = path_view.add_operation(
            path=path,
            methods=methods,
            view_func=view_func,
            auth=auth or cls.auth,
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
        return operation

    @classmethod
    def get_route_functions(cls) -> Iterator[RouteFunction]:
        for method in cls.__dict__.values():
            if isinstance(method, RouteFunction):
                yield method

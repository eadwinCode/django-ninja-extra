from abc import ABC, ABCMeta
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    cast, no_type_check,
)

from django.db.models import QuerySet
from django.urls import URLPattern, path as django_path
from .route.route_functions import RouteFunction
from ninja.constants import NOT_SET
from ninja_extra.operation import PathView, Operation
from ninja.utils import normalize_path
from ninja_extra.controllers.route import Route
from ninja_extra.permissions.mixins import NinjaExtraAPIPermissionMixin
from ninja import NinjaAPI
from ninja.security.base import AuthBase

__all__ = ["APIController", "APIControllerToNinjaRouter"]


def _get_class_route_functions(**kwargs) -> Iterator[RouteFunction]:
    for method in kwargs.values():
        if isinstance(method, RouteFunction):
            yield method


class APIControllerModelSchemaMetaclass(ABCMeta):
    @no_type_check
    def __new__(
            mcs, name: str, bases: tuple, namespace: dict
    ):
        cls = super().__new__(mcs, name, bases, namespace)
        if name == 'APIController' and ABC in bases:
            return cls

        cls = cast(APIController, cls)
        cls._path_operations = {}
        cls.prefix = namespace.get('prefix', None)
        cls.auth = namespace.get('auth', None)
        cls.api = namespace.get('api', None)
        cls.registered = False

        if not namespace.get('tags'):
            tag = str(cls.__name__).lower().replace('controller', '')
            cls.tags = [tag]

        for method_route_func in _get_class_route_functions(**namespace):
            method_route_func.controller = cls
            method_route_func.route_definition.permissions = (
                    method_route_func.route_definition.permissions or cls.permission_classes
            )
            cls.add_operation_from_route_definition(method_route_func.route_definition)
        return cls


class APIController(
    ABC,
    NinjaExtraAPIPermissionMixin,
    metaclass=APIControllerModelSchemaMetaclass
):
    _path_operations: Dict[str, PathView]
    api: Optional[NinjaAPI]
    queryset: QuerySet = None
    args = []
    kwargs = dict()
    prefix: str
    auth: AuthBase
    registered: bool

    @classmethod
    def path_operations(cls):
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
            include_in_schema=include_in_schema
        )
        return operation


class APIControllerToNinjaRouter:
    @property
    def path_operations(self):
        return self.api_controller.path_operations()

    def __init__(self, api_controller: APIController):
        self.api_controller = api_controller

    def set_api_instance(self, api: "NinjaAPI") -> None:
        self.api_controller.api = api
        for path_view in self.path_operations.values():
            path_view.set_api_instance(api, self.api_controller)

    def build_routers(self) -> List[Tuple[str, "APIController"]]:
        internal_routes = []
        return [(self.api_controller.prefix, self), *internal_routes]

    def urls_paths(self, prefix: str) -> Iterator[URLPattern]:
        for path, path_view in self.path_operations.items():
            path = path.replace("{", "<").replace("}", ">")
            route = "/".join([i for i in (prefix, path) if i])
            # to skip lot of checks we simply treat double slash as a mistake:
            route = normalize_path(route)
            route = route.lstrip("/")

            yield django_path(
                route, path_view.get_view(), name=cast(str, path_view.url_name)
            )

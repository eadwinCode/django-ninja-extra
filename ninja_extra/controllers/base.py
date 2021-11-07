from abc import ABC, ABCMeta
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    Union,
    cast,
    no_type_check,
)

from django.http.request import HttpRequest
from injector import inject, is_decorated_with_inject
from ninja import NinjaAPI
from ninja.constants import NOT_SET
from ninja.operation import Operation
from ninja.security.base import AuthBase
from ninja.types import DictStrAny

from ninja_extra.exceptions import PermissionDenied
from ninja_extra.operation import PathView
from ninja_extra.permissions import BasePermission
from ninja_extra.permissions.base import OperandHolder
from ninja_extra.shortcuts import fail_silently

from .route.route_functions import RouteFunction
from .router import ControllerRouter


class MissingRouterDecoratorException(Exception):
    pass


def compute_api_route_function(
    base_cls: Type["APIController"], controller: Optional[Type["APIController"]] = None
) -> None:
    controller = controller if controller else base_cls
    for cls_route_function in base_cls.get_route_functions():
        cls_route_function.controller = controller
        controller.add_operation_from_route_function(cls_route_function)


class APIControllerModelMetaclass(ABCMeta):
    @no_type_check
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)
        if name == "APIController" and ABC in bases:
            return cls

        cls = cast(Type[APIController], cls)
        cls._path_operations = {}
        cls.api = namespace.get("api", None)
        cls.registered = False
        cls.permission_classes = None

        if not namespace.get("tags"):
            tag = str(cls.__name__).lower().replace("controller", "")
            cls.tags = [tag]

        if len(bases) > 1:
            for base_cls in reversed(bases):
                if issubclass(base_cls, APIController):
                    compute_api_route_function(base_cls, cls)

        compute_api_route_function(cls)
        if not is_decorated_with_inject(cls.__init__):
            fail_silently(inject, constructor_or_class=cls)
        return cls


class APIController(ABC, metaclass=APIControllerModelMetaclass):
    # TODO: implement csrf on route function or on controller level. Which can override api csrf
    #   controller should have a csrf ON unless turned off by api instance
    auto_import = (
        True  # set to false and it would be ignored when api.auto_discover is called
    )
    _path_operations: Dict[str, PathView]
    api: Optional[NinjaAPI] = None
    args: List[Any] = []
    kwargs: DictStrAny = dict()
    auth: Optional[AuthBase] = None

    registered: bool
    _router: Optional[ControllerRouter] = None
    permission_classes: Union[List[Type[BasePermission]], List[OperandHolder[Any]]]
    request: Optional[HttpRequest] = None
    tags: List[str] = []

    @classmethod
    def get_router(cls) -> ControllerRouter:
        if not cls._router:
            raise MissingRouterDecoratorException(
                "Controller Router not found. "
                "Did you forget to use the `router` decorator"
            )
        return cls._router

    @classmethod
    def get_path_operations(cls) -> DictStrAny:
        return cls._path_operations

    @classmethod
    def add_operation_from_route_function(cls, route_function: RouteFunction) -> None:
        cls.add_api_operation(
            view_func=route_function.as_view, **route_function.route.route_params.dict()
        )

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

    @classmethod
    def permission_denied(cls, permission: BasePermission) -> None:
        message = getattr(permission, "message", None)
        raise PermissionDenied(message)

    def get_permissions(self) -> Iterator[BasePermission]:
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        for permission_class in self.permission_classes:
            permission_instance = permission_class()
            yield permission_instance

    def check_permissions(self) -> None:
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if self.request and not permission.has_permission(
                request=self.request, controller=self
            ):
                self.permission_denied(permission)

    def check_object_permissions(self, obj: Any) -> None:
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if self.request and not permission.has_object_permission(
                request=self.request, controller=self, obj=obj
            ):
                self.permission_denied(permission)

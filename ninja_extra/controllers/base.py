from abc import ABC, ABCMeta
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    cast,
    no_type_check,
)

from injector import inject, is_decorated_with_inject
from ninja import NinjaAPI
from ninja.constants import NOT_SET
from ninja.operation import Operation
from ninja.security.base import AuthBase
from ninja.types import DictStrAny

from ninja_extra.exceptions import PermissionDenied
from ninja_extra.operation import PathView
from ninja_extra.permissions import AllowAny, BasePermission
from ninja_extra.shortcuts import fail_silently
from ninja_extra.types import PermissionType

from .response import ControllerResponse, Detail, Id, Ok
from .route.route_functions import RouteFunction
from .router import ControllerRouter

if TYPE_CHECKING:
    from .route.context import RouteContext


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

    # `_path_operations` a converted dict of APIController route function used by Django-Ninja library
    _path_operations: Dict[str, PathView]
    # `api` a reference to NinjaExtraAPI on APIController registration
    api: Optional[NinjaAPI] = None
    # `auth` primarily defines APIController route function global authentication method.
    auth: Optional[AuthBase] = None
    # `registered` prevents controllers from being register twice or exist in two different `api` instances
    registered: bool
    # `_router` a reference to ControllerRouter of any APIController with a ControllerRouter decorator
    _router: Optional[ControllerRouter] = None
    # `permission_classes` primarily holds permission defined by the ControllerRouter and its used as
    # a fallback if route functions has no permissions definition
    permission_classes: PermissionType = [AllowAny]  # type: ignore
    # `tags` is a property for grouping endpoint in Swagger API docs
    tags: List[str] = []

    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: Optional["RouteContext"] = None

    Ok = Ok
    Id = Id
    Detail = Detail

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
        # converts route functions to Operation model
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
        if not self.context:
            return

        for permission_class in self.context.permission_classes:
            permission_instance = permission_class()
            yield permission_instance

    def check_permissions(self) -> None:
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if (
                self.context
                and self.context.request
                and not permission.has_permission(
                    request=self.context.request, controller=self
                )
            ):
                self.permission_denied(permission)

    def check_object_permissions(self, obj: Any) -> None:
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if (
                self.context
                and self.context.request
                and not permission.has_object_permission(
                    request=self.context.request, controller=self, obj=obj
                )
            ):
                self.permission_denied(permission)

    def create_response(
        self, message: Any, status_code: int = 200
    ) -> ControllerResponse:
        return self.Detail(message=message, status_code=status_code)

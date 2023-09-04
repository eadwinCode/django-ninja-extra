import inspect
import re
import uuid
from abc import ABC
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
    overload,
)

from django.db.models import Model, QuerySet
from django.http import HttpResponse
from django.urls import URLPattern
from django.urls import path as django_path
from injector import inject, is_decorated_with_inject
from ninja import NinjaAPI, Router
from ninja.constants import NOT_SET
from ninja.security.base import AuthBase
from ninja.signature import is_async
from ninja.utils import normalize_path

from ninja_extra.constants import ROUTE_FUNCTION, THROTTLED_FUNCTION
from ninja_extra.exceptions import APIException, NotFound, PermissionDenied, bad_request
from ninja_extra.helper import get_function_name
from ninja_extra.operation import ControllerPathView, Operation
from ninja_extra.permissions import AllowAny, BasePermission
from ninja_extra.permissions.base import OperationHolderMixin
from ninja_extra.shortcuts import (
    fail_silently,
    get_object_or_exception,
    get_object_or_none,
)
from ninja_extra.types import PermissionType

from .registry import ControllerRegistry
from .response import Detail, Id, Ok
from .route.route_functions import AsyncRouteFunction, RouteFunction

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra import NinjaExtraAPI
    from ninja_extra.throttling import BaseThrottle

    from .route.context import RouteContext


class MissingAPIControllerDecoratorException(Exception):
    pass


def get_route_functions(cls: Type) -> Iterable[RouteFunction]:
    for method in cls.__dict__.values():
        if hasattr(method, ROUTE_FUNCTION):
            yield getattr(method, ROUTE_FUNCTION)


def get_all_controller_route_function(
    controller: Union[Type["ControllerBase"], Type]
) -> List[RouteFunction]:  # pragma: no cover
    route_functions: List[RouteFunction] = []
    for item in dir(controller):
        attr = getattr(controller, item)
        if isinstance(attr, RouteFunction):
            route_functions.append(attr)
    return route_functions


def compute_api_route_function(
    base_cls: Type, api_controller_instance: "APIController"
) -> None:
    for cls_route_function in get_route_functions(base_cls):
        cls_route_function.api_controller = api_controller_instance
        api_controller_instance.add_controller_route_function(cls_route_function)


class ControllerBase(ABC):
    """
    Abstract Controller Base implementation all Controller class should implement

    Example:
    ---------
    ```python
    from ninja_extra import api_controller, ControllerBase, http_get

    @api_controller
    class SomeController(ControllerBase):
        @http_get()
        def some_method_name(self):
            ...
    ```
    Inheritance Example
    -------------------
    ```python

    @api_controller
    class AnotherController(SomeController):
        @http_get()
        def some_method_name(self):
            ...
    ```
    """

    # `_api_controller` a reference to APIController instance
    _api_controller: Optional["APIController"] = None

    # `api` a reference to NinjaExtraAPI on APIController registration
    api: Optional[NinjaAPI] = None

    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: Optional["RouteContext"] = None
    throttling_classes: List["BaseThrottle"] = []
    throttling_init_kwargs: Optional[Dict[Any, Any]] = None

    Ok = Ok
    Id = Id
    Detail = Detail
    bad_request = bad_request

    @classmethod
    def get_api_controller(cls) -> "APIController":
        if not cls._api_controller:
            raise MissingAPIControllerDecoratorException(
                "api_controller not found. "
                "Did you forget to use the `api_controller` decorator"
            )
        return cls._api_controller

    @classmethod
    def permission_denied(cls, permission: BasePermission) -> None:
        message = getattr(permission, "message", None)
        raise PermissionDenied(message)

    def get_object_or_exception(
        self,
        klass: Union[Type[Model], QuerySet],
        error_message: Optional[str] = None,
        exception: Type[APIException] = NotFound,
        **kwargs: Any,
    ) -> Any:
        obj = get_object_or_exception(
            klass=klass, error_message=error_message, exception=exception, **kwargs
        )
        self.check_object_permissions(obj)
        return obj

    def get_object_or_none(
        self, klass: Union[Type[Model], QuerySet], **kwargs: Any
    ) -> Optional[Any]:
        obj = get_object_or_none(klass=klass, **kwargs)
        if obj:
            self.check_object_permissions(obj)
        return obj

    def _get_permissions(self) -> Iterable[BasePermission]:
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        assert self.context

        for permission_class in self.context.permission_classes:
            if isinstance(permission_class, (type, OperationHolderMixin)):
                permission_instance = permission_class()  # type: ignore[operator]
            else:
                permission_instance = permission_class
            yield permission_instance

    def check_permissions(self) -> None:
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self._get_permissions():
            if (
                self.context
                and self.context.request
                and not permission.has_permission(
                    request=self.context.request, controller=self
                )
            ):
                self.permission_denied(permission)

    def check_object_permissions(self, obj: Union[Any, Model]) -> None:
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self._get_permissions():
            if (
                self.context
                and self.context.request
                and not permission.has_object_permission(
                    request=self.context.request, controller=self, obj=obj
                )
            ):
                self.permission_denied(permission)

    def create_response(
        self, message: Any, status_code: int = 200, **kwargs: Any
    ) -> HttpResponse:
        assert self.api and self.context and self.context.request
        content = self.api.renderer.render(
            self.context.request, message, response_status=status_code
        )
        content_type = "{}; charset={}".format(
            self.api.renderer.media_type, self.api.renderer.charset
        )
        return HttpResponse(
            content, status=status_code, content_type=content_type, **kwargs
        )


class APIController:
    _PATH_PARAMETER_COMPONENT_RE = r"{(?:(?P<converter>[^>:]+):)?(?P<parameter>[^>]+)}"

    """
    A class decorator

    Features
    --
    - Converts class to APIController
    - Forces class to inherit from `ControllerBase` if missing
    - Adapts class to Django-Ninja router

    Usage:
    ---------
    ```python
    from ninja_extra import api_controller, ControllerBase, http_post, http_get

    @api_controller
    class SomeController:
        @http_get()
        def some_method_name(self):
            ...

    assert issubclass(SomeController, ControllerBase) # true

    @api_controller
    class AnotherController(ControllerBase):
        @http_post()
        def some_method_name(self):
            ...
    ```
    You can more code intellisense within a controller decorated class when it inherits from `ControllerBase`
    as shown with `AnotherController` example.
    """

    # TODO: implement csrf on route function or on controller level. Which can override api csrf
    #   controller should have a csrf ON unless turned off by api instance

    def __init__(
        self,
        prefix: str,
        *,
        auth: Any = NOT_SET,
        tags: Union[Optional[List[str]], str] = None,
        permissions: Optional["PermissionType"] = None,
        auto_import: bool = True,
    ) -> None:
        self.prefix = prefix
        # `auth` primarily defines APIController route function global authentication method.
        self.auth: Optional[AuthBase] = auth

        self.tags = tags  # type: ignore

        self.auto_import: bool = auto_import  # set to false and it would be ignored when api.auto_discover is called
        # `controller_class` target class that the APIController wraps
        self._controller_class: Optional[Type["ControllerBase"]] = None
        # `_path_operations` a converted dict of APIController route function used by Django-Ninja library
        self._path_operations: Dict[str, ControllerPathView] = {}
        self._controller_class_route_functions: Dict[str, RouteFunction] = {}
        # `permission_classes` a collection of BasePermission Types
        # a fallback if route functions has no permissions definition
        self.permission_classes: PermissionType = permissions or [AllowAny]
        # `registered` prevents controllers from being register twice or exist in two different `api` instances
        self.registered: bool = False

        self._prefix_has_route_param = False

        if re.search(self._PATH_PARAMETER_COMPONENT_RE, prefix):
            self._prefix_has_route_param = True

        self.has_auth_async = False
        if auth is not NOT_SET:
            auth_callbacks = isinstance(auth, Sequence) and auth or [auth]
            for _auth in auth_callbacks:
                _call_back = _auth if inspect.isfunction(_auth) else _auth.__call__
                if is_async(_call_back):
                    self.has_auth_async = True
                    break

    @property
    def controller_class(self) -> Type["ControllerBase"]:
        assert self._controller_class, "Controller Class is not available"
        return self._controller_class

    @property
    def tags(self) -> Optional[List[str]]:
        # `tags` is a property for grouping endpoint in Swagger API docs
        return self._tags

    @tags.setter
    def tags(self, value: Union[str, List[str], None]) -> None:
        tag: Optional[List[str]] = cast(Optional[List[str]], value)
        if tag and isinstance(value, str):
            tag = [value]
        self._tags = tag

    def __call__(self, cls: Type) -> Union[Type, Type["ControllerBase"]]:
        from ninja_extra.throttling import throttle

        self.auto_import = getattr(cls, "auto_import", self.auto_import)
        if not issubclass(cls, ControllerBase):
            # We force the cls to inherit from `ControllerBase` by creating another type.
            cls = type(cls.__name__, (ControllerBase, cls), {"_api_controller": self})
        else:
            cls._api_controller = self

        assert isinstance(
            cls.throttling_classes, (list, tuple)
        ), f"Controller[{cls.__name__}].throttling_class must be a list or tuple"
        has_throttling_classes = len(cls.throttling_classes) > 0
        throttling_init_kwargs = cls.throttling_init_kwargs or {}

        if not self.tags:
            tag = str(cls.__name__).lower().replace("controller", "")
            self.tags = [tag]

        self._controller_class = cls
        bases = inspect.getmro(cls)
        for base_cls in reversed(bases):
            if base_cls not in [ControllerBase, ABC, object]:
                compute_api_route_function(base_cls, self)

        for _, v in self._controller_class_route_functions.items():
            throttled_endpoint = v.as_view.__dict__.get(THROTTLED_FUNCTION)
            if not throttled_endpoint and has_throttling_classes:
                v.route.view_func = throttle(
                    *cls.throttling_classes, **throttling_init_kwargs
                )(v.route.view_func)
            self._add_operation_from_route_function(v)

        if not is_decorated_with_inject(cls.__init__):
            fail_silently(inject, constructor_or_class=cls)

        ControllerRegistry().add_controller(cls)
        return cls

    @property
    def path_operations(self) -> Dict[str, ControllerPathView]:
        return self._path_operations

    def set_api_instance(self, api: "NinjaExtraAPI") -> None:
        self.controller_class.api = api
        for path_view in self.path_operations.values():
            path_view.set_api_instance(api, cast(Router, self))

    def build_routers(self) -> List[Tuple[str, "APIController"]]:
        prefix = self.prefix
        if self._prefix_has_route_param:
            prefix = ""
        return [(prefix, self)]

    def add_controller_route_function(self, route_function: RouteFunction) -> None:
        self._controller_class_route_functions[
            get_function_name(route_function.route.view_func)
        ] = route_function

    def urls_paths(self, prefix: str) -> Iterator[URLPattern]:
        for path, path_view in self.path_operations.items():
            path = path.replace("{", "<").replace("}", ">")
            route = "/".join([i for i in (prefix, path) if i])
            # to skip lot of checks we simply treat double slash as a mistake:
            route = normalize_path(route)
            route = route.lstrip("/")
            for op in path_view.operations:
                op = cast(Operation, op)
                yield django_path(route, path_view.get_view(), name=op.url_name)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<controller - {self.controller_class.__name__}>"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.controller_class.__name__}"

    def _add_operation_from_route_function(self, route_function: RouteFunction) -> None:
        # converts route functions to Operation model
        if route_function.route.route_params.operation_id is None:
            route_function.route.route_params.operation_id = f"{str(uuid.uuid4())[:8]}_controller_{route_function.route.view_func.__name__}"

        if (
            self.auth
            and self.has_auth_async
            and not isinstance(route_function, AsyncRouteFunction)
        ):
            raise Exception(
                f"You are using a Controller level Asynchronous Authentication Class, "
                f"All controller endpoint must be `async`.\n"
                f"Controller={self.controller_class.__name__}, "
                f"endpoint={get_function_name(route_function.route.view_func)}"
            )

        route_function.operation = self.add_api_operation(  # type: ignore
            view_func=route_function.as_view, **route_function.route.route_params.dict()
        )

    def add_api_operation(
        self,
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
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Operation:
        auth = self.auth if auth == NOT_SET else auth

        if self._prefix_has_route_param:
            path = normalize_path("/".join([i for i in (self.prefix, path) if i]))
        if path not in self._path_operations:
            path_view = ControllerPathView()
            self._path_operations[path] = path_view
        else:
            path_view = self._path_operations[path]
        operation = path_view.add_operation(
            path=path,
            methods=methods,
            view_func=view_func,
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
            openapi_extra=openapi_extra,
        )
        return operation


@overload
def api_controller(
    prefix_or_class: Type,
) -> Union[Type[ControllerBase], Callable[..., Any], Any]:  # pragma: no cover
    ...


@overload
def api_controller(
    prefix_or_class: str = "",
    auth: Any = NOT_SET,
    tags: Union[Optional[List[str]], str] = None,
    permissions: Optional["PermissionType"] = None,
    auto_import: bool = True,
) -> Union[Type[ControllerBase], Callable[..., Any], Any]:  # pragma: no cover
    ...


def api_controller(
    prefix_or_class: Union[str, Type] = "",
    auth: Any = NOT_SET,
    tags: Union[Optional[List[str]], str] = None,
    permissions: Optional["PermissionType"] = None,
    auto_import: bool = True,
) -> Union[Type[ControllerBase], Callable[..., Any], Any]:
    if isinstance(prefix_or_class, type):
        return APIController(
            prefix="",
            auth=auth,
            tags=tags,
            permissions=permissions,
            auto_import=auto_import,
        )(prefix_or_class)

    def _decorator(cls: Type) -> Union[Type[ControllerBase], Any]:
        return APIController(
            prefix=str(prefix_or_class),
            auth=auth,
            tags=tags,
            permissions=permissions,
            auto_import=auto_import,
        )(cls)

    return _decorator

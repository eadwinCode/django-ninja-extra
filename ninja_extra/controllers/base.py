"""
Base class for APIController.
"""

import inspect
import re
import typing as t
import uuid
import warnings

from django.db.models import Model, QuerySet
from django.http import HttpResponse
from django.urls import URLPattern, URLResolver, include
from django.urls import path as django_path
from injector import inject, is_decorated_with_inject
from ninja import Router
from ninja.constants import NOT_SET, NOT_SET_TYPE
from ninja.security.base import AuthBase
from ninja.signature import is_async
from ninja.throttling import BaseThrottle
from ninja.utils import normalize_path

from ninja_extra.constants import (
    API_CONTROLLER_INSTANCE,
    CONTROLLER_WATERMARK,
    NINJA_EXTRA_API_CONTROLLER_REGISTERED_KEY,
    OPERATION_ENDPOINT_KEY,
    ROUTE_OBJECT,
    THROTTLED_FUNCTION,
    THROTTLED_OBJECTS,
)
from ninja_extra.context import RouteContext
from ninja_extra.exceptions import APIException, NotFound, PermissionDenied
from ninja_extra.helper import get_function_name
from ninja_extra.operation import Operation, PathView
from ninja_extra.permissions import (
    AllowAny,
    AsyncBasePermission,
    BasePermission,
    BasePermissionType,
)
from ninja_extra.reflect import reflect
from ninja_extra.shortcuts import (
    aget_object_or_exception,
    aget_object_or_none,
    fail_silently,
    get_object_or_exception,
    get_object_or_none,
)

from .model import ModelConfig, ModelControllerBuilder, ModelService
from .registry import controller_registry
from .route.route_functions import AsyncRouteFunction, RouteFunction

if t.TYPE_CHECKING:  # pragma: no cover
    from ninja_extra import NinjaExtraAPI
    from ninja_extra.controllers.model import ModelConfig
    from ninja_extra.controllers.route import Route

T = t.TypeVar("T")


def get_route_functions(
    klass: t.Type,
    api_controller_instance: "APIController",
) -> t.Iterator[RouteFunction]:
    """
    Get all route functions from a class, creating RouteFunction instances from decorated methods.

    This function scans a class for methods decorated with route decorators (e.g., @http_get, @http_post)
    and yields RouteFunction or AsyncRouteFunction instances for each.

    :param klass: The class to scan for route functions
    :param api_controller_instance: The APIController instance associated with the class
    :return: An iterator of RouteFunction instances
    """

    for _, method in inspect.getmembers(klass, predicate=inspect.isfunction):
        if hasattr(method, OPERATION_ENDPOINT_KEY):
            route_obj: "Route" = reflect.get_metadata_or_raise_exception(
                ROUTE_OBJECT, method
            )
            if route_obj.is_async:
                yield AsyncRouteFunction(
                    route_obj, api_controller=api_controller_instance
                )
            else:
                yield RouteFunction(route_obj, api_controller=api_controller_instance)


def compute_api_route_function(
    base_cls: t.Type, api_controller_instance: "APIController"
) -> None:
    controller_routes = list(get_route_functions(base_cls, api_controller_instance))
    controller_routes.reverse()
    for cls_route_function in controller_routes:
        api_controller_instance.add_controller_route_function(cls_route_function)


class ControllerBase:
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

    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: t.Optional["RouteContext"] = None
    throttling_classes: t.List[t.Type["BaseThrottle"]] = []
    throttling_init_kwargs: t.Optional[t.Dict[t.Any, t.Any]] = None

    @classmethod
    def permission_denied(
        cls, permission: t.Union[BasePermission, AsyncBasePermission]
    ) -> None:
        """
        This method is called when the permission check fails. By default, it raises an exception.
        Adapt this method to your needs if you need to raise different exceptions depending on the permission type.
        """
        message = getattr(permission, "message", None)
        raise PermissionDenied(message)

    def get_object_or_exception(
        self,
        klass: t.Union[t.Type[Model], QuerySet],
        error_message: t.Optional[str] = None,
        exception: t.Type[APIException] = NotFound,
        **kwargs: t.Any,
    ) -> t.Any:
        obj = get_object_or_exception(
            klass=klass, error_message=error_message, exception=exception, **kwargs
        )
        self.check_object_permissions(obj)
        return obj

    async def aget_object_or_exception(
        self,
        klass: t.Union[t.Type[Model], QuerySet],
        error_message: t.Optional[str] = None,
        exception: t.Type[APIException] = NotFound,
        **kwargs: t.Any,
    ) -> t.Any:
        obj = await aget_object_or_exception(
            klass=klass, error_message=error_message, exception=exception, **kwargs
        )
        await self.async_check_object_permissions(obj)
        return obj

    def get_object_or_none(
        self, klass: t.Union[t.Type[Model], QuerySet], **kwargs: t.Any
    ) -> t.Optional[t.Any]:
        obj = get_object_or_none(klass=klass, **kwargs)
        if obj:
            self.check_object_permissions(obj)
        return obj

    async def aget_object_or_none(
        self, klass: t.Union[t.Type[Model], QuerySet], **kwargs: t.Any
    ) -> t.Optional[t.Any]:
        obj = await aget_object_or_none(klass=klass, **kwargs)
        if obj:
            await self.async_check_object_permissions(obj)
        return obj

    def _get_permissions(
        self,
    ) -> t.Iterable[t.Union[BasePermission, AsyncBasePermission]]:
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        assert self.context

        for permission_class in self.context.permission_classes:
            permission_instance: t.Union[BasePermission, AsyncBasePermission] = (
                permission_class  # type: ignore[assignment]
            )
            if isinstance(permission_class, type) and issubclass(
                permission_class, BasePermission
            ):
                permission_instance = permission_class.resolve()

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

    def check_object_permissions(self, obj: t.Union[t.Any, Model]) -> None:
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

    async def async_check_permissions(self) -> None:
        """
        Asynchronous version of check_permissions.
        Check if the request should be permitted, using async permission checks when available.
        Raises an appropriate exception if the request is not permitted.
        """

        if not self.context or not self.context.request:  # pragma: no cover
            return

        for permission in self._get_permissions():
            has_permission = False
            if isinstance(permission, AsyncBasePermission):
                has_permission = await permission.has_permission_async(
                    request=self.context.request, controller=self
                )
            else:
                from asgiref.sync import sync_to_async

                has_permission = await sync_to_async(permission.has_permission)(
                    request=self.context.request, controller=self
                )

            if not has_permission:
                self.permission_denied(permission)

    async def async_check_object_permissions(self, obj: t.Union[t.Any, Model]) -> None:
        """
        Asynchronous version of check_object_permissions.
        Check if the request should be permitted for a given object, using async permission checks when available.
        Raises an appropriate exception if the request is not permitted.
        """
        if not self.context or not self.context.request:  # pragma: no cover
            return

        for permission in self._get_permissions():
            has_permission = False
            if isinstance(permission, AsyncBasePermission):
                has_permission = await permission.has_object_permission_async(
                    request=self.context.request, controller=self, obj=obj
                )
            else:
                from asgiref.sync import sync_to_async

                has_permission = await sync_to_async(permission.has_object_permission)(
                    request=self.context.request, controller=self, obj=obj
                )

            if not has_permission:
                self.permission_denied(permission)

    def create_response(
        self, message: t.Any, status_code: int = 200, **kwargs: t.Any
    ) -> HttpResponse:
        assert self.context and self.context.request
        content = self.context.api.renderer.render(
            self.context.request, message, response_status=status_code
        )
        content_type = "{}; charset={}".format(
            self.context.api.renderer.media_type, self.context.api.renderer.charset
        )
        return HttpResponse(
            content, status=status_code, content_type=content_type, **kwargs
        )


class ModelControllerBase(ControllerBase):
    """
    An abstract base class for all Model Controllers

    Example:
    ---------
    ```python
    from ninja_extra import api_controller, ModelControllerBase, ModelConfig
    from .model import Post

    @api_controller
    class SomeController(ControllerBase):
        model_config = ModelConfig(model=Post)

    ```
    """

    service_type: t.Type[ModelService] = ModelService

    def __init__(self, service: ModelService):
        self.service = service

    model_config: t.Optional["ModelConfig"] = None


ControllerClassType = t.TypeVar(
    "ControllerClassType",
    bound=t.Union[t.Type[ControllerBase], t.Type],
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
        auth: t.Any = NOT_SET,
        throttle: t.Union[BaseThrottle, t.List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
        tags: t.Union[t.Optional[t.List[str]], str] = None,
        permissions: t.Optional[t.List[BasePermissionType]] = None,
        auto_import: bool = True,
        urls_namespace: t.Optional[str] = None,
        use_unique_op_id: bool = True,
    ) -> None:
        self.prefix = prefix
        # Optional controller-level URL namespace. Applied to all route paths.
        self.urls_namespace = urls_namespace or None
        # `auth` primarily defines APIController route function global authentication method.
        self.auth: t.Optional[AuthBase] = auth

        self.tags = tags  # type: ignore
        self.throttle = throttle
        self.use_unique_op_id = use_unique_op_id

        self.auto_import: bool = auto_import  # set to false and it would be ignored when api.auto_discover is called
        # `controller_class` target class that the APIController wraps
        self._controller_class: t.Optional[t.Type["ControllerBase"]] = None
        # `_path_operations` a converted dict of APIController route function used by Django-Ninja library
        self._path_operations: t.Dict[str, PathView] = {}
        self._controller_class_route_functions: t.Dict[str, RouteFunction] = {}
        # `permission_classes` a collection of BasePermission Types
        # a fallback if route functions has no permissions definition
        self.permission_classes: t.List[BasePermissionType] = permissions or [AllowAny]

        self._prefix_has_route_param = False

        if re.search(self._PATH_PARAMETER_COMPONENT_RE, prefix):
            self._prefix_has_route_param = True

        self.has_auth_async = False
        if auth and auth is not NOT_SET:
            auth_callbacks = isinstance(auth, t.Sequence) and auth or [auth]
            for _auth in auth_callbacks:
                _call_back = _auth if inspect.isfunction(_auth) else _auth.__call__
                if is_async(_call_back):
                    self.has_auth_async = True
                    break
        # `_prefix_route_params` a collection of route parameters that are used in the prefix
        # for example:
        # `api_controller("/{int:id}/{str:name}/{slug}")` will have `_prefix_route_params` = {"id": int, "name": str, "slug": str}
        self._prefix_route_params = {}
        if self._prefix_has_route_param:
            for match in re.finditer(self._PATH_PARAMETER_COMPONENT_RE, self.prefix):
                self._prefix_route_params[match.group("parameter")] = match.group(
                    "converter"
                )

    @property
    def prefix_route_params(self) -> t.Dict[str, str]:
        return self._prefix_route_params

    @property
    def controller_class(self) -> t.Type["ControllerBase"]:
        assert self._controller_class, "Controller Class is not available"
        return self._controller_class

    @property
    def tags(self) -> t.Optional[t.List[str]]:
        # `tags` is a property for grouping endpoint in Swagger API docs
        return self._tags

    @tags.setter
    def tags(self, value: t.Union[str, t.List[str], None]) -> None:
        tag: t.Optional[t.List[str]] = t.cast(t.Optional[t.List[str]], value)
        if tag and isinstance(value, str):
            tag = [value]
        self._tags = tag

    def __call__(self, cls: ControllerClassType) -> ControllerClassType:
        self.auto_import = getattr(cls, "auto_import", self.auto_import)
        if not issubclass(cls, ControllerBase):
            # We force the cls to inherit from `ControllerBase` by creating another type.
            cls = type(cls.__name__, (ControllerBase, cls), {})  # type:ignore[assignment]

        if reflect.has_metadata(API_CONTROLLER_INSTANCE, cls):
            raise Exception("Controller is already decorated with @api_controller")

        reflect.define_metadata(API_CONTROLLER_INSTANCE, self, cls)
        reflect.define_metadata(CONTROLLER_WATERMARK, True, cls)

        assert isinstance(cls.throttling_classes, (list, tuple)), (
            f"Controller[{cls.__name__}].throttling_class must be a list or tuple"
        )

        throttling_objects: t.Union[
            BaseThrottle, t.List[BaseThrottle], NOT_SET_TYPE
        ] = NOT_SET

        if self.throttle is not NOT_SET:
            throttling_objects = self.throttle
        elif cls.throttling_classes:
            throttling_init_kwargs = cls.throttling_init_kwargs or {}
            throttling_objects = [
                item(**throttling_init_kwargs) for item in cls.throttling_classes
            ]

        class_name = str(cls.__name__).lower().replace("controller", "")
        if not self.tags:
            self.tags = [class_name]

        self._controller_class = cls
        # if not self.urls_namespace:
        #     # if urls_namespace is not provided, use the class name as the namespace
        #     self.urls_namespace = class_name
        if issubclass(cls, ModelControllerBase):
            if cls.model_config:
                assert cls.service_type is not None, (
                    "service_type is required for ModelControllerBase"
                )
                # if model_config is not provided, treat controller class as normal
                builder = ModelControllerBuilder(cls, self)
                builder.register_model_routes()
                # We create a global service for handle CRUD Operations at class level
                # giving room for it to be changed at instance level through Dependency injection
                if hasattr(cls, "service"):
                    warnings.warn(
                        "ModelControllerBase.service is deprecated. "
                        "Use ModelControllerBase.service_type instead.",
                        DeprecationWarning,
                        stacklevel=2,
                    )

        compute_api_route_function(cls, self)

        for _, v in self._controller_class_route_functions.items():
            throttled_endpoint = v.as_view.__dict__.get(THROTTLED_FUNCTION)
            if v.route.route_params.throttle is NOT_SET:
                if throttled_endpoint or throttling_objects is not NOT_SET:
                    v.route.route_params.throttle = v.as_view.__dict__.get(
                        THROTTLED_OBJECTS, lambda: throttling_objects
                    )()

            self._add_operation_from_route_function(v)

        if not is_decorated_with_inject(cls.__init__):
            fail_silently(inject, constructor_or_class=cls)

        controller_registry.add_controller(cls)
        return cls

    @property
    def path_operations(self) -> t.Dict[str, PathView]:
        return self._path_operations

    def set_api_instance(self, api: "NinjaExtraAPI") -> None:
        reflect.define_metadata(
            NINJA_EXTRA_API_CONTROLLER_REGISTERED_KEY, {id(api)}, self
        )
        for path_view in self.path_operations.values():
            path_view.set_api_instance(api, t.cast(Router, self))

    def is_registered(self, api: "NinjaExtraAPI") -> bool:
        keys = (
            reflect.get_metadata(NINJA_EXTRA_API_CONTROLLER_REGISTERED_KEY, self)
            or set()
        )
        if id(api) in keys:
            return True
        return False

    def build_routers(self) -> t.List[t.Tuple[str, "APIController"]]:
        prefix = self.prefix
        if self._prefix_has_route_param:
            prefix = ""
        return [(prefix, self)]

    def add_controller_route_function(self, route_function: RouteFunction) -> None:
        self._controller_class_route_functions[
            get_function_name(route_function.route.view_func)
        ] = route_function

    def urls_paths(self, prefix: str) -> t.Iterator[t.Union[URLPattern, URLResolver]]:
        namespaced_patterns: t.List[URLPattern] = []

        for path, path_view in self.path_operations.items():
            path = path.replace("{", "<").replace("}", ">")
            route = "/".join([i for i in (prefix, path) if i])
            # to skip lot of checks we simply treat double slash as a mistake:
            route = normalize_path(route)
            route = route.lstrip("/")

            for op in path_view.operations:
                op = t.cast(Operation, op)
                view = path_view.get_view()
                pattern = django_path(route, view, name=op.url_name)

                if self.urls_namespace:
                    namespaced_patterns.append(pattern)
                else:
                    yield pattern

        if namespaced_patterns and self.urls_namespace:
            yield django_path(
                "",
                include(
                    (namespaced_patterns, self.urls_namespace),
                    namespace=self.urls_namespace,
                ),
            )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<controller - {self.controller_class.__name__}>"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.controller_class.__name__}"

    def _add_operation_from_route_function(self, route_function: RouteFunction) -> None:
        # converts route functions to Operation model
        if route_function.route.route_params.operation_id is None:
            controller_name = (
                str(self.controller_class.__name__).lower().replace("controller", "")
            )
            route_function.route.route_params.operation_id = (
                f"{controller_name}_{route_function.route.view_func.__name__}"
            )
            if self.use_unique_op_id:
                route_function.route.route_params.operation_id += (
                    f"_{uuid.uuid4().hex[:8]}"
                )

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
        data = route_function.route.route_params.dict()
        if not data.get("url_name"):
            data["url_name"] = get_function_name(route_function.route.view_func)
        route_function.operation = self.add_api_operation(
            view_func=route_function.as_view, **data
        )

    def add_api_operation(
        self,
        path: str,
        methods: t.List[str],
        view_func: t.Callable,
        *,
        auth: t.Any = NOT_SET,
        throttle: t.Union[BaseThrottle, t.List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
        response: t.Any = NOT_SET,
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = None,
        description: t.Optional[str] = None,
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        url_name: t.Optional[str] = None,
        include_in_schema: bool = True,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> Operation:
        auth = self.auth if auth == NOT_SET else auth

        if self._prefix_has_route_param:
            path = normalize_path("/".join([i for i in (self.prefix, path) if i]))
        if path not in self._path_operations:
            path_view = PathView()
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
            throttle=throttle,
        )
        return operation


@t.overload
def api_controller(
    prefix_or_class: t.Union[ControllerClassType, t.Type[T]],
) -> t.Union[t.Type[ControllerBase], t.Type[T]]:  # pragma: no cover
    ...


@t.overload
def api_controller(
    prefix_or_class: str = "",
    auth: t.Any = NOT_SET,
    throttle: t.Union[BaseThrottle, t.List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
    tags: t.Union[t.Optional[t.List[str]], str] = None,
    permissions: t.Optional[t.List[BasePermissionType]] = None,
    auto_import: bool = True,
    urls_namespace: t.Optional[str] = None,
    use_unique_op_id: bool = True,
) -> t.Callable[
    [t.Union[t.Type, t.Type[T]]], t.Union[t.Type[ControllerBase], t.Type[T]]
]:  # pragma: no cover
    ...


def api_controller(
    prefix_or_class: t.Union[str, ControllerClassType] = "",
    auth: t.Any = NOT_SET,
    throttle: t.Union[BaseThrottle, t.List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
    tags: t.Union[t.Optional[t.List[str]], str] = None,
    permissions: t.Optional[t.List[BasePermissionType]] = None,
    auto_import: bool = True,
    urls_namespace: t.Optional[str] = None,
    use_unique_op_id: bool = True,
) -> t.Union[
    ControllerClassType, t.Callable[[ControllerClassType], ControllerClassType]
]:
    if isinstance(prefix_or_class, type):
        return APIController(
            prefix="",
            auth=auth,
            tags=tags,
            permissions=permissions,
            auto_import=auto_import,
            throttle=throttle,
            use_unique_op_id=use_unique_op_id,
            urls_namespace=urls_namespace,
        )(prefix_or_class)

    def _decorator(cls: ControllerClassType) -> ControllerClassType:
        return APIController(
            prefix=str(prefix_or_class),
            auth=auth,
            tags=tags,
            permissions=permissions,
            auto_import=auto_import,
            throttle=throttle,
            use_unique_op_id=use_unique_op_id,
            urls_namespace=urls_namespace,
        )(cls)

    return _decorator

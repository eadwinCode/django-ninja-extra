import inspect
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, Tuple, Type

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from ...dependency_resolver import get_injector

if TYPE_CHECKING:
    from ...controllers import Route, APIController


class RouteFunction(object):
    def __init__(self, route_definition: "Route", controller: Type['APIController']):
        self.route_definition = route_definition
        self.has_request_param = False
        self.api_func = route_definition.view_func
        self.controller = controller
        self.as_view = wraps(route_definition.view_func)(self.get_view_function())
        self._resolve_api_func_signature_(self.as_view)

    def _get_required_api_func_signature(self) -> Tuple:
        skip_parameters = ["self", "request"]
        sig_inspect = inspect.signature(self.api_func)
        sig_parameter = []
        for parameter in sig_inspect.parameters.values():
            if parameter.name not in skip_parameters:
                sig_parameter.append(parameter)
            if parameter.name == "request":
                self.has_request_param = True
        return sig_inspect, sig_parameter

    def _resolve_api_func_signature_(self, context_func: Callable) -> Callable:
        # Override signature
        sig_inspect, sig_parameter = self._get_required_api_func_signature()
        sig_replaced = sig_inspect.replace(parameters=sig_parameter)
        context_func.__signature__ = sig_replaced  # type: ignore
        return context_func

    def get_view_function(self) -> Callable:
        def as_view(
            request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
        ) -> Any:
            controller_instance = self._get_controller_instance(
                request, *args, **kwargs
            )
            controller_instance.check_permissions()
            api_func_kwargs = dict(**kwargs)

            if self.has_request_param:
                api_func_kwargs.update(request=request)
            return self.api_func(controller_instance, *args, **api_func_kwargs)

        return as_view

    def _get_controller_instance(
        self, request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> "APIController":

        injector = get_injector()
        init_kwargs = self._get_controller_init_kwargs(request, *args, **kwargs)
        controller_instance: "APIController" = injector.create_object(self.controller)

        for k, v in init_kwargs.items():
            if hasattr(controller_instance, k):
                setattr(controller_instance, k, v)
        return controller_instance

    def _get_controller_init_kwargs(
        self, request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.controller:
            raise ImproperlyConfigured("Controller object is required")

        return dict(
            permission_classes=self.route_definition.permissions
            or self.controller.permission_classes,
            request=request,
            kwargs=kwargs,
            args=args,
        )

    def __str__(self) -> str:
        return self.route_definition.route_params.path

    def __repr__(self) -> str:
        return f"<RouteFunction, controller: {self.controller.__name__} path: {self.__str__()}>"


class AsyncRouteFunction(RouteFunction):
    def get_view_function(self) -> Callable:
        async def as_view(
            request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
        ) -> Any:
            controller_instance = self._get_controller_instance(request, *args, **kwargs)
            controller_instance.check_permissions()

            api_func_kwargs = dict(**kwargs)
            if self.has_request_param:
                api_func_kwargs.update(request=request)
            return await self.api_func(controller_instance, *args, **api_func_kwargs)
        return as_view

    def __repr__(self) -> str:
        return f"<AsyncRouteFunction, controller: {self.controller.__name__} path: {self.__str__()}>"

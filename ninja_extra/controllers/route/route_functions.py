import inspect
from functools import wraps
from typing import TYPE_CHECKING, Tuple, Any, Dict

from django.http import HttpRequest
from django.http.response import HttpResponseBase
from ninja.types import TCallable
from ninja_extra.dependency_resolver import get_injector
from pydantic import ConfigError

if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIController
    from ninja_extra.controllers.route import Route


class RouteFunction(object):
    controller: "APIController" = None
    as_view: TCallable

    def __init__(self, route_definition: "Route", api_func: TCallable):
        self.route_definition = route_definition
        self.has_request_param = False
        self.api_func = api_func
        self.as_view = wraps(api_func)(self.get_view_function())
        self._resolve_api_func_signature_(self.as_view)

    def _get_required_api_func_signature(self):
        skip_parameters = ["self", "request"]
        sig_inspect = inspect.signature(self.api_func)
        sig_parameter = []
        for parameter in sig_inspect.parameters.values():
            if parameter.name not in skip_parameters:
                sig_parameter.append(parameter)
            if parameter.name == "request":
                self.has_request_param = True
        return sig_inspect, sig_parameter

    def _resolve_api_func_signature_(self, context_func):
        # Override signature
        sig_inspect, sig_parameter = self._get_required_api_func_signature()
        sig_replaced = sig_inspect.replace(parameters=sig_parameter)
        context_func.__signature__ = sig_replaced
        return context_func

    @classmethod
    def from_route(
        cls, api_func: TCallable, route_definition: "Route"
    ) -> "RouteFunction":
        route_function = cls(route_definition=route_definition, api_func=api_func)
        return route_function

    def get_view_function(self) -> TCallable:
        def as_view(
            request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
        ) -> HttpResponseBase:
            controller_instance = self._get_controller_instance(
                request, *args, **kwargs
            )
            controller_instance.check_permissions()
            api_func_kwargs = kwargs.copy()

            if self.has_request_param:
                api_func_kwargs.update(request=request)
            return self.api_func(controller_instance, *args, **api_func_kwargs)

        return as_view

    def _get_controller_instance(
        self, request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> "APIController":

        injector = get_injector()
        init_kwargs = self._get_controller_init_kwargs(request, *args, **kwargs)
        controller_instance = injector.create_object(self.controller)

        for k, v in init_kwargs.items():
            if hasattr(controller_instance, k):
                setattr(controller_instance, k, v)
        return controller_instance

    def _get_controller_init_kwargs(
        self, request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.controller:
            raise ConfigError("Controller object is required")

        return dict(
            permission_classes=self.route_definition.permissions
            or self.controller.permission_classes,
            request=request,
            kwargs=kwargs,
            args=args,
        )

    def __str__(self):
        return self.route_definition.route_params.path

    def __repr__(self):
        return f"<RouteFunction, controller: {self.controller.__name__} path: {self.__str__()}>"


class AsyncRouteFunction(RouteFunction):
    async def as_view(
        self, request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> HttpResponseBase:
        controller_instance = self._get_controller_instance(request, *args, **kwargs)
        controller_instance.check_permissions()

        api_func_kwargs = kwargs.copy()
        if self.has_request_param:
            api_func_kwargs.update(request=request)
        return await self.api_func(controller_instance, *args, **api_func_kwargs)

    def __repr__(self):
        return f"<AsyncRouteFunction, controller: {self.controller.__name__} path: {self.__str__()}>"

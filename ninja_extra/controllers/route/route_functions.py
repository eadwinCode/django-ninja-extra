import inspect
from functools import wraps
from typing import TYPE_CHECKING, Tuple, Any, Dict

from django.http import HttpRequest
from django.http.response import HttpResponseBase
from ninja.signature import is_async
from ninja.types import TCallable
from ninja_extra.dependency_resolver import resolve_container_services

if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIController
    from ninja_extra.controllers.route import Route


__all__ = ["RouteFunction"]


class RouteFunction:
    controller: "APIController" = None

    def __init__(self, route_definition: "Route"):
        self.route_definition = route_definition
        self.has_request_param = False

    def _get_required_api_func_signature(self, api_func: TCallable):
        skip_parameters = ['self', 'request']
        sig_inspect = inspect.signature(api_func)
        sig_parameter = []
        for parameter in sig_inspect.parameters.values():
            if parameter.name not in skip_parameters:
                sig_parameter.append(parameter)
            if parameter.name == 'request':
                self.has_request_param = True
        return sig_inspect, sig_parameter

    def _resolve_api_func_signature_(self, api_func, context_func):
        # Override signature
        sig_inspect, sig_parameter = self._get_required_api_func_signature(api_func)
        sig_replaced = sig_inspect.replace(parameters=sig_parameter)
        context_func.__signature__ = sig_replaced
        return context_func

    @classmethod
    def from_route(cls, api_func: TCallable, route_definition: "Route") -> Tuple[TCallable, "RouteFunction"]:
        route_function = cls(route_definition=route_definition)
        if is_async(api_func):
            return route_function.convert_async_api_func_to_context_view(api_func=api_func), route_function
        return route_function.convert_api_func_to_context_view(api_func=api_func), route_function

    def convert_api_func_to_context_view(self, api_func: TCallable) -> TCallable:
        @wraps(api_func)
        def context_func(
                request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
        ) -> HttpResponseBase:
            controller_instance = self._get_controller_instance(request, *args, **kwargs)
            controller_instance.check_permissions()
            api_func_kwargs = kwargs.copy()

            if self.has_request_param:
                api_func_kwargs.update(request=request)
            return api_func(controller_instance, *args, **api_func_kwargs)

        return self._resolve_api_func_signature_(api_func, context_func)

    def convert_async_api_func_to_context_view(
            self, api_func: TCallable
    ) -> TCallable:
        @wraps(api_func)
        async def context_func(
                request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
        ) -> HttpResponseBase:
            controller_instance = self._get_controller_instance(request, *args, **kwargs)
            controller_instance.check_permissions()

            api_func_kwargs = kwargs.copy()
            if self.has_request_param:
                api_func_kwargs.update(request=request)
            return await api_func(controller_instance, *args, **api_func_kwargs)

        return self._resolve_api_func_signature_(api_func, context_func)

    def _get_controller_instance(
            self, request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> "APIController":
        controller_instance = resolve_container_services(self.controller)
        init_kwargs = self._get_controller_init_kwargs(request, *args, **kwargs)

        for k, v in init_kwargs.items():
            if hasattr(controller_instance, k):
                setattr(controller_instance, k, v)
        return controller_instance

    def _get_controller_init_kwargs(
            self, request: HttpRequest, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        return dict(
            permission_classes=self.route_definition.permissions,
            request=request, kwargs=kwargs, args=args
        )

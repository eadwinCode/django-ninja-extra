import inspect
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional, Tuple, Type

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from ninja_extra.controllers.response import ControllerResponse

from ...dependency_resolver import get_injector
from .context import RouteContext

if TYPE_CHECKING:
    from ...controllers import APIController, Route


class RouteFunctionContext:
    def __init__(
        self, controller_instance: "APIController", **view_func_kwargs: Any
    ) -> None:
        self.controller_instance = controller_instance
        self.view_func_kwargs = view_func_kwargs


class RouteFunction(object):
    def __init__(
        self, route: "Route", controller: Optional[Type["APIController"]] = None
    ):
        self.route = route
        self.has_request_param = False
        self.controller: Optional[Type["APIController"]] = controller
        self.as_view = wraps(route.view_func)(self.get_view_function())
        self._resolve_api_func_signature_(self.as_view)

    def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        context = self.get_route_execution_context(request, *args, **kwargs)
        return self.as_view(*args, context=context, **kwargs)

    def _get_required_api_func_signature(self) -> Tuple:
        skip_parameters = ["self", "request"]
        sig_inspect = inspect.signature(self.route.view_func)
        sig_parameter = []
        for parameter in sig_inspect.parameters.values():
            if parameter.name not in skip_parameters:
                sig_parameter.append(parameter)
            elif parameter.name == "request":
                self.has_request_param = True
        return sig_inspect, sig_parameter

    def _resolve_api_func_signature_(self, context_func: Callable) -> Callable:
        # Override signature
        sig_inspect, sig_parameter = self._get_required_api_func_signature()
        sig_replaced = sig_inspect.replace(parameters=sig_parameter)
        context_func.__signature__ = sig_replaced  # type: ignore
        return context_func

    def get_view_function(self) -> Callable:
        def as_view(context: RouteContext, *args: Any, **kwargs: Any) -> Any:
            with self._prep_controller_route_execution(context, **kwargs) as ctx:
                ctx.controller_instance.check_permissions()
                result = self.route.view_func(
                    ctx.controller_instance, *args, **ctx.view_func_kwargs
                )
            return self._process_view_function_result(result)

        as_view.get_route_function = lambda: self  # type:ignore
        return as_view

    def _process_view_function_result(self, result: Any) -> Any:
        """
        This process any an returned value from view_func
        and creates an api response if result is ControllerResponseSchema
        """

        if result and isinstance(result, ControllerResponse):
            return result.status_code, result.convert_to_schema()
        return result

    def _get_controller_instance(self) -> "APIController":
        injector = get_injector()
        assert self.controller

        controller_instance: "APIController" = injector.create_object(self.controller)
        return controller_instance

    def get_route_execution_context(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> RouteContext:

        if not self.controller:
            raise ImproperlyConfigured("Controller object is required")

        init_kwargs = dict(
            permission_classes=self.route.permissions
            or self.controller.permission_classes,
            request=request,
            kwargs=kwargs,
            args=args,
        )
        context = RouteContext(**init_kwargs)
        return context

    @contextmanager
    def _prep_controller_route_execution(
        self, context: RouteContext, **kwargs: Any
    ) -> Iterator[RouteFunctionContext]:
        controller_instance = self._get_controller_instance()
        controller_instance.context = context

        api_func_kwargs = dict(**kwargs)
        if self.has_request_param:
            api_func_kwargs.update(request=context.request)
        try:
            yield RouteFunctionContext(
                controller_instance=controller_instance, **api_func_kwargs
            )
        except Exception as ex:
            raise ex
        finally:
            controller_instance.context = None

    def __str__(self) -> str:
        return self.route.route_params.path

    def __repr__(self) -> str:
        if not self.controller:
            return f"<RouteFunction, controller: No Controller Found, path: {self.__str__()}>"
        return f"<RouteFunction, controller: {self.controller.__name__}, path: {self.__str__()}>"


class AsyncRouteFunction(RouteFunction):
    def get_view_function(self) -> Callable:
        async def as_view(context: RouteContext, *args: Any, **kwargs: Any) -> Any:
            with self._prep_controller_route_execution(context, **kwargs) as ctx:
                ctx.controller_instance.check_permissions()
                result = await self.route.view_func(
                    ctx.controller_instance, *args, **ctx.view_func_kwargs
                )
            return self._process_view_function_result(result)

        as_view.get_route_function = lambda: self  # type:ignore
        return as_view

    def __repr__(self) -> str:
        if not self.controller:
            return f"<AsyncRouteFunction, controller: No Controller Found, path: {self.__str__()}>"
        return f"<AsyncRouteFunction, controller: {self.controller.__name__}, path: {self.__str__()}>"

    async def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        context = self.get_route_execution_context(request, *args, **kwargs)
        return await self.as_view(*args, context=context, **kwargs)

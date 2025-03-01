import inspect
import warnings
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional, Tuple, cast

from django.http import HttpRequest, HttpResponse

from ninja_extra.context import (
    RouteContext,
    get_route_execution_context,
)
from ninja_extra.dependency_resolver import get_injector, service_resolver

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers.base import APIController, ControllerBase
    from ninja_extra.controllers.route import Route
    from ninja_extra.operation import Operation


class RouteFunctionContext:
    def __init__(
        self, controller_instance: "ControllerBase", **view_func_kwargs: Any
    ) -> None:
        self.controller_instance = controller_instance
        self.view_func_kwargs = view_func_kwargs


class RouteFunction(object):
    def __init__(
        self, route: "Route", api_controller: Optional["APIController"] = None
    ):
        self.route = route
        self.operation: Optional["Operation"] = None
        self.has_request_param = False
        self.api_controller = api_controller
        self.as_view = wraps(route.view_func)(self.get_view_function())
        self._resolve_api_func_signature_(self.as_view)

    def __call__(
        self,
        request: HttpRequest,
        temporal_response: Optional[HttpResponse] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        _api_controller = self.get_api_controller()
        context = get_route_execution_context(
            request,
            temporal_response,
            self.route.permissions or _api_controller.permission_classes,  # type: ignore[arg-type]
            *args,
            **kwargs,
        )
        self.run_permission_check(context)
        return self.as_view(request, *args, route_context=context, **kwargs)

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

    def get_api_controller(self) -> "APIController":
        assert self.api_controller, "APIController is required"
        return self.api_controller

    def _resolve_api_func_signature_(self, context_func: Callable) -> Callable:
        # Override signature
        sig_inspect, sig_parameter = self._get_required_api_func_signature()
        sig_replaced = sig_inspect.replace(parameters=sig_parameter)
        context_func.__signature__ = sig_replaced  # type: ignore
        return context_func

    def run_permission_check(self, route_context: RouteContext) -> None:
        _route_context = route_context or cast(
            RouteContext, service_resolver(RouteContext)
        )
        with self._prep_controller_route_execution(_route_context) as ctx:
            ctx.controller_instance.check_permissions()

    def get_view_function(self) -> Callable:
        def as_view(
            request: HttpRequest,
            route_context: Optional[RouteContext] = None,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            _route_context = route_context or cast(
                RouteContext, service_resolver(RouteContext)
            )
            with self._prep_controller_route_execution(_route_context, **kwargs) as ctx:
                # ctx.controller_instance.check_permissions()
                result = self.route.view_func(
                    ctx.controller_instance, *args, **ctx.view_func_kwargs
                )
            return result

        as_view.get_route_function = lambda: self  # type:ignore
        return as_view

    def _process_view_function_result(self, result: Any) -> Any:
        """
        This process any a returned value from view_func
        and creates an api response if a result is ControllerResponseSchema

        deprecated:: 0.21.5
           This method is deprecated and will be removed in a future version.
           The result processing should be handled by the response handlers.
        """
        warnings.warn(
            "_process_view_function_result() is deprecated and will be removed in a future version. "
            "The result processing should be handled by the response handlers.",
            DeprecationWarning,
            stacklevel=2,
        )
        return result

    def _get_controller_instance(self) -> "ControllerBase":
        from ninja_extra.controllers.base import ModelControllerBase

        injector = get_injector()
        _api_controller = self.get_api_controller()
        additional_kwargs = {}

        if issubclass(_api_controller.controller_class, ModelControllerBase):
            controller_klass = cast(
                ModelControllerBase, _api_controller.controller_class
            )
            # make sure model_config is not None
            if controller_klass.model_config is not None:
                service = injector.create_object(
                    controller_klass.service_type,
                    additional_kwargs={"model": controller_klass.model_config.model},
                )
                additional_kwargs.update({"service": service})

        controller_instance = injector.create_object(
            _api_controller.controller_class, additional_kwargs=additional_kwargs
        )

        return controller_instance

    def get_route_execution_context(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> RouteContext:
        warnings.warn(
            "get_route_execution_context() is deprecated in favor of "
            "ninja_extra.controllers.route.context.get_route_execution_context()",
            DeprecationWarning,
            stacklevel=2,
        )
        _api_controller = self.get_api_controller()

        init_kwargs = {
            "permission_classes": self.route.permissions
            or _api_controller.permission_classes,
            "request": request,
            "kwargs": kwargs,
            "args": args,
        }
        context = RouteContext(**init_kwargs)  # type:ignore[arg-type]
        return context

    @contextmanager
    def _prep_controller_route_execution(
        self, route_context: RouteContext, **kwargs: Any
    ) -> Iterator[RouteFunctionContext]:
        controller_instance = self._get_controller_instance()
        controller_instance.context = route_context

        api_func_kwargs = dict(kwargs)
        if self.has_request_param:
            api_func_kwargs.update(request=route_context.request)
        try:
            yield RouteFunctionContext(
                controller_instance=controller_instance, **api_func_kwargs
            )
        except Exception as ex:
            raise ex
        finally:
            controller_instance.context = None

    def __str__(self) -> str:  # pragma: no cover
        return self.route.route_params.path

    def __repr__(self) -> str:  # pragma: no cover
        if not self.api_controller:
            return f"<RouteFunction, controller: No Controller Found, path: {self.__str__()}>"
        return f"<RouteFunction, controller: {self.api_controller.controller_class.__name__}, path: {self.__str__()}>"


class AsyncRouteFunction(RouteFunction):
    async def async_run_check_permissions(self, route_context: RouteContext) -> None:
        from asgiref.sync import sync_to_async

        await sync_to_async(self.run_permission_check)(route_context)

    def get_view_function(self) -> Callable:
        async def as_view(
            request: HttpRequest,
            route_context: Optional[RouteContext] = None,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            _route_context = route_context or cast(
                RouteContext, service_resolver(RouteContext)
            )
            with self._prep_controller_route_execution(_route_context, **kwargs) as ctx:
                # await sync_to_async(ctx.controller_instance.check_permissions)()
                result = await self.route.view_func(
                    ctx.controller_instance, *args, **ctx.view_func_kwargs
                )
            return result

        as_view.get_route_function = lambda: self  # type:ignore
        return as_view

    def __repr__(self) -> str:  # pragma: no cover
        if not self.api_controller:
            return f"<AsyncRouteFunction, controller: No Controller Found, path: {self.__str__()}>"
        return f"<AsyncRouteFunction, controller: {self.api_controller.controller_class.__name__}, path: {self.__str__()}>"

    async def __call__(
        self,
        request: HttpRequest,
        temporal_response: Optional[HttpResponse] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        _api_controller = self.get_api_controller()
        context = get_route_execution_context(
            request,
            temporal_response,
            self.route.permissions or _api_controller.permission_classes,  # type:ignore[arg-type]
            *args,
            **kwargs,
        )
        await self.async_run_check_permissions(context)
        return await self.as_view(request, *args, route_context=context, **kwargs)

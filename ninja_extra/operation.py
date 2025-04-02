import inspect
import time
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.utils.encoding import force_str
from ninja.constants import NOT_SET, NOT_SET_TYPE
from ninja.errors import AuthenticationError
from ninja.operation import (
    AsyncOperation as NinjaAsyncOperation,
)
from ninja.operation import (
    Operation as NinjaOperation,
)
from ninja.operation import (
    PathView as NinjaPathView,
)
from ninja.signature import is_async
from ninja.throttling import BaseThrottle
from ninja.types import TCallable
from ninja.utils import check_csrf

from ninja_extra.compatible import asynccontextmanager
from ninja_extra.constants import ROUTE_CONTEXT_VAR
from ninja_extra.context import RouteContext, get_route_execution_context
from ninja_extra.exceptions import APIException, Throttled
from ninja_extra.helper import get_function_name
from ninja_extra.logger import request_logger

# from ninja_extra.signals import route_context_finished, route_context_started
from ninja_extra.types import PermissionType

from .details import ViewSignature

if TYPE_CHECKING:  # pragma: no cover
    from .controllers.route.route_functions import AsyncRouteFunction, RouteFunction


class Operation(NinjaOperation):
    view_func: Callable

    def __init__(
        self,
        path: str,
        methods: List[str],
        view_func: Callable,
        *,
        url_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.is_coroutine = is_async(view_func)
        self.url_name = url_name  # type: ignore[assignment]
        super().__init__(path, methods, view_func, **kwargs)
        self.signature = ViewSignature(self.path, self.view_func)

    def _set_auth(
        self, auth: Optional[Union[Sequence[Callable], Callable, object]]
    ) -> None:
        if auth is not None and auth is not NOT_SET:
            self.auth_callbacks = isinstance(auth, Sequence) and auth or [auth]
            for callback in self.auth_callbacks:
                _call_back = (
                    callback if inspect.isfunction(callback) else callback.__call__  # type: ignore
                )

                if not getattr(callback, "is_coroutine", None):
                    callback.is_coroutine = is_async(  # type:ignore[union-attr]
                        _call_back
                    )

                if is_async(_call_back) and not self.is_coroutine:
                    raise Exception(
                        f"Could apply auth=`{get_function_name(callback)}` "
                        f"to view_func=`{get_function_name(self.view_func)}`.\n"
                        f"N:B - {get_function_name(callback)} can only be used on Asynchronous view functions"
                    )

    def _get_route_function(
        self,
    ) -> Optional[Union["RouteFunction", "AsyncRouteFunction"]]:
        if hasattr(self.view_func, "get_route_function"):
            return cast(
                Union["RouteFunction", "AsyncRouteFunction"],
                self.view_func.get_route_function(),
            )
        return None

    def _log_action(
        self,
        logger: Callable[..., Any],
        request: HttpRequest,
        duration: Optional[float] = None,
        ex: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        try:
            msg = (
                f'"{request.method.upper() if request.method else "METHOD NOT FOUND"} - '
                f'{self.view_func.__name__} {request.path}" '
                f"{duration if duration else ''}"
            )
            route_function = self._get_route_function()
            if route_function:
                api_controller = route_function.get_api_controller()

                msg = (
                    f'"{request.method.upper() if request.method else "METHOD NOT FOUND"} - '
                    f'{api_controller.controller_class.__name__}[{self.view_func.__name__}] {request.path}" '
                    f"{duration if duration else ''}"
                )
            if ex:
                msg += (
                    f"{ex.status_code}"
                    if isinstance(ex, APIException)
                    else f"{force_str(ex.args)}"
                )

            logger(msg, **kwargs)
        except Exception as log_ex:
            request_logger.debug(log_ex)

    def get_execution_context(
        self,
        request: HttpRequest,
        temporal_response: HttpResponse,
        *args: Any,
        **kwargs: Any,
    ) -> RouteContext:
        permission_classes: PermissionType = []
        if hasattr(self.view_func, "get_route_function"):
            route_function: "RouteFunction" = self.view_func.get_route_function()

            _api_controller = route_function.get_api_controller()
            permission_classes = (
                route_function.route.permissions or _api_controller.permission_classes  # type: ignore[assignment]
            )

        return get_route_execution_context(
            request,
            temporal_response,
            permission_classes,
            *args,
            **kwargs,
        )

    @contextmanager
    def _prep_run(
        self, request: HttpRequest, temporal_response: HttpResponse, **kw: Any
    ) -> Iterator[RouteContext]:
        try:
            start_time = time.time()
            context = self.get_execution_context(
                request, temporal_response=temporal_response, **kw
            )
            # send route_context_started signal
            ROUTE_CONTEXT_VAR.set(context)

            yield context
            self._log_action(
                request_logger.info,
                request=request,
                duration=time.time() - start_time,
                extra={"request": request},
                exc_info=None,
            )
        except Exception as e:
            self._log_action(
                request_logger.warning,
                request=request,
                ex=e,
                extra={"request": request},
                exc_info=None,
            )
            raise e
        finally:
            # send route_context_finished signal
            ROUTE_CONTEXT_VAR.set(None)

    def run(self, request: HttpRequest, **kw: Any) -> HttpResponseBase:
        try:
            with self._prep_run(
                request,
                temporal_response=self.api.create_temporal_response(request),
                api=self.api,
                view_signature=self.signature,
                **kw,
            ) as ctx:
                error = self._run_checks(request)
                if error:
                    return error

                route_function = self._get_route_function()
                if route_function:
                    route_function.run_permission_check(ctx)

                if not ctx.has_computed_route_parameters:
                    ctx.compute_route_parameters()

                result = self.view_func(request, **ctx.kwargs["view_func_kwargs"])
                assert ctx.response is not None
                _processed_results = self._result_to_response(
                    request, result, ctx.response
                )

                return _processed_results
        except Exception as e:
            if isinstance(e, TypeError) and "required positional argument" in str(
                e
            ):  # pragma: no cover
                msg = "Did you fail to use functools.wraps() in a decorator?"
                msg = f"{e.args[0]}: {msg}" if e.args else msg
                e.args = (msg,) + e.args[1:]
            return self.api.on_exception(request, e)

    def _check_throttles(self, request: HttpRequest) -> Optional[HttpResponse]:
        throttle_durations = []
        for throttle in self.throttle_objects:
            if not throttle.allow_request(request):
                throttle_durations.append(throttle.wait())

        if throttle_durations:
            # Filter out `None` values which may happen in case of config / rate
            durations = [
                duration for duration in throttle_durations if duration is not None
            ]

            duration = max(durations, default=None)
            raise Throttled(wait=duration)
        return None


class AsyncOperation(Operation, NinjaAsyncOperation):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        from asgiref.sync import sync_to_async

        self._get_values = cast(Callable, sync_to_async(super()._get_values))  # type: ignore
        self._result_to_response = cast(  # type: ignore
            Callable,
            sync_to_async(super()._result_to_response),
        )

    async def _run_checks(self, request: HttpRequest) -> Optional[HttpResponse]:  # type: ignore
        """Runs security checks for each operation"""
        # csrf:
        if self.api.csrf:
            error = check_csrf(request, self.view_func)
            if error:
                return error

        # auth:
        if self.auth_callbacks:
            error = await self._run_authentication(request)  # type: ignore[assignment]
            if error:
                return error

        # Throttling:
        if self.throttle_objects:
            error = self._check_throttles(request)  # type: ignore
            if error:
                return error

        return None

    async def _run_authentication(self, request: HttpRequest) -> Optional[HttpResponse]:  # type: ignore
        for callback in self.auth_callbacks:
            try:
                is_coroutine = getattr(callback, "is_coroutine", False)
                if is_coroutine:
                    result = await callback(request)
                else:
                    result = callback(request)
            except Exception as exc:
                return self.api.on_exception(request, exc)

            if result:
                request.auth = result  # type: ignore
                return None

        return self.api.on_exception(request, AuthenticationError())

    @asynccontextmanager
    async def _prep_run(  # type:ignore
        self, request: HttpRequest, **kw: Any
    ) -> AsyncIterator[RouteContext]:
        try:
            start_time = time.time()
            context = self.get_execution_context(request, **kw)
            # send route_context_started signal
            ROUTE_CONTEXT_VAR.set(context)

            yield context
            self._log_action(
                request_logger.info,
                request=request,
                duration=time.time() - start_time,
                extra={"request": request},
                exc_info=None,
            )
        except Exception as e:
            self._log_action(
                request_logger.warning,
                request=request,
                ex=e,
                extra={"request": request},
                exc_info=None,
            )
            raise e
        finally:
            # send route_context_finished signal
            ROUTE_CONTEXT_VAR.set(None)

    async def run(self, request: HttpRequest, **kw: Any) -> HttpResponseBase:  # type: ignore
        try:
            async with self._prep_run(
                request,
                temporal_response=self.api.create_temporal_response(request),
                api=self.api,
                view_signature=self.signature,
                **kw,
            ) as ctx:
                error = await self._run_checks(request)
                if error:
                    return error

                route_function = self._get_route_function()
                if route_function:
                    await route_function.async_run_check_permissions(ctx)  # type: ignore[attr-defined]

                if not ctx.has_computed_route_parameters:
                    ctx.compute_route_parameters()

                result = await self.view_func(request, **ctx.kwargs["view_func_kwargs"])
                assert ctx.response is not None
                _processed_results = await self._result_to_response(
                    request, result, ctx.response
                )

                return cast(HttpResponseBase, _processed_results)
        except Exception as e:
            return self.api.on_exception(request, e)


class PathView(NinjaPathView):
    async def _async_view(  # type: ignore
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponseBase:
        return await super(PathView, self)._async_view(request, *args, **kwargs)

    def _sync_view(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:  # type: ignore
        return super(PathView, self)._sync_view(request, *args, **kwargs)

    def add_operation(
        self,
        path: str,
        methods: List[str],
        view_func: Callable,
        *,
        auth: Optional[Union[Sequence[Callable], Callable, object]] = NOT_SET,
        throttle: Union[BaseThrottle, List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
        response: Any = NOT_SET,
        operation_id: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        deprecated: Optional[bool] = None,
        by_alias: Optional[bool] = None,
        exclude_unset: Optional[bool] = None,
        exclude_defaults: Optional[bool] = None,
        exclude_none: Optional[bool] = None,
        url_name: Optional[str] = None,
        include_in_schema: bool = True,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Operation:
        if url_name:
            self.url_name = url_name
        operation_class = self.get_operation_class(view_func)
        operation = operation_class(
            path,
            methods,
            view_func,
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
            include_in_schema=include_in_schema,
            url_name=url_name,
            openapi_extra=openapi_extra,
            throttle=throttle,
        )

        self.operations.append(operation)
        return operation

    def get_operation_class(
        self, view_func: TCallable
    ) -> Type[Union[Operation, AsyncOperation]]:
        operation_class = Operation
        if is_async(view_func):
            self.is_async = True
            operation_class = AsyncOperation
        return operation_class

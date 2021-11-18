import time
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    List,
    Optional,
    Sequence,
    Union,
)

from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.utils.encoding import force_str
from ninja.constants import NOT_SET
from ninja.operation import (
    AsyncOperation as NinjaAsyncOperation,
    Operation as NinjaOperation,
    PathView as NinjaPathView,
)
from ninja.signature import is_async

from ninja_extra.exceptions import APIException
from ninja_extra.logger import request_logger
from ninja_extra.signals import route_context_finished, route_context_started

from .controllers.route.context import RouteContext

if TYPE_CHECKING:
    from .controllers import RouteFunction


class Operation(NinjaOperation):
    def _log_action(
        self,
        logger: Callable[..., Any],
        request: HttpRequest,
        duration: Optional[float] = None,
        ex: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        try:
            route_function: "RouteFunction" = (
                self.view_func.get_route_function()  # type:ignore
            )
            assert route_function.controller
            msg = (
                f'"{request.method.upper() if request.method else "METHOD NOT FOUND"} - '
                f'{route_function.controller.__name__}[{self.view_func.__name__}] {request.path}" '
                f"{duration if duration else ''}"
            )
            if ex:
                msg += (
                    f"{ex.status_code}"
                    if isinstance(ex, APIException)
                    else f"{force_str(ex.args)}"
                )

            logger(msg, **kwargs)
        except (Exception,) as dd:
            print(dd)

    def get_execution_context(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> RouteContext:
        route_function: "RouteFunction" = (
            self.view_func.get_route_function()  # type:ignore
        )

        if not route_function:
            raise Exception("Route Function is found missing")

        if route_function and not hasattr(
            route_function, "get_route_execution_context"
        ):
            raise Exception("Invalid Route Function")

        return route_function.get_route_execution_context(request, *args, **kwargs)

    @contextmanager
    def _prep_run(self, request: HttpRequest, **kw: Any) -> Iterator:
        try:
            start_time = time.time()
            values = self._get_values(request, kw)
            context = self.get_execution_context(request, **values)
            # send route_context_started signal
            route_context_started.send(RouteContext, route_context=context)

            yield values, context
            self._log_action(
                request_logger.info,
                request=request,
                duration=time.time() - start_time,
                extra=dict(request=request),
                exc_info=None,
            )
        except Exception as e:
            self._log_action(
                request_logger.error,
                request=request,
                ex=e,
                extra=dict(request=request),
                exc_info=None,
            )
            raise e
        finally:
            # send route_context_finished signal
            route_context_finished.send(RouteContext, route_context=None)

    def run(self, request: HttpRequest, **kw: Any) -> HttpResponseBase:
        error = super(Operation, self)._run_checks(request)
        if error:
            return error
        try:
            with self._prep_run(request, **kw) as ctx:
                values, context = ctx
                result = self.view_func(context=context, **values)
                _processed_results = self._result_to_response(request, result)
            return _processed_results
        except Exception as e:
            if isinstance(e, TypeError) and "required positional argument" in str(e):
                msg = "Did you fail to use functools.wraps() in a decorator?"
                msg = f"{e.args[0]}: {msg}" if e.args else msg
                e.args = (msg,) + e.args[1:]
            return self.api.on_exception(request, e)


class AsyncOperation(Operation, NinjaAsyncOperation):
    async def run(self, request: HttpRequest, **kw: Any) -> HttpResponseBase:  # type: ignore
        error = self._run_checks(request)
        if error:
            return error
        try:
            with self._prep_run(request, **kw) as ctx:
                values, context = ctx
                result = await self.view_func(context=context, **values)
                _processed_results = self._result_to_response(request, result)
            return _processed_results
        except Exception as e:
            return self.api.on_exception(request, e)


class PathView(NinjaPathView):
    async def _async_view(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # type: ignore
        return await super(PathView, self)._async_view(request, *args, **kwargs)

    def _sync_view(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # type: ignore
        return super(PathView, self)._sync_view(request, *args, **kwargs)

    def add_operation(
        self,
        path: str,
        methods: List[str],
        view_func: Callable,
        *,
        auth: Optional[Union[Sequence[Callable], Callable, object]] = NOT_SET,
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
        if url_name:
            self.url_name = url_name

        operation_class = Operation
        if is_async(view_func):
            self.is_async = True
            operation_class = AsyncOperation

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
        )

        self.operations.append(operation)
        return operation

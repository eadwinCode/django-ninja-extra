import inspect
import math
from functools import wraps
from typing import Any, Callable, Optional, Type, Union, cast

from django.http import HttpRequest, HttpResponse
from ninja.constants import NOT_SET
from ninja.signature import is_async

from ninja_extra import exceptions
from ninja_extra.conf import settings
from ninja_extra.controllers import ControllerBase, RouteContext
from ninja_extra.dependency_resolver import service_resolver

from .model import BaseThrottle


def throttle(
    func_or_throttle_class: Any = NOT_SET, **init_kwargs: Any
) -> Callable[..., Any]:
    isfunction = inspect.isfunction(func_or_throttle_class)
    isnotset = func_or_throttle_class == NOT_SET

    throttle_class: Type[BaseThrottle] = settings.THROTTLING_CLASS

    if isfunction:
        return _inject_throttling(func_or_throttle_class, throttle_class, **init_kwargs)

    if not isnotset:
        throttle_class = func_or_throttle_class

    def wrapper(view_func: Callable[..., Any]) -> Any:
        return _inject_throttling(view_func, throttle_class, **init_kwargs)

    return wrapper


def _run_throttles(
    throttle_class: Type[BaseThrottle],
    request_or_controller: Union[HttpRequest, ControllerBase],
    response: HttpResponse = None,
    **init_kwargs: Any,
) -> None:
    """
    Run all throttles for a request.
    Raises an appropriate exception if the request is throttled.
    """

    request = cast(
        HttpRequest,
        (
            request_or_controller.context.request  # type:ignore
            if isinstance(request_or_controller, RouteContext)
            else request_or_controller
        ),
    )

    throttle_durations = []

    throttling: BaseThrottle = throttle_class(**init_kwargs)
    if not throttling.allow_request(request):
        throttle_durations.append(throttling.wait())

    if throttle_durations:
        # Filter out `None` values which may happen in case of config / rate
        durations = [
            duration for duration in throttle_durations if duration is not None
        ]

        duration = max(durations, default=None)
        raise exceptions.Throttled(duration)

    if response:
        response.setdefault("X-Rate-Limit-Limit", str(throttling.num_requests or ""))
        response.setdefault(
            "X-Rate-Limit-Remaining",
            str((throttling.num_requests or 0) - len(throttling.history)),
        )
        response.setdefault(
            "X-Rate-Limit-Reset", str(math.ceil(throttling.wait() or 0))
        )


def _inject_throttling(
    func: Callable[..., Any],
    throttle_class: Type[BaseThrottle],
    **init_kwargs: Any,
) -> Callable[..., Any]:
    if is_async(func):
        return _async_inject_throttling_handler(func, throttle_class, **init_kwargs)
    return _sync_inject_throttling_handler(func, throttle_class, **init_kwargs)


def _sync_inject_throttling_handler(
    func: Callable[..., Any],
    throttle_class: Type[BaseThrottle],
    **init_kwargs: Any,
) -> Callable[..., Any]:
    @wraps(func)
    def as_view(
        request_or_controller: Union[HttpRequest, ControllerBase], *args: Any, **kw: Any
    ) -> Any:
        ctx = cast(Optional[RouteContext], service_resolver(RouteContext))
        _run_throttles(
            throttle_class,
            request_or_controller=request_or_controller,
            response=ctx.response if ctx else None,
            **init_kwargs,
        )

        res = func(request_or_controller, *args, **kw)
        return res

    return as_view


def _async_inject_throttling_handler(
    func: Callable[..., Any],
    throttle_class: Type[BaseThrottle],
    **init_kwargs: Any,
) -> Callable[..., Any]:
    @wraps(func)
    async def as_view(
        request_or_controller: Union[HttpRequest, ControllerBase], *args: Any, **kw: Any
    ) -> Any:
        ctx = cast(Optional[RouteContext], service_resolver(RouteContext))
        _run_throttles(
            throttle_class,
            request_or_controller=request_or_controller,
            response=ctx.response if ctx else None,
            **init_kwargs,
        )

        res = await func(request_or_controller, *args, **kw)
        return res

    return as_view

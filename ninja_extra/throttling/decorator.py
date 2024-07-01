import inspect
from typing import Any, Callable, List, Type, Union

from ninja.throttling import BaseThrottle

from ninja_extra.conf import settings
from ninja_extra.constants import THROTTLED_FUNCTION, THROTTLED_OBJECTS


def throttle(
    *func_or_throttle_klass_or_object: Any, **init_kwargs: Any
) -> Callable[..., Any]:
    isfunction = (
        inspect.isfunction(func_or_throttle_klass_or_object[0])
        if len(func_or_throttle_klass_or_object) == 1
        else False
    )

    if isfunction:
        func = func_or_throttle_klass_or_object[0]
        throttle_classes: List[Type[BaseThrottle]] = settings.THROTTLE_CLASSES
        return _inject_throttling(func, *throttle_classes, **init_kwargs)

    def wrapper(view_func: Callable[..., Any]) -> Any:
        return _inject_throttling(
            view_func, *func_or_throttle_klass_or_object, **init_kwargs
        )

    return wrapper


# def _run_throttles(
#     *throttle_classes: Type[BaseThrottle],
#     request_or_controller: Union[HttpRequest, ControllerBase],
#     response: Optional[HttpResponse] = None,
#     **init_kwargs: Any,
# ) -> None:
#     """
#     Run all throttles for a request.
#     Raises an appropriate exception if the request is throttled.
#     """
#
#     request = cast(
#         HttpRequest,
#         (
#             request_or_controller.context.request  # type:ignore
#             if isinstance(request_or_controller, ControllerBase)
#             else request_or_controller
#         ),
#     )
#
#     throttle_durations = []
#
#     for throttle_class in throttle_classes:
#         throttling: BaseThrottle = throttle_class(**init_kwargs)
#         if not throttling.allow_request(request):
#             # Filter out `None` values which may happen in case of config / rate
#             duration = throttling.wait()
#             if duration is not None:
#                 throttle_durations.append(duration)
#
#     if throttle_durations:
#         duration = max(throttle_durations, default=None)
#         raise exceptions.Throttled(duration)


def _lazy_throttling_objects(
    *throttle_klass_or_object: Union[Type[BaseThrottle], BaseThrottle],
    **init_kwargs: Any,
) -> Callable:
    def _() -> List[BaseThrottle]:
        res = []
        for item in throttle_klass_or_object:
            if isinstance(item, type):
                res.append(item(**init_kwargs))
                continue

            res.append(item)

        return res

    return _


def _inject_throttling(
    func: Callable[..., Any],
    *throttle_classes: Type[BaseThrottle],
    **init_kwargs: Any,
) -> Callable[..., Any]:
    throttling_objects_lazy: Callable = _lazy_throttling_objects(
        *throttle_classes, **init_kwargs
    )
    setattr(func, THROTTLED_FUNCTION, True)
    setattr(func, THROTTLED_OBJECTS, throttling_objects_lazy)

    return func
    # if is_async(func):
    #     return _async_inject_throttling_handler(func, *throttle_classes, **init_kwargs)
    # return _sync_inject_throttling_handler(func, *throttle_classes, **init_kwargs)


# def _sync_inject_throttling_handler(
#     func: Callable[..., Any],
#     *throttle_classes: Type[BaseThrottle],
#     **init_kwargs: Any,
# ) -> Callable[..., Any]:
#     @wraps(func)
#     def as_view(
#         request_or_controller: Union[HttpRequest, ControllerBase], *args: Any, **kw: Any
#     ) -> Any:
#         ctx = cast(Optional[RouteContext], service_resolver(RouteContext))
#         _run_throttles(
#             *throttle_classes,
#             request_or_controller=request_or_controller,
#             response=ctx.response if ctx else None,
#             **init_kwargs,
#         )
#
#         res = func(request_or_controller, *args, **kw)
#         return res
#
#     return as_view
#
#
# def _async_inject_throttling_handler(
#     func: Callable[..., Any],
#     *throttle_classes: Type[BaseThrottle],
#     **init_kwargs: Any,
# ) -> Callable[..., Any]:
#     @wraps(func)
#     async def as_view(
#         request_or_controller: Union[HttpRequest, ControllerBase], *args: Any, **kw: Any
#     ) -> Any:
#         ctx = cast(Optional[RouteContext], service_resolver(RouteContext))
#         _run_throttles(
#             *throttle_classes,
#             request_or_controller=request_or_controller,
#             response=ctx.response if ctx else None,
#             **init_kwargs,
#         )
#
#         res = await func(request_or_controller, *args, **kw)
#         return res
#
#     return as_view

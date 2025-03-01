import inspect
from typing import Any, Callable, List, Type, Union, cast

from ninja.throttling import BaseThrottle

from ninja_extra.constants import THROTTLED_FUNCTION, THROTTLED_OBJECTS
from ninja_extra.lazy import settings_lazy


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
        throttle_classes: List[Type[BaseThrottle]] = cast(
            List[Type[BaseThrottle]], settings_lazy().THROTTLE_CLASSES
        )
        return _inject_throttling(func, *throttle_classes, **init_kwargs)

    def wrapper(view_func: Callable[..., Any]) -> Any:
        return _inject_throttling(
            view_func, *func_or_throttle_klass_or_object, **init_kwargs
        )

    return wrapper


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

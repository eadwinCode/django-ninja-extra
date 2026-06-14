import inspect
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    pass


def get_function_name(func_class: t.Any) -> str:
    if inspect.isfunction(func_class) or inspect.isclass(func_class):
        return str(func_class.__name__)
    return str(func_class.__class__.__name__)


def get_real_view_func(view_func: t.Callable) -> t.Callable:
    """
    Unwrap ninja_extra controller wrappers to retrieve the underlying view function.

    It is essential for features like async streaming (JSONL/SSE), where inspection tools
    such as `inspect.isasyncgenfunction` must evaluate the original `async def ... yield`
    implementation.
    """
    while hasattr(view_func, "__wrapped__"):
        view_func = view_func.__wrapped__
    if hasattr(view_func, "get_route_function"):
        route_function = view_func.get_route_function()
        if hasattr(route_function, "route") and hasattr(
            route_function.route, "view_func"
        ):
            return route_function.route.view_func  # type: ignore[no-any-return]
    return view_func


# TODO: Add deprecation warning
# @t.no_type_check
# def get_route_function(func: t.Callable) -> t.Optional["RouteFunction"]:
#     if hasattr(func, ROUTE_FUNCTION):
#         return func.__dict__[ROUTE_FUNCTION]
#     return None  # pragma: no cover

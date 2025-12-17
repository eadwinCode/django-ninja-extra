import inspect
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    pass


def get_function_name(func_class: t.Any) -> str:
    if inspect.isfunction(func_class) or inspect.isclass(func_class):
        return str(func_class.__name__)
    return str(func_class.__class__.__name__)


# TODO: Add deprecation warning
# @t.no_type_check
# def get_route_function(func: t.Callable) -> t.Optional["RouteFunction"]:
#     if hasattr(func, ROUTE_FUNCTION):
#         return func.__dict__[ROUTE_FUNCTION]
#     return None  # pragma: no cover

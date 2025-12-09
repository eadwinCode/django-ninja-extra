import inspect
import typing as t

from ninja_extra.constants import ROUTE_FUNCTION

if t.TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers import RouteFunction


def get_function_name(func_class: t.Any) -> str:
    if inspect.isfunction(func_class) or inspect.isclass(func_class):
        return str(func_class.__name__)
    return str(func_class.__class__.__name__)


@t.no_type_check
def get_route_function(func: t.Callable) -> t.Optional["RouteFunction"]:
    controller_instance = getattr(func, "__self__", None)

    if controller_instance is not None:
        controller_class = controller_instance.__class__
        api_controller = controller_class.get_api_controller()
        return api_controller._controller_class_route_functions.get(func.__name__)

    # Unbound function – return a clone of the template for introspection
    underlying_func = getattr(func, "__func__", func)
    route_template = getattr(underlying_func, ROUTE_FUNCTION, None)
    if route_template is None:
        return None  # pragma: no cover

    return route_template.clone(underlying_func)

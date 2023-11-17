import inspect
import warnings
from typing import TYPE_CHECKING

from ninja.signature.details import ViewSignature as NinjaViewSignature

if TYPE_CHECKING:  # pragma: no cover
    from .controllers.route.route_functions import RouteFunction


class ViewSignature(NinjaViewSignature):
    def _validate_view_path_params(self) -> None:
        """verify all path params are present in the path model fields"""
        if self.path_params_names:
            path_model = next(
                (m for m in self.models if m.__ninja_param_source__ == "path"), None
            )
            missing = tuple(
                sorted(
                    name
                    for name in self.path_params_names
                    if not (path_model and name in path_model.__ninja_flatten_map__)
                )
            )
            if missing:  # pragma: no cover
                message = f"Field(s) {missing} are in the view path, but were not found in the view signature."
                view_func = self.view_func
                filename = inspect.getfile(view_func)

                if hasattr(self.view_func, "get_route_function"):
                    route_function: "RouteFunction" = (
                        self.view_func.get_route_function()
                    )
                    api_controller = route_function.get_api_controller()

                    view_func = route_function.route.view_func

                    message += f" @ {api_controller.controller_class.__name__}[{self.view_func.__name__}]"
                    filename = inspect.getfile(api_controller.controller_class)

                warnings.warn_explicit(
                    UserWarning(message),
                    category=None,
                    filename=filename,
                    lineno=inspect.getsourcelines(view_func)[1],
                    source=None,
                )

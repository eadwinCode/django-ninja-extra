import typing as t
import warnings

from .base import ControllerBase, ModelControllerBase, api_controller
from .model import (
    ModelAsyncEndpointFactory,
    ModelConfig,
    ModelControllerBuilder,
    ModelEndpointFactory,
    ModelPagination,
    ModelSchemaConfig,
    ModelService,
    ModelServiceBase,
)
from .response import Detail, Id, Ok
from .route import (
    Route,
    RouteInvalidParameterException,
    http_delete,
    http_generic,
    http_get,
    http_patch,
    http_post,
    http_put,
    route,
)
from .route.route_functions import AsyncRouteFunction, RouteFunction

__all__ = [
    "api_controller",
    "route",
    "http_get",
    "http_post",
    "http_put",
    "http_delete",
    "http_patch",
    "http_generic",
    "ControllerBase",
    "RouteInvalidParameterException",
    "AsyncRouteFunction",
    "RouteFunction",
    "Route",
    "Ok",
    "Id",
    "Detail",
    "ModelControllerBase",
    "ModelConfig",
    "ModelService",
    "ModelSchemaConfig",
    "ModelControllerBuilder",
    "ModelPagination",
    "ModelServiceBase",
    "ModelEndpointFactory",
    "ModelAsyncEndpointFactory",
]


def __getattr__(name: str) -> t.Any:
    if name == "RouteContext":
        warnings.warn(
            "RouteContext is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        from ninja_extra.context import RouteContext

        return RouteContext
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

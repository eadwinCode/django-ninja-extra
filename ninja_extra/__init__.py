"""Django Ninja Extra - Class Based Utility and more for Django Ninja(Fast Django REST framework)"""

__version__ = "0.22.8"

import django

from ninja_extra.controllers import (
    ControllerBase,
    ModelAsyncEndpointFactory,
    ModelConfig,
    ModelControllerBase,
    ModelControllerBuilder,
    ModelEndpointFactory,
    ModelPagination,
    ModelSchemaConfig,
    ModelService,
    ModelServiceBase,
    api_controller,
    http_delete,
    http_generic,
    http_get,
    http_patch,
    http_post,
    http_put,
)
from ninja_extra.controllers.route import route
from ninja_extra.dependency_resolver import get_injector, service_resolver
from ninja_extra.main import NinjaExtraAPI
from ninja_extra.pagination import paginate
from ninja_extra.router import Router
from ninja_extra.throttling import throttle

if django.VERSION < (3, 2):  # pragma: no cover
    default_app_config = "ninja_extra.apps.NinjaExtraConfig"


__all__ = [
    "ControllerBase",
    "api_controller",
    "NinjaExtraAPI",
    "route",
    "http_patch",
    "http_get",
    "http_put",
    "http_post",
    "http_delete",
    "http_generic",
    "permissions",
    "exceptions",
    "status",
    "shortcuts",
    "get_injector",
    "service_resolver",
    "lazy",
    "Router",
    "throttle",
    "paginate",
    "ModelControllerBase",
    "ModelConfig",
    "ModelService",
    "ModelSchemaConfig",
    "ModelControllerBuilder",
    "ModelPagination",
    "ModelServiceBase",
    "ModelControllerBase",
    "ModelEndpointFactory",
    "ModelAsyncEndpointFactory",
]

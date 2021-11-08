"""Django Ninja Extra - Class Based Utility and more for Django Ninja(Fast Django REST framework)"""

__version__ = "0.11.8"

from ninja_extra.controllers import APIController
from ninja_extra.controllers.route import route
from ninja_extra.controllers.router import router
from ninja_extra.dependency_resolver import get_injector, service_resolver
from ninja_extra.main import NinjaExtraAPI

default_app_config = "ninja_extra.apps.NinjaExtraConfig"

__all__ = [
    "NinjaExtraAPI",
    "route",
    "APIController",
    "router",
    "permissions",
    "exceptions",
    "status",
    "shortcuts",
    "get_injector",
    "service_resolver",
    "lazy",
]

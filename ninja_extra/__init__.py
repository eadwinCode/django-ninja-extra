"""Django Ninja Extra - Class Based Utility and more for Django Ninja(Fast Django REST framework)"""

__version__ = "0.10.1"


from ninja_extra.main import NinjaExtraAPI
from ninja_extra.controllers import APIController, APIContext
from ninja_extra.controllers.controller_route.route_functions import (
    PaginatedRouteFunction, RetrieveObjectRouteFunction, RouteFunction
)
from ninja_extra.controllers.controller_route.route import route, Route
from ninja_extra.controllers.controller_route.router import router, ControllerRouter

__all__ = [
    'NinjaExtraAPI',
    'APIContext',
    'PaginatedRouteFunction',
    'RetrieveObjectRouteFunction',
    'Route',
    'route',
    'RouteFunction',
    'APIController',
    'router',
    'ControllerRouter'
]

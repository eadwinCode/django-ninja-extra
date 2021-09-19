"""Django Ninja Extra - Class Based Utility and more for Django Ninja(Fast Django REST framework)"""

__version__ = "0.10.1"


from ninja_extra.main import NinjaExtraAPI
from ninja_extra.controllers import APIController
from ninja_extra.controllers.route import route
from ninja_extra.controllers.router import router
from ninja_extra import permissions
from ninja_extra import exceptions
from ninja_extra import status
from ninja_extra import shortcuts
from ninja_extra.dependency_resolver import get_injector, service_resolver

default_app_config = 'ninja_extra.apps.NinjaExtraConfig'

__all__ = [
    'NinjaExtraAPI',
    'route',
    'APIController',
    'router',
    'permissions',
    'exceptions',
    'status',
    'shortcuts',
    'get_injector',
    'service_resolver'
]

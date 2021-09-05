"""Django Ninja Extra - Class Based Utility and more for Django Ninja(Fast Django REST framework)"""

__version__ = "0.10.1"


from ninja_extra.main import NinjaExtraAPI
from ninja_extra.controllers import APIController
from ninja_extra.controllers.route import route
from ninja_extra.controllers.router import router

__all__ = [
    'NinjaExtraAPI',
    'route',
    'APIController',
    'router',
]

from typing import Any, Optional, List, Iterator, Dict, TYPE_CHECKING
from ninja.constants import NOT_SET

from ninja_extra.controllers.route.route_functions import RouteFunction
if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIController

__all__ = ['router', 'ControllerRouter']


class ControllerRouterBorg:
    _shared_state_ = dict(controllers=dict())

    def __init__(self):
        self.__dict__ = self._shared_state_

    def add_controller(self, controller: "APIController"):
        self._shared_state_['controllers'].update(**{str(controller): controller})

    @classmethod
    def get_controllers(cls) -> Dict[str, "APIController"]:
        return cls._shared_state_.get('controllers')


class ControllerRouter(ControllerRouterBorg):
    def __init__(self, prefix, *, auth: Any = NOT_SET, tags: Optional[List[str]] = None, permissions=None):
        ControllerRouterBorg.__init__(self)
        self.prefix = prefix
        self.auth = auth
        self.tags = tags
        self.permission_classes = permissions or []

    def __call__(self, controller: "APIController"):
        controller.prefix = self.prefix
        controller.auth = self.auth
        controller.api = controller.api if hasattr(controller, 'api') else None
        controller.registered = False
        controller.permission_classes = self.permission_classes
        self.add_controller(controller)
        return controller

    @classmethod
    def _get_class_route_functions(cls, controller: "APIController") -> Iterator[RouteFunction]:
        for method in controller.__dict__.values():
            if isinstance(method, RouteFunction):
                yield method


router = ControllerRouter

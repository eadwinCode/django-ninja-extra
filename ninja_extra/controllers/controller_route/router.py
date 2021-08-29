from typing import Any, Optional, List, Iterator, Dict
from ninja.constants import NOT_SET
from ninja_extra.controllers.base import APIController
from ninja_extra.controllers.controller_route.route_functions import RouteFunction

__all__ = ['router', 'ControllerRouter']


class Borg:
    _shared_state_ = dict(controllers=dict())

    def __init__(self):
        self.__dict__ = self._shared_state_

    def add_controller(self, controller: APIController):
        self._shared_state_['controllers'].update(**{str(controller): controller})

    @classmethod
    def get_controllers(cls) -> Dict[str, APIController]:
        return cls._shared_state_.get('controllers')


class ControllerRouter(Borg):
    def __init__(self, prefix, *, auth: Any = NOT_SET, tags: Optional[List[str]] = None):
        Borg.__init__(self)
        self.prefix = prefix
        self.auth = auth
        self.tags = tags

    def __call__(self, controller: APIController, *args, **kwargs):
        controller.prefix = self.prefix
        controller.auth = self.auth
        controller.api = controller.api if hasattr(controller, 'api') else None
        controller.registered = False

        if not self.tags:
            tag = str(controller.__name__).lower().replace('controller', '')
            controller.tags = [tag]
        controller._path_operations = {}

        for method_route_func in self._get_class_route_functions(controller):
            method_route_func.route_definition.controller = controller
            method_route_func.route_definition.queryset = (
                    method_route_func.route_definition.queryset or controller.queryset
            )
            method_route_func.route_definition.permissions = (
                    method_route_func.route_definition.permissions or controller.permission_classes
            )
            controller.add_operation_from_route_definition(method_route_func.route_definition)

        self.add_controller(controller)
        return controller

    @classmethod
    def _get_class_route_functions(cls, controller: APIController) -> Iterator[RouteFunction]:
        for method in controller.__dict__.values():
            if isinstance(method, RouteFunction):
                yield method


router = ControllerRouter

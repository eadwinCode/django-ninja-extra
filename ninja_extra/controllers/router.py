from typing import Any, Optional, List, Iterator, Dict, TYPE_CHECKING, Tuple, cast
from django.urls import URLPattern, path as django_path
from ninja.utils import normalize_path
from ninja.constants import NOT_SET
from ninja_extra.permissions.common import AllowAny
from ninja_extra.permissions import BasePermission
from ninja_extra.controllers.route.route_functions import RouteFunction

if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIController
    from ninja_extra import NinjaExtraAPI

__all__ = ["router", "ControllerRegistry", "ControllerRouter"]


class ControllerBorg:
    _shared_state_ = dict(controllers=dict())

    def __init__(self) -> None:
        self.__dict__ = self._shared_state_

    def add_controller(self, controller: "APIController") -> None:
        self._shared_state_["controllers"].update(**{str(controller): controller})

    def remove_controller(
        self, controller: "APIController"
    ) -> Optional["APIController"]:
        if str(controller) in self._shared_state_["controllers"]:
            return self._shared_state_["controllers"].pop(str(controller))
        return None

    def clear_controller(self) -> None:
        self._shared_state_["controllers"] = dict()

    @classmethod
    def get_controllers(cls) -> Dict[str, "APIController"]:
        return cls._shared_state_.get("controllers")


class ControllerRegistry(ControllerBorg):
    def __init__(self) -> None:
        ControllerBorg.__init__(self)


class ControllerRouter:
    _tags: Optional[List[str]] = None
    _controller: "APIController"

    def __init__(
        self,
        prefix,
        *,
        auth: Any = NOT_SET,
        tags: Optional[List[str]] = None,
        permissions: List[BasePermission] = None,
    ):
        self.prefix = prefix
        self.auth = auth
        self.tags = tags
        self.permission_classes = permissions or [AllowAny]
        self._controller = None

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        tag = value
        if value and not isinstance(value, list):
            tag = [value]
        self._tags = tag

    def __call__(self, controller: "APIController"):
        self._controller = controller
        controller.permission_classes = self.permission_classes
        controller._router = self
        self.tags = self.tags or controller.tags
        ControllerRegistry().add_controller(controller)
        return controller

    @classmethod
    def _get_class_route_functions(
        cls, controller: "APIController"
    ) -> Iterator[RouteFunction]:
        for method in controller.__dict__.values():
            if isinstance(method, RouteFunction):
                yield method

    @property
    def path_operations(self):
        return self._controller.get_path_operations()

    def set_api_instance(self, api: "NinjaExtraAPI") -> None:
        self._controller.api = api
        for path_view in self.path_operations.values():
            path_view.set_api_instance(api, self)

    def build_routers(self) -> List[Tuple[str, "ControllerRouter"]]:
        return [(self.prefix, self)]

    def urls_paths(self, prefix: str) -> Iterator[URLPattern]:
        for path, path_view in self.path_operations.items():
            path = path.replace("{", "<").replace("}", ">")
            route = "/".join([i for i in (prefix, path) if i])
            # to skip lot of checks we simply treat double slash as a mistake:
            route = normalize_path(route)
            route = route.lstrip("/")

            yield django_path(
                route, path_view.get_view(), name=cast(str, path_view.url_name)
            )

    def __repr__(self):
        return f"<controller - {self._controller.__name__}>"

    def __str__(self):
        return self._controller.__name__


router = ControllerRouter

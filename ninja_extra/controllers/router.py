from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from django.urls import URLPattern, path as django_path
from ninja.constants import NOT_SET
from ninja.types import DictStrAny
from ninja.utils import normalize_path

from ninja_extra.controllers.route.route_functions import RouteFunction
from ninja_extra.permissions import BasePermission
from ninja_extra.permissions.common import AllowAny

if TYPE_CHECKING:
    from ninja_extra import NinjaExtraAPI
    from ninja_extra.controllers.base import APIController
    from ninja_extra.permissions.base import OperandHolder


class ControllerBorg:
    _shared_state_: Dict[str, Dict[str, Type["APIController"]]] = dict(
        controllers=dict()
    )

    def __init__(self) -> None:
        self.__dict__ = self._shared_state_

    def add_controller(self, controller: Type["APIController"]) -> None:
        if controller.auto_import:
            self._shared_state_["controllers"].update(**{str(controller): controller})

    def remove_controller(
        self, controller: Type["APIController"]
    ) -> Optional[Type["APIController"]]:
        if str(controller) in self._shared_state_["controllers"]:
            return self._shared_state_["controllers"].pop(str(controller))
        return None

    def clear_controller(self) -> None:
        self._shared_state_["controllers"] = dict()

    @classmethod
    def get_controllers(cls) -> Dict[str, Type["APIController"]]:
        return cls._shared_state_.get("controllers", dict())


class ControllerRegistry(ControllerBorg):
    def __init__(self) -> None:
        ControllerBorg.__init__(self)


class ControllerRouter:
    _tags: Optional[List[str]] = None
    _controller: Type["APIController"]

    def __init__(
        self,
        prefix: str,
        *,
        auth: Any = NOT_SET,
        tags: Optional[List[str]] = None,
        permissions: Optional[
            Union[List[Type[BasePermission]], List["OperandHolder[Any]"]]
        ] = None,
        controller: Optional[Type["APIController"]] = None,
    ) -> None:
        self.prefix = prefix
        self.auth = auth
        self.tags = tags
        self.permission_classes = permissions or [AllowAny]

        if controller:
            self._controller = controller
            self(controller)

    @property
    def controller(self) -> Optional[Type["APIController"]]:
        return self._controller

    @property
    def tags(self) -> Optional[List[str]]:
        return self._tags

    @tags.setter
    def tags(self, value: Union[str, List[str], None]) -> None:
        tag: Optional[List[str]] = cast(Optional[List[str]], value)
        if tag and isinstance(value, str):
            tag = [value]
        self._tags = tag

    def __call__(self, controller: Type["APIController"]) -> Type["APIController"]:
        self._controller = controller
        controller.permission_classes = self.permission_classes  # type:ignore
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
    def path_operations(self) -> DictStrAny:
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

    def __repr__(self) -> str:
        return f"<controller - {self._controller.__name__}>"

    def __str__(self) -> str:
        return f"{self._controller.__name__}"


router = ControllerRouter

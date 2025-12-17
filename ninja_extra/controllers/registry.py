from typing import TYPE_CHECKING, Dict, Optional, Type, cast

from ninja_extra.constants import API_CONTROLLER_INSTANCE
from ninja_extra.reflect import reflect

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers.base import (
        APIController,
        ControllerBase,
    )  # pragma: no cover


class ControllerRegistry:
    KEY = "CONTROLLER_REGISTRY"

    def __init__(self) -> None:
        reflect.define_metadata(self.KEY, {}, self.__class__)

    def add_controller(self, controller: Type["ControllerBase"]) -> None:
        api_controller_raw = reflect.get_metadata(API_CONTROLLER_INSTANCE, controller)
        if not api_controller_raw:
            return
        api_controller: "APIController" = cast("APIController", api_controller_raw)
        if not api_controller.auto_import:
            return
        reflect.define_metadata(self.KEY, {str(controller): controller}, self.__class__)

    def remove_controller(
        self, controller: Type["ControllerBase"]
    ) -> Optional[Type["ControllerBase"]]:
        controllers = reflect.get_metadata(self.KEY, self.__class__)

        if controllers and str(controller) in controllers:
            removed_controller: Type["ControllerBase"] = cast(
                Type["ControllerBase"], controllers[str(controller)]
            )
            del controllers[str(controller)]

            reflect.delete_metadata(self.KEY, self.__class__)
            reflect.define_metadata(self.KEY, controllers, self.__class__)

            return removed_controller
        return None

    def clear_controller(self) -> None:
        reflect.delete_metadata(self.KEY, self.__class__)
        reflect.define_metadata(self.KEY, {}, self.__class__)

    def get_controllers(self) -> Dict[str, Type["ControllerBase"]]:
        controllers = reflect.get_metadata(self.KEY, self.__class__)
        return (
            cast(Dict[str, Type["ControllerBase"]], controllers) if controllers else {}
        )


controller_registry = ControllerRegistry()

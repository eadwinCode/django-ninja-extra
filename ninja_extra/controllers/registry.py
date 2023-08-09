from typing import TYPE_CHECKING, Dict, Optional, Type

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers.base import ControllerBase  # pragma: no cover


class ControllerBorg:
    _shared_state_: Dict[str, Dict[str, Type["ControllerBase"]]] = {"controllers": {}}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state_

    def add_controller(self, controller: Type["ControllerBase"]) -> None:
        if (
            hasattr(controller, "get_api_controller")
            and controller.get_api_controller().auto_import
        ):
            self._shared_state_["controllers"].update({str(controller): controller})

    def remove_controller(
        self, controller: Type["ControllerBase"]
    ) -> Optional[Type["ControllerBase"]]:
        if str(controller) in self._shared_state_["controllers"]:
            return self._shared_state_["controllers"].pop(str(controller))
        return None

    def clear_controller(self) -> None:
        self._shared_state_["controllers"] = {}

    @classmethod
    def get_controllers(cls) -> Dict[str, Type["ControllerBase"]]:
        return cls._shared_state_.get("controllers", {})


class ControllerRegistry(ControllerBorg):
    def __init__(self) -> None:
        ControllerBorg.__init__(self)

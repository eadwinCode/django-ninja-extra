import typing as t

from ninja_extra.constants import API_CONTROLLER_INSTANCE
from ninja_extra.reflect import reflect

if t.TYPE_CHECKING:  # pragma: no cover
    from .base import APIController, ControllerBase


def get_api_controller(
    controller_class: t.Type["ControllerBase"],
) -> t.Optional["APIController"]:
    return t.cast(
        "APIController", reflect.get_metadata(API_CONTROLLER_INSTANCE, controller_class)
    )

from typing import (
    Any,
    Optional,
    Type,
    Union,
    no_type_check,
)

from ninja import Schema

from ninja_extra import status


class ControllerResponse:
    status_code: int = status.HTTP_204_NO_CONTENT
    _schema: Optional[Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Controller Response are no longer supported.")

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:  # pragma: no cover
        raise NotImplementedError

    def convert_to_schema(self) -> Any:  # pragma: no cover
        raise NotImplementedError

    @no_type_check
    def __class_getitem__(cls: Type["ControllerResponse"], item: Any) -> Any:
        raise RuntimeError("Controller Response are no longer supported.")


Detail = ControllerResponse
Ok = ControllerResponse
Id = ControllerResponse

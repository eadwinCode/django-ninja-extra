import abc
from typing import Any, Optional, Type, Union

from ninja import Schema
from pydantic.types import UUID1, UUID3, UUID4, UUID5

from ninja_extra import status


class ControllerResponse(abc.ABC):
    status_code: int = status.HTTP_204_NO_CONTENT

    def __init__(self, **kwargs: Any) -> None:
        pass

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def convert_to_schema(self) -> Any:
        pass


class Id(ControllerResponse):
    status_code: int = status.HTTP_201_CREATED
    id: Union[int, str, UUID4, UUID1, UUID3, UUID5, Any]

    def __init__(self, id: Any) -> None:
        super(Id, self).__init__()
        self.id = id

    class Id(Schema):
        id: Any

    def convert_to_schema(self) -> Any:
        return self.Id.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls.Id


class Ok(ControllerResponse):
    status_code: int = status.HTTP_200_OK
    message: Any = "Action was successful"

    def __init__(self, message: Optional[Any] = None) -> None:
        super(Ok, self).__init__()
        self.message = message or self.message

    class Ok(Schema):
        message: Any

    def convert_to_schema(self) -> Any:
        return self.Ok.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls.Ok


class Detail(ControllerResponse):
    status_code: int = status.HTTP_200_OK
    message: Any = dict()

    def __init__(
        self, message: Optional[Any] = None, status_code: int = status.HTTP_200_OK
    ) -> None:
        super(Detail, self).__init__()
        self.message = message or self.message
        self.status_code = status_code or self.status_code

    class Detail(Schema):
        message: Any

    def convert_to_schema(self) -> Any:
        return self.Detail.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls.Detail


# class NotFound(ControllerResponse):
#     status_code: int = status.HTTP_404_NOT_FOUND
#     message: Any = 'Item not found'
#
#     def __init__(self, detail: Optional[Any] = None) -> None:
#         super(NotFound, self).__init__()
#         self.detail = detail or self.message
#
#     class NotFound(Schema):
#         message: Any
#
#     def convert_to_schema(self) -> Any:
#         return self.NotFound.from_orm(self)
#
#     @classmethod
#     def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
#         return cls.NotFound

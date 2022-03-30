from typing import Any, Dict, List, Optional, Type, Union

from ninja import Schema
from pydantic.types import UUID1, UUID3, UUID4, UUID5

from ninja_extra import status


class ControllerResponseMeta(type):
    pass


class ControllerResponse(metaclass=ControllerResponseMeta):
    status_code: int = status.HTTP_204_NO_CONTENT

    def __init__(self, **kwargs: Any) -> None:
        pass

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        raise NotImplementedError

    def convert_to_schema(self) -> Any:
        raise NotImplementedError


class Id(ControllerResponse):
    """
    Creates a 201 response with id information
    {
        id: int| str| UUID4| UUID1| UUID3| UUID5,
    }
    Example:
           Id(423) ==> 201, {id: 423}
    """

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
    """
    Creates a 200 response with a detail information.
    {
        detail: str| List[Dict] | List[str] | Dict,
    }

    Example:
       Ok('Saved Successfully') ==> 200, {detail: 'Saved Successfully'}

    """

    status_code: int = status.HTTP_200_OK
    detail: Union[str, List[Dict], List[str], Dict] = "Action was successful"

    def __init__(self, message: Optional[Any] = None) -> None:
        super(Ok, self).__init__()
        self.detail = message or self.detail

    class Ok(Schema):
        detail: Union[str, List[Dict], List[str], Dict]

    def convert_to_schema(self) -> Any:
        return self.Ok.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls.Ok


class Detail(ControllerResponse):
    """
    Creates a custom response with detail information
    {
        detail: str| List[Dict] | List[str] | Dict,
    }
    Example:
       Detail('Invalid Request', 404) ==> 404, {detail: 'Invalid Request'}
    """

    status_code: int = status.HTTP_200_OK
    detail: Union[str, List[Dict], List[str], Dict] = dict()

    def __init__(
        self, message: Optional[Any] = None, status_code: int = status.HTTP_200_OK
    ) -> None:
        super(Detail, self).__init__()
        self.detail = message or self.detail
        self.status_code = status_code or self.status_code

    class Detail(Schema):
        detail: Union[str, List[Dict], List[str], Dict]

    def convert_to_schema(self) -> Any:
        return self.Detail.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls.Detail

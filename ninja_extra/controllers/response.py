import sys
from typing import (
    Any,
    Dict,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    no_type_check,
)

from ninja import Schema

from .. import status
from ..schemas import DetailSchema, IdSchema, OkSchema

T = TypeVar("T")
SCHEMA_KEY = "_schema"

if sys.version_info < (3, 7):  # pragma: no cover
    from typing import GenericMeta  # type: ignore[attr-defined]

    class ControllerResponseMeta(GenericMeta):
        @no_type_check
        def __new__(mcls, name: str, bases: Tuple, namespace: Dict, **kwargs: Any):
            args = kwargs.get("args")
            if args and args[0].__name__ != "T":
                t = args[0]
                origin_schema = namespace.get(SCHEMA_KEY)
                if origin_schema and hasattr(origin_schema, "__generic_model__"):
                    schema = origin_schema.__generic_model__[t]
                else:
                    schema = origin_schema[t]
                namespace[SCHEMA_KEY] = schema
            res = super().__new__(mcls, name, bases, namespace, **kwargs)
            return res

    class GenericControllerResponse(metaclass=ControllerResponseMeta):
        @no_type_check
        def __new__(
            cls: Type["ControllerResponse[T]"], *args: Any, **kwargs: Any
        ) -> "ControllerResponse[T]":
            if cls._gorg is Generic or "_schema" not in cls.__dict__:
                raise TypeError(
                    "Type Generic cannot be instantiated; "
                    "it can be used only as a base class"
                )
            return object.__new__(cls)

else:
    _generic_types_cache: Dict[
        Tuple[Type[Any], Union[Any, Tuple[Any, ...]]], Type["ControllerResponse"]
    ] = {}
    GenericControllerResponseT = TypeVar(
        "GenericControllerResponseT", bound="GenericControllerResponse"
    )

    class ControllerResponseMeta(type):
        pass

    class GenericControllerResponse(metaclass=ControllerResponseMeta):
        def __new__(  # type:ignore[misc]
            cls: Type["ControllerResponse[T]"], *args: Any, **kwargs: Any
        ) -> "ControllerResponse[T]":
            if "_schema" not in cls.__dict__:
                raise TypeError(
                    "Type Generic cannot be instantiated; "
                    "it can be used only as a base class"
                )
            return object.__new__(cls)

        @no_type_check
        def __class_getitem__(cls: Type[GenericControllerResponseT], item: Any) -> Any:
            if isinstance(item, tuple):
                raise TypeError("Tuple Generic Model not supported")

            _key = (cls, item)
            _cached_value = _generic_types_cache.get(_key)
            if _cached_value:
                return _cached_value

            if str(type(item)) == "<class 'typing.TypeVar'>":
                result = super().__class_getitem__(item)
            else:
                new_schema = cls.__dict__.get(SCHEMA_KEY)
                if hasattr(new_schema, "__generic_model__"):
                    new_schema = new_schema.__generic_model__[item]

                result = type(
                    f"{cls.__name__}[{item.__name__}]", (cls,), {SCHEMA_KEY: new_schema}
                )
            _generic_types_cache[_key] = result
            return result


class ControllerResponse(GenericControllerResponse, Generic[T]):
    status_code: int = status.HTTP_204_NO_CONTENT
    _schema: Optional[T]

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:  # pragma: no cover
        raise NotImplementedError

    def convert_to_schema(self) -> Any:  # pragma: no cover
        raise NotImplementedError


class Id(ControllerResponse[T]):
    """
    Creates a 201 response with id information
    {
        id: int| str| UUID4| UUID1| UUID3| UUID5,
    }
    Example:
           Id(423) ==> 201, {id: 423}
           OR
           Id[int](424) ==> 201, {id: 424}
           Id[UUID4]("883a1a3d-7b10-458d-bccc-f9b7219342c9")
                ==> 201, {id: "883a1a3d-7b10-458d-bccc-f9b7219342c9"}
    """

    _schema = IdSchema[Any]
    status_code: int = status.HTTP_201_CREATED

    def __init__(self, id: T) -> None:
        super(Id, self).__init__()
        self.id = id

    def convert_to_schema(self) -> Any:
        return self._schema.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls._schema


class Ok(ControllerResponse[T]):
    """
    Creates a 200 response with a detail information.
    {
        detail: str| List[Dict] | List[str] | Dict,
    }

    Example:
       Ok('Saved Successfully') ==> 200, {detail: 'Saved Successfully'}
       OR
       class ASchema(BaseModel):
            name: str
            age: int

       OK[ASchema](ASchema(name='Eadwin', age=18)) ==> 200, {detail: {'name':'Eadwin', 'age': 18}}
    """

    status_code: int = status.HTTP_200_OK
    _schema = OkSchema[Any]

    def __init__(self, message: Optional[Any] = None) -> None:
        super(Ok, self).__init__()
        self.detail = message or "Action was successful"

    def convert_to_schema(self) -> Any:
        return self._schema.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls._schema


class Detail(ControllerResponse[T]):
    """
    Creates a custom response with detail information
    {
        detail: str| List[Dict] | List[str] | Dict,
    }
    Example:
       Detail('Invalid Request', 404) ==> 404, {detail: 'Invalid Request'}
       OR
        class ErrorSchema(BaseModel):
            message: str

       Detail[ErrorSchema](dict(message='Bad Request'),400) ==> 400, {detail: {'message':'Bad Request'}}
    """

    status_code: int = status.HTTP_200_OK
    _schema = DetailSchema[Any]

    def __init__(
        self, message: Optional[Any] = None, status_code: int = status.HTTP_200_OK
    ) -> None:
        super(Detail, self).__init__()
        self.detail = message or "Action was successful"
        self.status_code = status_code or self.status_code

    def convert_to_schema(self) -> Any:
        return self._schema.from_orm(self)

    @classmethod
    def get_schema(cls) -> Union[Schema, Type[Schema], Any]:
        return cls._schema

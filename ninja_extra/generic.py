from typing import Any, Dict, Optional, Tuple, Type, cast, no_type_check

_generic_types_registry: Dict[Tuple[Type["GenericType"], Type], Type] = {}


class GenericModelMeta(type):
    def _get_name(self: Type["GenericType"], wrap_type: Type) -> str:  # type: ignore
        _name = f"{self._generic_base_name or self.__name__}"
        if hasattr(wrap_type, "__name__"):
            _name += f"[{str(wrap_type.__name__)}]"
        return _name

    def __getitem__(self: Type["GenericType"], wraps: Any) -> Any:  # type: ignore
        if (self, wraps) not in _generic_types_registry:
            new_generic_type = cast(Type, self().get_generic_type(wraps))
            new_generic_type.__generic_model__ = self
            new_generic_type.__name__ = self._get_name(wraps)

            _generic_types_registry[self, wraps] = new_generic_type
        return _generic_types_registry[self, wraps]


@no_type_check
class GenericType(metaclass=GenericModelMeta):
    _generic_base_name: Optional[str] = None
    """
    Get a wrapper class that mimic python 3.8 generic support to python3.6, 3.7
    Examples
    --------
    Create a Class to reference the generic model to be create:
    >>> class ObjectA(GenericType, generic_base_name="A"):
    >>>     def get_generic_type(self, wrap_type):
    >>>         class ObjectAGeneric(self):
    >>>             item: wrap_type
    >>>         return ObjectAGeneric

    Usage:
    >>> class Pass: ...
    >>> object_generic_type  = ObjectA[Pass]
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        cls._generic_base_name = kwargs.get("generic_base_name")
        return super().__init_subclass__()

    def get_generic_type(self, wrap_type: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

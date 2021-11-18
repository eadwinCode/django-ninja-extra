from typing import Any, Dict, no_type_check


class GenericModelMeta(type):
    registry: Dict = {}

    def __getitem__(self, wraps: Any) -> Any:
        if (self, wraps) not in self.__class__.registry:
            self.__class__.registry[self, wraps] = self().get_generic_type(wraps)
        return self.__class__.registry[self, wraps]


@no_type_check
class GenericType(metaclass=GenericModelMeta):
    """
    Get a wrapper class that mimic python 3.8 generic support to python3.6, 3.7
    Examples
    --------
    Create a Class to reference the generic model to be create:
    >>> class ObjectA(GenericType):
    >>>     def get_generic_type(self, wrap_type):
    >>>         class ObjectAGeneric(self):
    >>>             item: wrap_type
    >>>         ObjectAGeneric.__name__ = (
    >>>             f"{self.__class__.__name__}[{str(wrap_type.__name__).capitalize()}]"
    >>>         )
    >>>         return ObjectAGeneric

    Usage:
    >>> class Pass: ...
    >>> object_generic_type  = ObjectA[Pass]
    """

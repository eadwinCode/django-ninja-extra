"""
Copied from DRF
Provides a set of pluggable permission policies.
"""
from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Tuple, Type, TypeVar, Union

from django.http import HttpRequest
from ninja.types import DictStrAny

if TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers.base import ControllerBase  # pragma: no cover

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

T = TypeVar("T")


class OperationHolderMixin:
    def __and__(
        self, other: Union[Type["BasePermission"], "BasePermission"]
    ) -> "OperandHolder[AND]":
        return OperandHolder(AND, self, other)  # type: ignore

    def __or__(
        self, other: Union[Type["BasePermission"], "BasePermission"]
    ) -> "OperandHolder[OR]":
        return OperandHolder(OR, self, other)  # type: ignore

    def __rand__(
        self, other: Union[Type["BasePermission"], "BasePermission"]
    ) -> "OperandHolder[AND]":  # pragma: no cover
        return OperandHolder(AND, other, self)  # type: ignore

    def __ror__(
        self, other: Union[Type["BasePermission"], "BasePermission"]
    ) -> "OperandHolder[OR]":  # pragma: no cover
        return OperandHolder(OR, other, self)  # type: ignore

    def __invert__(self) -> "SingleOperandHolder[NOT]":
        return SingleOperandHolder(NOT, self)  # type: ignore


class BasePermissionMetaclass(OperationHolderMixin, ABCMeta):
    pass


class BasePermission(ABC, metaclass=BasePermissionMetaclass):  # pragma: no cover
    """
    A base class from which all permission classes should inherit.
    """

    message: Any = None

    @abstractmethod
    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: Any
    ) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True


class SingleOperandHolder(OperationHolderMixin, Generic[T]):
    def __init__(
        self,
        operator_class: Type[BasePermission],
        op1_class: Union[Type["BasePermission"], "BasePermission"],
    ) -> None:
        super().__init__()
        self.operator_class = operator_class
        self.op1_class = op1_class

    def __call__(self, *args: Tuple[Any], **kwargs: DictStrAny) -> BasePermission:
        op1 = self.op1_class
        if isinstance(self.op1_class, (type, OperationHolderMixin)):
            op1 = self.op1_class()
        return self.operator_class(op1)  # type: ignore


class OperandHolder(OperationHolderMixin, Generic[T]):
    def __init__(
        self,
        operator_class: Type["BasePermission"],
        op1_class: Union[Type["BasePermission"], "BasePermission"],
        op2_class: Union[Type["BasePermission"], "BasePermission"],
    ) -> None:
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args: Tuple[Any], **kwargs: DictStrAny) -> BasePermission:
        op1 = self.op1_class
        op2 = self.op2_class

        if isinstance(self.op1_class, (type, OperationHolderMixin)):
            op1 = self.op1_class()

        if isinstance(self.op2_class, (type, OperationHolderMixin)):
            op2 = self.op2_class()
        return self.operator_class(op1, op2)  # type: ignore


class AND(BasePermission):
    def __init__(self, op1: "BasePermission", op2: "BasePermission") -> None:
        self.op1 = op1
        self.op2 = op2

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        return self.op1.has_permission(request, controller) and self.op2.has_permission(
            request, controller
        )

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: Any
    ) -> bool:
        return self.op1.has_object_permission(
            request, controller, obj
        ) and self.op2.has_object_permission(request, controller, obj)


class OR(BasePermission):
    def __init__(self, op1: "BasePermission", op2: "BasePermission") -> None:
        self.op1 = op1
        self.op2 = op2

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        return self.op1.has_permission(request, controller) or self.op2.has_permission(
            request, controller
        )

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: Any
    ) -> bool:
        return self.op1.has_object_permission(
            request, controller, obj
        ) or self.op2.has_object_permission(request, controller, obj)


class NOT(BasePermission):
    def __init__(self, op1: "BasePermission") -> None:
        self.op1 = op1

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        return not self.op1.has_permission(request, controller)

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: Any
    ) -> bool:
        return not self.op1.has_object_permission(request, controller, obj)

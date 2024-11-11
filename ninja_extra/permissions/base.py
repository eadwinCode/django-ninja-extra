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
    def __and__(  # type:ignore[misc]
        self: Union[Type["BasePermission"], "BasePermission"],
        other: Union[Type["BasePermission"], "BasePermission"],
    ) -> "OperandHolder[AND]":
        return OperandHolder(AND, self, other)

    def __or__(  # type:ignore[misc]
        self: Union[Type["BasePermission"], "BasePermission"],
        other: Union[Type["BasePermission"], "BasePermission"],
    ) -> "OperandHolder[OR]":
        return OperandHolder(OR, self, other)

    def __rand__(  # type:ignore[misc]
        self: Union[Type["BasePermission"], "BasePermission"],
        other: Union[Type["BasePermission"], "BasePermission"],
    ) -> "OperandHolder[AND]":  # pragma: no cover
        return OperandHolder(AND, other, self)

    def __ror__(  # type:ignore[misc]
        self: Union[Type["BasePermission"], "BasePermission"],
        other: Union[Type["BasePermission"], "BasePermission"],
    ) -> "OperandHolder[OR]":  # pragma: no cover
        return OperandHolder(OR, other, self)

    def __invert__(  # type:ignore[misc]
        self: Union[Type["BasePermission"], "BasePermission"],
    ) -> "SingleOperandHolder[NOT]":
        return SingleOperandHolder(NOT, self)


class BasePermissionMetaclass(OperationHolderMixin, ABCMeta): ...


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
        # Instance the Permission class before using it
        self.op1 = op1_class
        self.op2 = op2_class
        self.message = op1_class.message
        if isinstance(op1_class, (type, OperationHolderMixin)):
            self.op1 = op1_class()

        if isinstance(op2_class, (type, OperationHolderMixin)):
            self.op2 = op2_class()

    def __call__(self, *args: Tuple[Any], **kwargs: DictStrAny) -> BasePermission:
        return self.operator_class(self.op1, self.op2)  # type: ignore


class AND(BasePermission):
    def __init__(self, op1: "BasePermission", op2: "BasePermission") -> None:
        self.op1 = op1
        self.op2 = op2
        self.message = op1.message

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        if self.op1.has_permission(request, controller):
            self.message = self.op2.message
            return self.op2.has_permission(request, controller)
        return False

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
        self.message = op1.message

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        if not self.op1.has_permission(request, controller):
            self.message = self.op2.message
            return self.op2.has_permission(request, controller)
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: Any
    ) -> bool:
        return self.op1.has_object_permission(
            request, controller, obj
        ) or self.op2.has_object_permission(request, controller, obj)


class NOT(BasePermission):
    def __init__(self, op1: "BasePermission") -> None:
        self.op1 = op1
        self.message = op1.message

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        return not self.op1.has_permission(request, controller)

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: Any
    ) -> bool:
        return not self.op1.has_object_permission(request, controller, obj)

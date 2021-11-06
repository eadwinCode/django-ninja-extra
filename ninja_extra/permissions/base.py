"""
Copied from DRF
Provides a set of pluggable permission policies.
"""
from typing import TYPE_CHECKING, Any, Generic, Tuple, Type, TypeVar

from django.http import HttpRequest
from ninja.types import DictStrAny

if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIController

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

T = TypeVar("T")


class OperationHolderMixin:
    def __and__(self, other: Type["BasePermission"]) -> "OperandHolder[AND]":
        return OperandHolder(AND, self, other)  # type: ignore

    def __or__(self, other: Type["BasePermission"]) -> "OperandHolder[OR]":
        return OperandHolder(OR, self, other)  # type: ignore

    def __rand__(self, other: Type["BasePermission"]) -> "OperandHolder[AND]":
        return OperandHolder(AND, other, self)  # type: ignore

    def __ror__(self, other: Type["BasePermission"]) -> "OperandHolder[OR]":
        return OperandHolder(OR, other, self)  # type: ignore

    def __invert__(self) -> "SingleOperandHolder[NOT]":
        return SingleOperandHolder(NOT, self)  # type: ignore


class SingleOperandHolder(OperationHolderMixin, Generic[T]):
    def __init__(self, operator_class: T, op1_class: Type["BasePermission"]) -> None:
        self.operator_class = operator_class
        self.op1_class = op1_class

    def __call__(self, *args: Tuple[Any], **kwargs: DictStrAny) -> T:
        op1 = self.op1_class()
        return self.operator_class(op1)  # type: ignore


class OperandHolder(OperationHolderMixin, Generic[T]):
    def __init__(
        self,
        operator_class: T,
        op1_class: Type["BasePermission"],
        op2_class: Type["BasePermission"],
    ) -> None:
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args: Tuple[Any], **kwargs: DictStrAny) -> T:
        op1 = self.op1_class()
        op2 = self.op2_class()
        return self.operator_class(op1, op2)  # type: ignore


class AND:
    def __init__(self, op1: "BasePermission", op2: "BasePermission") -> None:
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request: HttpRequest, controller: "APIController") -> bool:
        return self.op1.has_permission(request, controller) and self.op2.has_permission(
            request, controller
        )

    def has_object_permission(
        self, request: HttpRequest, controller: "APIController", obj: Any
    ) -> bool:
        return self.op1.has_object_permission(
            request, controller, obj
        ) and self.op2.has_object_permission(request, controller, obj)


class OR:
    def __init__(self, op1: "BasePermission", op2: "BasePermission") -> None:
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request: HttpRequest, controller: "APIController") -> bool:
        return self.op1.has_permission(request, controller) or self.op2.has_permission(
            request, controller
        )

    def has_object_permission(
        self, request: HttpRequest, controller: "APIController", obj: Any
    ) -> bool:
        return self.op1.has_object_permission(
            request, controller, obj
        ) or self.op2.has_object_permission(request, controller, obj)


class NOT:
    def __init__(self, op1: "BasePermission") -> None:
        self.op1 = op1

    def has_permission(self, request: HttpRequest, controller: "APIController") -> bool:
        return not self.op1.has_permission(request, controller)

    def has_object_permission(
        self, request: HttpRequest, controller: "APIController", obj: Any
    ) -> bool:
        return not self.op1.has_object_permission(request, controller, obj)


class BasePermissionMetaclass(OperationHolderMixin, type):
    pass


class BasePermission(metaclass=BasePermissionMetaclass):
    """
    A base class from which all permission classes should inherit.
    """

    message = None

    def has_permission(self, request: HttpRequest, controller: "APIController") -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: "APIController", obj: Any
    ) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

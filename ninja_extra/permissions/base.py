"""
Copied from DRF
Provides a set of pluggable permission policies.
"""
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Any

from django.http import HttpRequest

if TYPE_CHECKING:
    from ninja_extra.controllers.base import APIController

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class OperationHolderMixin:
    def __and__(self, other):
        return OperandHolder(AND, self, other)

    def __or__(self, other):
        return OperandHolder(OR, self, other)

    def __rand__(self, other):
        return OperandHolder(AND, other, self)

    def __ror__(self, other):
        return OperandHolder(OR, other, self)

    def __invert__(self):
        return SingleOperandHolder(NOT, self)


class SingleOperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class):
        self.operator_class = operator_class
        self.op1_class = op1_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        return self.operator_class(op1)


class OperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class, op2_class):
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        op2 = self.op2_class(*args, **kwargs)
        return self.operator_class(op1, op2)


class AND:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request: HttpRequest, controller: "APIController") -> bool:
        return self.op1.has_permission(request, controller) and self.op2.has_permission(
            request, controller
        )

    def has_object_permission(
        self, request: HttpRequest, controller: "APIController", obj
    ) -> bool:
        return self.op1.has_object_permission(
            request, controller, obj
        ) and self.op2.has_object_permission(request, controller, obj)


class OR:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request: HttpRequest, controller: "APIController") -> bool:
        return self.op1.has_permission(request, controller) or self.op2.has_permission(
            request, controller
        )

    def has_object_permission(
        self, request: HttpRequest, controller: "APIController", obj
    ) -> bool:
        return self.op1.has_object_permission(
            request, controller, obj
        ) or self.op2.has_object_permission(request, controller, obj)


class NOT:
    def __init__(self, op1):
        self.op1 = op1

    def has_permission(self, request: HttpRequest, controller: "APIController") -> bool:
        return not self.op1.has_permission(request, controller)

    def has_object_permission(
        self, request: HttpRequest, controller: "APIController", obj
    ) -> bool:
        return not self.op1.has_object_permission(request, controller, obj)


class BasePermissionMetaclass(OperationHolderMixin, type):
    pass


class BasePermission(metaclass=BasePermissionMetaclass):
    """
    A base class from which all permission classes should inherit.
    """

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

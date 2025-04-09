"""
Copied from DRF
Provides a set of pluggable permission policies.
"""

import typing as t
from abc import ABC, ABCMeta, abstractmethod

from django.http import HttpRequest
from injector import is_decorated_with_inject

from ninja_extra.threading import execute_coroutine

if t.TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.controllers.base import ControllerBase  # pragma: no cover

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

T = t.TypeVar("T")


class _OperationHolderMixin:
    def __and__(  # type:ignore[misc]
        self: "BasePermissionType",
        other: "BasePermissionType",
    ) -> t.Union["BasePermission", "AsyncBasePermission"]:
        return AND(self, other)

    def __or__(  # type:ignore[misc]
        self: "BasePermissionType",
        other: "BasePermissionType",
    ) -> t.Union["BasePermission", "AsyncBasePermission"]:
        return OR(self, other)

    def __rand__(  # type:ignore[misc]
        self: "BasePermissionType",
        other: "BasePermissionType",
    ) -> t.Union["BasePermission", "AsyncBasePermission"]:  # pragma: no cover
        return AND(self, other)

    def __ror__(  # type:ignore[misc]
        self: "BasePermissionType",
        other: "BasePermissionType",
    ) -> t.Union["BasePermission", "AsyncBasePermission"]:  # pragma: no cover
        return OR(self, other)

    def __invert__(  # type:ignore[misc]
        self: "BasePermissionType",
    ) -> t.Union["BasePermission", "AsyncBasePermission"]:
        return NOT(self)


class BasePermissionMetaclass(_OperationHolderMixin, ABCMeta):
    pass


class BasePermission(
    ABC, _OperationHolderMixin, metaclass=BasePermissionMetaclass
):  # pragma: no cover
    """
    A base class from which all permission classes should inherit.
    """

    message: t.Any = None

    @abstractmethod
    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    @classmethod
    def resolve(cls) -> t.Union["BasePermission", "AsyncBasePermission"]:
        from ninja_extra import service_resolver

        if is_decorated_with_inject(getattr(cls, "__init__", cls)):
            return service_resolver(  # type: ignore[return-value]
                t.cast(t.Type[t.Union[BasePermission, AsyncBasePermission]], cls)
            )
        return cls()


class AsyncBasePermission(BasePermission, ABC):
    """
    A base class for asynchronous permission classes.

    This class extends the permission checking capabilities,
    allowing for efficient permission checks with async Django models using asgiref.
    """

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        res = execute_coroutine(self.has_permission_async(request, controller))
        return t.cast(bool, res)

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        res = execute_coroutine(
            self.has_object_permission_async(request, controller, obj)
        )
        return t.cast(bool, res)

    @abstractmethod
    async def has_permission_async(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        """
        Asynchronous version of has_permission.
        By default, it calls the synchronous has_permission method using sync_to_async.
        Override this method to implement custom async permission logic.

        Return `True` if permission is granted, `False` otherwise.
        """

    async def has_object_permission_async(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        """
        Asynchronous version of has_object_permission.
        By default, it calls the synchronous has_object_permission method using sync_to_async.
        Override this method to implement custom async object permission logic.

        Return `True` if permission is granted, `False` otherwise.
        """
        return True


BasePermissionType = t.Union[
    BasePermission,
    t.Type[BasePermission],
    AsyncBasePermission,
    t.Type[AsyncBasePermission],
]


class _OperandResolversMixin:
    def resolve(self) -> t.Union["BasePermission", "AsyncBasePermission"]:
        return t.cast(t.Union["BasePermission", "AsyncBasePermission"], self)

    def _get_permission_object(
        self, permission: BasePermissionType
    ) -> t.Union[BasePermission, AsyncBasePermission]:
        from ninja_extra import service_resolver

        if isinstance(permission, type) and is_decorated_with_inject(
            getattr(permission, "__init__", permission)
        ):
            return service_resolver(  # type: ignore[return-value]
                permission
            )
        if isinstance(permission, type):
            return permission()
        return permission


class AND(_OperandResolversMixin, AsyncBasePermission):
    """
    Logical AND operator for permissions.
    Works with both sync and async permissions.
    """

    def __init__(
        self,
        op1: BasePermissionType,
        op2: BasePermissionType,
    ) -> None:
        self.op1 = op1
        self.op2 = op2
        self.message = getattr(op1, "message", None)

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        if op1.has_permission(request, controller):
            self.message = getattr(op2, "message", None)
            return op2.has_permission(request, controller)
        return False

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        return op1.has_object_permission(
            request, controller, obj
        ) and op2.has_object_permission(request, controller, obj)

    async def has_permission_async(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        from asgiref.sync import sync_to_async

        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        # Handle op1
        if isinstance(op1, AsyncBasePermission):
            if not await op1.has_permission_async(request, controller):
                return False
        else:
            if not await sync_to_async(op1.has_permission)(request, controller):
                return False

        # Handle op2
        self.message = getattr(op2, "message", None)
        if isinstance(op2, AsyncBasePermission):
            return await op2.has_permission_async(request, controller)
        else:
            return await sync_to_async(op2.has_permission)(request, controller)

    async def has_object_permission_async(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        from asgiref.sync import sync_to_async

        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        # Handle op1
        if isinstance(op1, AsyncBasePermission):
            result1 = await op1.has_object_permission_async(request, controller, obj)
        else:
            result1 = await sync_to_async(op1.has_object_permission)(
                request, controller, obj
            )

        # Short-circuit if first permission fails
        if not result1:
            return False

        # Handle op2
        if isinstance(op2, AsyncBasePermission):
            result2 = await op2.has_object_permission_async(request, controller, obj)
        else:
            result2 = await sync_to_async(op2.has_object_permission)(
                request, controller, obj
            )

        return result1 and result2


class OR(_OperandResolversMixin, AsyncBasePermission):
    """
    Logical OR operator for permissions.
    Works with both sync and async permissions.
    """

    def __init__(
        self,
        op1: BasePermissionType,
        op2: BasePermissionType,
    ) -> None:
        self.op1 = op1
        self.op2 = op2
        self.message = getattr(op1, "message", None)

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        if not op1.has_permission(request, controller):
            self.message = getattr(op2, "message", None)
            return op2.has_permission(request, controller)
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        return op1.has_object_permission(
            request, controller, obj
        ) or op2.has_object_permission(request, controller, obj)

    async def has_permission_async(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        from asgiref.sync import sync_to_async

        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        # Handle op1
        if isinstance(op1, AsyncBasePermission):
            if await op1.has_permission_async(request, controller):
                return True
        else:
            if await sync_to_async(op1.has_permission)(request, controller):
                return True

        # Op1 failed, check op2
        self.message = getattr(op2, "message", None)
        if isinstance(op2, AsyncBasePermission):
            return await op2.has_permission_async(request, controller)
        else:
            return await sync_to_async(op2.has_permission)(request, controller)

    async def has_object_permission_async(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        from asgiref.sync import sync_to_async

        op1 = self._get_permission_object(self.op1)
        op2 = self._get_permission_object(self.op2)

        # Handle op1
        if isinstance(op1, AsyncBasePermission):
            result1 = await op1.has_object_permission_async(request, controller, obj)
        else:
            result1 = await sync_to_async(op1.has_object_permission)(
                request, controller, obj
            )

        # Short-circuit if first permission succeeds
        if result1:
            return True

        # Handle op2
        if isinstance(op2, AsyncBasePermission):
            return await op2.has_object_permission_async(request, controller, obj)
        else:
            return await sync_to_async(op2.has_object_permission)(
                request, controller, obj
            )


class NOT(_OperandResolversMixin, AsyncBasePermission):
    """
    Logical NOT operator for permissions.
    Works with both sync and async permissions.
    """

    def __init__(self, op1: BasePermissionType) -> None:
        self.op1 = op1
        self.message = getattr(op1, "message", None)

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        op1 = self._get_permission_object(self.op1)

        return not op1.has_permission(request, controller)

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        op1 = self._get_permission_object(self.op1)

        return not op1.has_object_permission(request, controller, obj)

    async def has_permission_async(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        from asgiref.sync import sync_to_async

        op1 = self._get_permission_object(self.op1)

        if isinstance(op1, AsyncBasePermission):
            return not await op1.has_permission_async(request, controller)
        else:
            return not await sync_to_async(op1.has_permission)(request, controller)

    async def has_object_permission_async(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        from asgiref.sync import sync_to_async

        op1 = self._get_permission_object(self.op1)

        if isinstance(op1, AsyncBasePermission):
            return not await op1.has_object_permission_async(request, controller, obj)
        else:
            return not await sync_to_async(op1.has_object_permission)(
                request, controller, obj
            )

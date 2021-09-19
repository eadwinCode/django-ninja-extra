from typing import List, Callable, cast

from django.http import HttpRequest
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.permissions.base import BasePermission

__all__ = ["APIControllerPermissionMixin"]


class APIControllerPermissionMixin:
    # partial class of APIController

    permission_classes: List[BasePermission]
    request: HttpRequest = None

    @classmethod
    def permission_denied(cls, permission: BasePermission):
        message = getattr(permission, "message", None)
        raise PermissionDenied(message)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        for permission_class in self.permission_classes:
            permission_class = cast(Callable, permission_class)
            permission_instance = permission_class()
            yield permission_instance

    def check_permissions(self):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(request=self.request, controller=self):
                self.permission_denied(permission)

    def check_object_permissions(self, obj):
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(
                request=self.request, controller=self, obj=obj
            ):
                self.permission_denied(permission)

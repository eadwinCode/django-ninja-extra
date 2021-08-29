from typing import List
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.permissions.base import BasePermission

__all__ = ['NinjaExtraAPIPermissionMixin']


class NinjaExtraAPIPermissionMixin:
    permission_classes: List[BasePermission] = []
    request = None

    @staticmethod
    def permission_denied(permission):
        message = getattr(permission, 'message', None)
        raise PermissionDenied(message)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def check_permissions(self):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(self.request, self):
                self.permission_denied(permission)

    def check_object_permissions(self, obj):
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(self.request, self, obj):
                self.permission_denied(permission)


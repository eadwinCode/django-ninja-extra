from typing import TYPE_CHECKING

from django.http import HttpRequest

from ninja_extra.permissions.base import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from ninja_extra.controllers.base import ControllerBase  # pragma: no cover


class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        return True


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        user = request.user or request.auth  # type: ignore
        return bool(user and user.is_authenticated)


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    message: str = "You must be an admin user to access this resource."

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        user = request.user or request.auth  # type: ignore
        return bool(user and user.is_staff)  # type: ignore


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        user = request.user or request.auth  # type: ignore
        return bool(request.method in SAFE_METHODS or user and user.is_authenticated)

from django.utils.encoding import force_str
from ninja_extra import status
from django.utils.translation import gettext_lazy as _
from ninja.errors import HttpError


class APIException(HttpError):
    """
    Subclasses should provide `.status_code` and `.message` properties.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = _("A server error occurred.")

    def __init__(self, message=None, status_code=None):
        self.message = message or self.message
        self.status_code = status_code or self.status_code
        super().__init__(status_code=self.status_code, message=self.message)

    def __str__(self):
        return self.message


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = _("Incorrect authentication credentials.")


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = _("Authentication credentials were not provided.")


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    message = _("You do not have permission to perform this action.")


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    message = _("Not found.")


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _('Method "{method}" not allowed.')

    def __init__(self, method, detail=None, code=None):
        if detail is None:
            detail = force_str(self.default_detail).format(method=method)
        super().__init__(status_code=code, message=detail)

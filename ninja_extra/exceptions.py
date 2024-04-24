"""
DRF Exceptions
"""

import math
from typing import Any, Dict, List, Optional, Type, Union, no_type_check

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from ninja.errors import HttpError

from ninja_extra import status


@no_type_check
def _get_error_details(
    data: Union[List, Dict, "ErrorDetail"],
    default_code: Optional[Union[str, int]] = None,
) -> Union[List["ErrorDetail"], "ErrorDetail", Dict[Any, "ErrorDetail"]]:
    """
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.
    """
    if isinstance(data, list):
        ret = [_get_error_details(item, default_code) for item in data]
        return ret
    elif isinstance(data, dict):
        ret = {
            key: _get_error_details(value, default_code) for key, value in data.items()
        }
        return ret

    text = force_str(data)
    code = getattr(data, "code", default_code)
    return ErrorDetail(text, code)


@no_type_check
def _get_codes(detail: Union[List, Dict, "ErrorDetail"]) -> Union[str, Dict]:
    if isinstance(detail, list):
        return [_get_codes(item) for item in detail]
    elif isinstance(detail, dict):
        return {key: _get_codes(value) for key, value in detail.items()}
    return detail.code


@no_type_check
def _get_full_details(detail: Union[List, Dict, "ErrorDetail"]) -> Dict:
    if isinstance(detail, list):
        return [_get_full_details(item) for item in detail]
    elif isinstance(detail, dict):
        return {key: _get_full_details(value) for key, value in detail.items()}
    return {"message": detail, "code": detail.code}


class ErrorDetail(str):
    """
    A string-like object that can additionally have a code.
    """

    code = None

    def __new__(
        cls, string: str, code: Optional[Union[str, int]] = None
    ) -> "ErrorDetail":
        self = super().__new__(cls, string)
        self.code = code
        return self

    def __eq__(self, other: object) -> bool:
        r = super().__eq__(other)
        try:
            return r and self.code == other.code  # type: ignore
        except AttributeError:
            return r

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return "ErrorDetail(string=%r, code=%r)" % (
            str(self),
            self.code,
        )

    def __hash__(self) -> Any:
        return hash(str(self))


class APIException(HttpError):
    """
    Base class for Django-Ninja-Extra exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("A server error occurred.")
    default_code = "error"

    def __init__(
        self,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
    ) -> None:
        if detail is None:
            detail = force_str(self.default_detail)
        if code is None:
            code = self.default_code

        self.detail = _get_error_details(detail, code)

    def __str__(self) -> str:
        return str(self.detail)

    def get_codes(self) -> Union[str, Dict[Any, Any]]:
        """
        Return only the code part of the error details.

        Eg. {"name": ["required"]}
        """
        return _get_codes(self.detail)  # type: ignore

    def get_full_details(self) -> Dict[Any, Any]:
        """
        Return both the message & code parts of the error details.

        Eg. {"name": [{"message": "This field is required.", "code": "required"}]}
        """
        return _get_full_details(self.detail)  # type: ignore


# The recommended style for using `ValidationError`,
# in order to minimize potential confusion with Django's
# built in `ValidationError`. For example:
#
# from ninja_extra import exceptions
# raise exceptions.ValidationError('Value was invalid')


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid input.")
    default_code = "invalid"

    def __init__(
        self,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
    ):
        if detail is None:
            detail = force_str(self.default_detail)
        if code is None:
            code = self.default_code

        # For validation failures, we may collect many errors together,
        # so the details should always be coerced to a list if not already.
        if not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]

        self.detail = _get_error_details(detail, code)


class ParseError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Malformed request.")
    default_code = "parse_error"


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Incorrect authentication credentials.")
    default_code = "authentication_failed"


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Authentication credentials were not provided.")
    default_code = "not_authenticated"


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("You do not have permission to perform this action.")
    default_code = "permission_denied"


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Not found.")
    default_code = "not_found"


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _('Method "{method}" not allowed.')
    default_code = "method_not_allowed"

    def __init__(
        self,
        method: str,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
    ):
        if detail is None:
            detail = force_str(self.default_detail).format(method=method)
        super().__init__(detail, code)


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = _("Could not satisfy the request Accept header.")
    default_code = "not_acceptable"

    def __init__(
        self,
        detail: Optional[Union[List, Dict, "ErrorDetail"]] = None,
        code: Optional[Union[str, int]] = None,
        available_renderers: Optional[str] = None,
    ):
        self.available_renderers = available_renderers
        super().__init__(detail, code)


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = _('Unsupported media type "{media_type}" in request.')
    default_code = "unsupported_media_type"

    def __init__(
        self,
        media_type: str,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
    ):
        if detail is None:
            detail = force_str(self.default_detail).format(media_type=media_type)
        super().__init__(detail, code)


class Throttled(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _("Request was throttled.")
    extra_detail_singular = _("Expected available in {wait} second.")
    extra_detail_plural = _("Expected available in {wait} seconds.")
    default_code = "throttled"

    def __init__(
        self,
        wait: Optional[float] = None,
        detail: Optional[Any] = None,
        code: Optional[Any] = None,
    ) -> None:
        if detail is None:
            detail = force_str(self.default_detail)
        if wait is not None:
            wait = math.ceil(wait)
            detail = " ".join(
                (
                    detail,
                    force_str(
                        ngettext(
                            self.extra_detail_singular.format(wait=wait),
                            self.extra_detail_plural.format(wait=wait),
                            wait,
                        )
                    ),
                )
            )
        self.wait = wait
        super().__init__(detail, code)


def server_error(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    """
    Generic 500 error handler.
    """
    data = {"error": "Server Error (500)"}
    return JsonResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def bad_request(
    request: HttpRequest, exception: Type[APIException], *args: Any, **kwargs: Any
) -> HttpResponse:
    """
    Generic 400 error handler.
    """
    data = {"error": "Bad Request (400)"}
    return JsonResponse(data, status=status.HTTP_400_BAD_REQUEST)

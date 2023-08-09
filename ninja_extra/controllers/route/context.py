from typing import Any, List, Optional, Union

from django.http import HttpResponse
from django.http.request import HttpRequest
from ninja.types import DictStrAny
from pydantic import BaseModel as PydanticModel
from pydantic import Field

from ninja_extra.types import PermissionType


class RouteContext(PydanticModel):
    """
    APIController Context which will be available to the class instance when handling request
    """

    class Config:
        arbitrary_types_allowed = True

    permission_classes: PermissionType = Field([])
    request: Union[Any, HttpRequest, None] = None
    response: Union[Any, HttpResponse, None] = None
    args: List[Any] = Field([])
    kwargs: DictStrAny = Field({})


def get_route_execution_context(
    request: HttpRequest,
    temporal_response: Optional[HttpResponse] = None,
    permission_classes: Optional[PermissionType] = None,
    *args: Any,
    **kwargs: Any,
) -> RouteContext:
    init_kwargs = {
        "permission_classes": permission_classes
        if permission_classes is not None
        else [],
        "request": request,
        "kwargs": kwargs,
        "response": temporal_response,
        "args": args,
    }
    context = RouteContext(**init_kwargs)  # type:ignore[arg-type]
    return context

from typing import Any, List, Union

from django.http.request import HttpRequest
from ninja.types import DictStrAny
from pydantic import BaseModel as PydanticModel, Field

from ninja_extra.types import PermissionType


class RouteContext(PydanticModel):
    class Config:
        arbitrary_types_allowed = True

    permission_classes: PermissionType = Field([])
    request: Union[Any, HttpRequest, None] = None
    args: List[Any] = Field([])
    kwargs: DictStrAny = Field({})

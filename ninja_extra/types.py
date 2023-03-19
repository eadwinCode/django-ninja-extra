from typing import Any, List, Type, Union

from ninja_extra.permissions.base import (
    BasePermission,
    OperandHolder,
    SingleOperandHolder,
)

PermissionType = List[
    Union[Type[BasePermission], OperandHolder, SingleOperandHolder, BasePermission, Any]
]

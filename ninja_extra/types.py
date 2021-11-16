from typing import List, Type, Union

from ninja_extra.permissions.base import (
    BasePermission,
    OperandHolder,
    SingleOperandHolder,
)

PermissionType = Union[
    List[Type[BasePermission]], List[OperandHolder], List[SingleOperandHolder]
]

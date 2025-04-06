from typing import Any, List, Type, Union

from ninja_extra.permissions.base import AsyncBasePermission, BasePermission

PermissionType = List[
    Union[
        Type[BasePermission],
        BasePermission,
        Any,
        Type[AsyncBasePermission],
        AsyncBasePermission,
    ]
]

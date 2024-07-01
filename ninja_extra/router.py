from typing import Any, Callable, Dict, List, Optional, Union, get_type_hints

from ninja.constants import NOT_SET, NOT_SET_TYPE
from ninja.router import Router as NinjaRouter
from ninja.throttling import BaseThrottle

from ninja_extra.operation import PathView

__all__ = ["Router"]


class Router(NinjaRouter):
    def __init__(
        self,
        *,
        auth: Any = NOT_SET,
        tags: Optional[List[str]] = None,
        throttle: Union[BaseThrottle, List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
    ) -> None:
        super().__init__(auth=auth, tags=tags, throttle=throttle)
        self.path_operations: Dict[str, PathView] = {}  # type: ignore

    def add_api_operation(
        self,
        path: str,
        methods: List[str],
        view_func: Callable,
        *,
        auth: Any = NOT_SET,
        throttle: Union[BaseThrottle, List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
        response: Any = NOT_SET,
        operation_id: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        deprecated: Optional[bool] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        url_name: Optional[str] = None,
        include_in_schema: bool = True,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if path not in self.path_operations:
            path_view = PathView()
            self.path_operations[path] = path_view
        else:
            path_view = self.path_operations[path]

        if response is NOT_SET:
            response = get_type_hints(view_func).get("return") or NOT_SET

        path_view.add_operation(
            path=path,
            throttle=throttle,
            methods=methods,
            view_func=view_func,
            auth=auth,
            response=response,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            url_name=url_name,
            include_in_schema=include_in_schema,
            openapi_extra=openapi_extra,
        )
        if self.api:
            path_view.set_api_instance(self.api, self)

        return None

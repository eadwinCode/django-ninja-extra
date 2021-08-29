from abc import ABC
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    cast,
)

from django.db.models import QuerySet
from django.urls import URLPattern, path as django_path

from ninja.constants import NOT_SET
from ninja.operation import PathView
from ninja.types import TCallable
from ninja.utils import normalize_path
from ninja_extra.controllers.controller_route.route import Route
from ninja_extra.permissions.mixins import NinjaExtraAPIPermissionMixin
from ninja_extra.controllers.mixins import ObjectControllerMixin, ListControllerMixin

if TYPE_CHECKING:
    from ninja import NinjaAPI
    from .controller_route.route_functions import RouteFunction


__all__ = ["APIController", "APIContext"]


class APIContext:
    request: Any
    object: Any
    object_list: List[Any]
    kwargs: Dict
    view_func: "RouteFunction"

    def __init__(self, data: Dict):
        self.__dict__ = data


class APIController(
    ABC,
    NinjaExtraAPIPermissionMixin,
    ObjectControllerMixin,
    ListControllerMixin
):
    _path_operations: Dict[str, PathView]
    api: Optional["NinjaAPI"]
    route_definition: Route = None
    queryset: QuerySet = None
    args = []
    kwargs = dict()

    @property
    def path_operations(self):
        return self._path_operations

    @classmethod
    def add_operation_from_route_definition(cls, route: Route):
        cls.add_api_operation(view_func=route.view_func, **route.route_params.dict())

    def __new__(cls, **kwargs):
        obj = super().__new__(cls)
        for k, v in kwargs.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj

    @classmethod
    def add_api_operation(
            cls,
            path: str,
            methods: List[str],
            view_func: Callable,
            *,
            auth: Any = NOT_SET,
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
    ) -> None:
        if path not in cls._path_operations:
            path_view = PathView()
            cls._path_operations[path] = path_view
        else:
            path_view = cls._path_operations[path]
        path_view.add_operation(
            path=path,
            methods=methods,
            view_func=view_func,
            auth=auth or cls.auth,
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
            include_in_schema=include_in_schema
        )
        return None

    def urls_paths(self, prefix: str) -> Iterator[URLPattern]:
        for path, path_view in self._path_operations.items():
            path = path.replace("{", "<").replace("}", ">")
            route = "/".join([i for i in (prefix, path) if i])
            # to skip lot of checks we simply treat double slash as a mistake:
            route = normalize_path(route)
            route = route.lstrip("/")

            yield django_path(
                route, path_view.get_view(), name=cast(str, path_view.url_name)
            )

    def set_api_instance(self, api: "NinjaAPI") -> None:
        self.api = api
        for path_view in self._path_operations.values():
            path_view.set_api_instance(self.api, self)

    def build_routers(self) -> List[Tuple[str, "APIController"]]:
        internal_routes = []
        return [(self.prefix, self), *internal_routes]

    def get_context(self, **kwargs):
        data = dict(request=self.request, kwargs=self.kwargs)
        data.update(**kwargs)
        return APIContext(data=data)

    def run_view_func(self, api_func: TCallable):
        return api_func(
            self, self.get_context(), *self.args, **self.kwargs
        )

    async def async_run_view_func(self, api_func: TCallable):
        return await api_func(
            self, self.get_context(), *self.args, **self.kwargs
        )

    def resolve_queryset(self, request_context: APIContext):
        if callable(self.queryset):
            return self.queryset(self, request_context)
        return self.queryset

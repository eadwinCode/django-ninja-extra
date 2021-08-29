from typing import TYPE_CHECKING, Callable, Any, Dict

from asgiref.sync import sync_to_async
from django.core.paginator import Page
from django.db.models import QuerySet
from ninja.constants import NOT_SET
from ninja.types import TCallable
from ninja_extra.controllers.controller_route.route import Route
from ninja_extra.pagination import BasePagination
from ninja_extra.shortcuts import get_object_or_404

if TYPE_CHECKING:
    from ninja_extra import APIContext

__all__ = ['ObjectControllerMixin', 'ListControllerMixin']


class ObjectControllerMixin:
    route_definition: Route
    get_context: Callable[..., "APIContext"]
    check_object_permissions: Callable[..., bool]
    resolve_queryset: Callable[..., QuerySet]
    kwargs: dict
    args: tuple
    request: Any

    def get_object(self, queryset: QuerySet):
        lookup_url_kwarg = self.route_definition.lookup_url_kwarg or self.route_definition.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected api_func to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                lookup_url_kwarg
        )

        filter_kwargs = {self.route_definition.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        return obj

    def run_object_view_func(self, api_func: TCallable):
        query_set = self.resolve_queryset(self.get_context())
        obj = self.get_object(queryset=query_set)
        obj_schema = None
        self.check_object_permissions(obj=obj)
        if self.route_definition.object_schema is not NOT_SET:
            obj_schema = self.route_definition.object_schema.from_django(obj)
        view_context = self.get_context(
            object=obj, serialized_object=obj_schema
        )
        return api_func(self, view_context, *self.args, **self.kwargs)

    async def async_run_object_view_func(self, api_func: TCallable):
        query_set = self.resolve_queryset(self.get_context())
        obj = await sync_to_async(self.get_object)(queryset=query_set)
        obj_schema = None
        self.check_object_permissions(obj=obj)
        if self.route_definition.object_schema is not NOT_SET:
            obj = await sync_to_async(self.route_definition.object_schema.from_django)(obj)
        view_context = self.get_context(
            object=obj, serialized_object=obj_schema
        )
        return api_func(self, view_context, *self.args, **self.kwargs)


class ListControllerMixin:
    route_definition: Route
    get_context: Callable[..., "APIContext"]
    _paginator: BasePagination
    pagination_class: BasePagination
    page_size: int
    max_page_size: int
    resolve_queryset: Callable[..., QuerySet]
    kwargs: dict
    args: tuple
    request: Any

    def resolve_paginator(self):
        return self.route_definition.create_paginator()

    @property
    def paginator(self) -> BasePagination:
        """
        The paginator instance associated with the view, or `None`.
        """
        return self._paginator

    def paginate_queryset(self, *, request, queryset: QuerySet) -> Page:
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        return self.paginator.paginate_queryset(queryset=queryset, request=request)

    def get_paginated_response(self, request, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        url = request.build_absolute_uri()
        return self.paginator.get_paginated_response(data=data, base_url=url)

    def run_list_view_func(self, api_func: TCallable):
        self.init_paginator()
        query_set = self.resolve_queryset(self.get_context())
        view_context = self.list_context(query_set=query_set)
        return api_func(self, view_context, *self.args, **self.kwargs)

    async def async_run_list_view_func(self, api_func: TCallable):
        self.init_paginator()
        query_set = self.resolve_queryset(
            self.get_context()
        )
        view_context = await self.list_context_async(query_set=query_set)
        return await api_func(self, view_context, *self.args, **self.kwargs)

    def init_paginator(self):
        self._paginator = self.resolve_paginator()

    def list_context(self, query_set: QuerySet):
        page = self.paginate_queryset(queryset=query_set, request=self.request)

        response_scheme = self.route_definition.object_schema

        schema_processed_data = response_scheme.from_django(page, many=True)
        response_data = self.get_paginated_response(data=schema_processed_data, request=self.request)

        response_schema_data = self.route_definition.route_params.response(**response_data)

        return self.get_context(
            view_func=self, page=page,
            object_list=response_schema_data
        )

    async def list_context_async(self, query_set: QuerySet):
        page = await sync_to_async(self.paginate_queryset)(queryset=query_set)

        response_scheme = self.route_definition.object_schema

        schema_processed_data = await sync_to_async(response_scheme.from_django)(page, many=True)
        response_data = self.get_paginated_response(data=schema_processed_data, request=self.request)

        response_schema = self.paginator.get_response_schema()
        response_schema_data = response_schema(**response_data)

        return self.get_context(
            view_func=self, page=page,
            object_list=response_schema_data
        )

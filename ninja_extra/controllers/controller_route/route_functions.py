import inspect
from functools import wraps
from typing import (
    Any,
    List,
    Dict, TYPE_CHECKING
)

from asgiref.sync import sync_to_async
from django.core.paginator import Page
from django.db.models import QuerySet
from ninja import Query
from ninja import params
from ninja.constants import NOT_SET
from ninja.signature import is_async
from ninja.types import TCallable

from ninja_extra.pagination import BasePagination
from ninja_extra.shortcuts import get_object_or_404

if TYPE_CHECKING:
    from .route import Route
    from ninja_extra.controllers.base import APIController

__all__ = ["RouteFunction", 'APIContext', 'PaginatedRouteFunction', 'RetrieveObjectRouteFunction']


class APIContext:
    request: Any
    object: Any
    object_list: List[Any]
    kwargs: Dict
    view_func: "RouteFunction"

    def __init__(self, data: Dict):
        self.__dict__ = data


class RouteFunction:
    def __call__(self, *args, **kwargs):
        pass

    def __init__(self, route_definition: "Route", api_func):
        self.route_definition = route_definition
        self.api_func = api_func

    @classmethod
    def get_context(cls, request, **kwargs):
        data = dict(request=request)
        data.update(**kwargs)
        return APIContext(data=data)

    @classmethod
    def get_required_api_func_signature(cls, api_func: TCallable):
        skip_parameters = ['context', 'self', 'request']
        sig_inspect = inspect.signature(api_func)
        sig_parameter = [
            parameter for parameter in sig_inspect.parameters.values()
            if parameter.name not in skip_parameters
        ]
        return sig_inspect, sig_parameter

    def _resolve_api_func_signature_(self, api_func, context_func):
        # Override signature
        sig_inspect, sig_parameter = self.get_required_api_func_signature(api_func)
        sig_replaced = sig_inspect.replace(parameters=sig_parameter)
        context_func.__signature__ = sig_replaced

        return context_func

    def __set_name__(self, owner, name):
        self.route_definition.owner = owner
        setattr(owner, name, self.api_func)
        add_from_route = getattr(owner, 'add_from_route', None)
        if add_from_route:
            add_from_route(self.route_definition)

    @classmethod
    def from_route(cls, api_func: TCallable, route_definition: "Route"):
        route_function = cls(route_definition=route_definition, api_func=api_func)
        if is_async(api_func):
            return route_function.convert_async_api_func_to_context_view(api_func=api_func), route_function
        return route_function.convert_api_func_to_context_view(api_func=api_func), route_function

    def convert_api_func_to_context_view(self, api_func: TCallable):
        @wraps(api_func)
        def context_func(request, *args, **kwargs):
            controller_instance = self.get_owner_instance()
            controller_instance.check_permissions(request)
            return self.run_view_func(*args, controller_instance=controller_instance, **kwargs)

        return self._resolve_api_func_signature_(api_func, context_func)

    def convert_async_api_func_to_context_view(
            self, api_func: TCallable
    ):
        @wraps(api_func)
        async def context_func(request, *args, **kwargs):
            controller_instance = self.get_owner_instance()
            controller_instance.check_permissions(request)
            return await self.async_run_view_func(*args, controller_instance=controller_instance, **kwargs)

        return self._resolve_api_func_signature_(api_func, context_func)

    def run_view_func(self, request, controller_instance, *args, **kwargs):
        return self.api_func(
            controller_instance, self.get_context(request), *args, **kwargs
        )

    async def async_run_view_func(self, request, controller_instance, *args, **kwargs):
        return await self.api_func(
            controller_instance, self.get_context(request), *args, **kwargs
        )

    def get_owner_instance(self):
        return self.route_definition.create_view_func_instance()


class RetrieveObjectRouteFunction(RouteFunction):
    def get_object(self, queryset: QuerySet, **kwargs):
        lookup_url_kwarg = self.route_definition.lookup_url_kwarg or self.route_definition.lookup_field

        assert lookup_url_kwarg in kwargs, (
            'Expected api_func to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            lookup_url_kwarg
        )

        filter_kwargs = {self.route_definition.lookup_field: kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        return obj

    def run_view_func(self, request, controller_instance: "APIController", *args, **kwargs):
        query_set = self.route_definition.resolve_queryset(
            controller_instance, request_context=self.get_context(request, kwargs=kwargs)
        )
        obj = self.get_object(queryset=query_set)
        obj_schema = None
        controller_instance.check_object_permissions(request, obj=obj)
        if self.route_definition.object_schema is not NOT_SET:
            obj_schema = self.route_definition.object_schema.from_django(obj)
        view_context = APIContext(
            dict(request=request, view=self, object=obj, kwargs=kwargs, serialized_object=obj_schema)
        )
        return self.api_func(controller_instance, view_context, *args, **kwargs)

    async def async_run_view_func(self, request, controller_instance: "APIController", *args, **kwargs):
        query_set = self.route_definition.resolve_queryset(
            controller_instance, request_context=self.get_context(request, kwargs=kwargs)
        )
        obj = await sync_to_async(self.get_object)(queryset=query_set)
        obj_schema = None
        controller_instance.check_object_permissions(request, obj=obj)
        if self.route_definition.object_schema is not NOT_SET:
            obj = await sync_to_async(self.route_definition.object_schema.from_django)(obj)
        view_context = APIContext(
            dict(request=request, view=self, object=obj, kwargs=kwargs, serialized_object=obj_schema)
        )
        return self.api_func(controller_instance, view_context, *args, **kwargs)


class PaginatedRouteFunction(RouteFunction):
    _paginator: None

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

    def _resolve_api_func_signature_(
            self, api_func, context_func
    ):
        route_definition: "Route" = self.route_definition
        # Override signature for Ninja API documentation purposes
        if not route_definition and not route_definition.pagination_class:
            raise Exception('route_definition with pagination_class is required')

        sig_inspect, required_func_signature = self.get_required_api_func_signature(api_func)
        # check if API func has any query params before injecting one.
        # Ninja api functions only allows on Query parameter
        has_query_param = any((type(param.default) == type(params.Query)
                              for param in required_func_signature))
        # if extract signatures are pass to the api_function, we ignore the
        if not has_query_param:
            query_params = inspect.Parameter(
                name='filters',
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=Query(...),
                annotation=route_definition.pagination_class.get_request_schema(),
            )
            required_func_signature.append(query_params)
        sig_replaced = sig_inspect.replace(parameters=required_func_signature)
        context_func.__signature__ = sig_replaced
        return context_func

    def run_view_func(self, request, controller_instance: "APIController", *args, **kwargs):
        self.init_paginator()
        query_set = self.route_definition.resolve_queryset(
            controller_instance, request_context=self.get_context(request, kwargs=kwargs)
        )
        view_context = self.list_context(
            query_set=query_set, request=request, **kwargs
        )
        return self.api_func(controller_instance, view_context, *args, **kwargs)

    async def async_run_view_func(self, request, controller_instance: "APIController", *args, **kwargs):
        self.init_paginator()
        query_set = self.route_definition.resolve_queryset(
            controller_instance, request_context=self.get_context(request, kwargs=kwargs)
        )
        view_context = await self.list_context_async(
            query_set=query_set, request=request, **kwargs
        )
        return await self.api_func(controller_instance, view_context, *args, **kwargs)

    def init_paginator(self):
        self._paginator = self.route_definition.get_paginator()

    def list_context(self, request, query_set: QuerySet, **kwargs):
        page = self.paginate_queryset(queryset=query_set, request=request)

        response_scheme = self.route_definition.object_schema

        schema_processed_data = response_scheme.from_django(page, many=True)
        response_data = self.get_paginated_response(data=schema_processed_data, request=request)

        response_schema = self.paginator.get_response_schema()
        response_schema_data = response_schema(**response_data)

        return self.get_context(
            request, view_func=self, page=page,
            object_list=response_schema_data, kwargs=kwargs
        )

    async def list_context_async(self, request, query_set: QuerySet, **kwargs):
        page = await sync_to_async(self.paginate_queryset)(queryset=query_set)

        response_scheme = self.route_definition.object_schema

        schema_processed_data = await sync_to_async(response_scheme.from_django)(page, many=True)
        response_data = self.get_paginated_response(data=schema_processed_data, request=request)

        response_schema = self.paginator.get_response_schema()
        response_schema_data = response_schema(**response_data)

        return self.get_context(
            request, view_func=self, page=page,
            object_list=response_schema_data, kwargs=kwargs
        )

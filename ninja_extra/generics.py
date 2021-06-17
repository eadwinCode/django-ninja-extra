import inspect
from abc import ABC, abstractmethod
from functools import wraps
from collections import namedtuple
from typing import Dict

from django.core.paginator import Page
from ninja import Query
from ninja.signature import is_async
from ninja.types import TCallable

from ninja_extra.databases import DatabaseQuerySet, AsyncDatabaseQuerySet
from ninja_extra.pagination import PageNumberPagination, BasePagination
from ninja_extra.permissions.mixins import NinjaExtraAPIPermissionMixin


__all__ = ['GenericAPIView', 'GenericPaginatedAPIView', 'GenericBaseAPIView']


class GenericBaseAPIView(ABC):
    def __new__(cls, request, *args, **kwargs):
        context_view_instance = cls(request, *args, **kwargs)
        return context_view_instance.handle_request(*args)

    @classmethod
    async def __async_new__(cls, request, *args, **kwargs):
        context_view_instance = super().__new__(
            cls, request, *args, database_query=AsyncDatabaseQuerySet, **kwargs
        )
        return await context_view_instance.async_handle_request(*args)

    @property
    def api_func(self) -> TCallable:
        raise NotImplementedError()

    @classmethod
    def get_context_view(cls, api_func: TCallable):
        context_view_dto = namedtuple('context_view_dto', ['context_view', 'context_conversion_view'])
        if is_async(api_func):
            return context_view_dto(
                context_view=cls.__async_new__,
                context_conversion_view=cls.convert_async_api_func_to_context_view
            )
        return context_view_dto(
            context_view=cls.__new__,
            context_conversion_view=cls.convert_api_func_to_context_view
        )

    @classmethod
    def get_required_api_func_signature(cls, api_func: TCallable):
        skip_parameters = ['context', 'request', 'self']
        func_signature = namedtuple(
            'func_signature', ['func_signatures', 'required_func_signature']
        )
        sig = inspect.signature(api_func)
        sig_parameter = [
            parameter for parameter in sig.parameters.values()
            if parameter.name not in skip_parameters
        ]
        return func_signature(func_signatures=sig, required_func_signature=sig_parameter)

    @classmethod
    def __resolve_api_func_signature(cls, api_func, context_func, **options):
        # Override signature
        func_parameters = cls.get_required_api_func_signature(api_func)
        api_func_parameters = func_parameters.func_signatures
        sig_replaced = api_func_parameters.replace(parameters=func_parameters.required_func_signature)
        context_func.__signature__ = sig_replaced

        return context_func

    @classmethod
    def convert_api_func_to_context_view(
            cls, api_func: TCallable, *, context_view: TCallable, **options
    ):
        @wraps(api_func)
        def context_func(*args, **kwargs):
            return context_view(*args, **kwargs)

        return cls.__resolve_api_func_signature(api_func, context_func)

    @classmethod
    def convert_async_api_func_to_context_view(
            cls, api_func: TCallable, *, context_view: TCallable, **options
    ):
        @wraps(api_func)
        async def context_func(*args, **kwargs):
            return await context_view(*args, **kwargs)

        return cls.__resolve_api_func_signature(api_func, context_func)

    @abstractmethod
    def handle_request(self, *args):
        pass

    @abstractmethod
    async def async_handle_request(self, *args):
        pass


class GenericAPIView(GenericBaseAPIView, NinjaExtraAPIPermissionMixin):
    """
    Base class for all other generic views.
    """

    def __init__(
            self,
            request,
            *,
            queryset,
            permission_classes=None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            database_query=DatabaseQuerySet,
            **kwargs
    ):
        super(GenericAPIView, self).__init__()
        self.request = request
        self.database_query = database_query(self, queryset)
        self.permission_classes = permission_classes or self.permission_classes
        self.lookup_field = lookup_field
        self.lookup_url_kwarg = lookup_url_kwarg
        self.kwargs = kwargs


class GenericPaginatedAPIView(GenericAPIView):

    def __init__(self, *args, pagination_class=None, page_size=50, **kwargs):
        super(GenericPaginatedAPIView, self).__init__(*args, **kwargs)
        self._paginator = PageNumberPagination(page_size=page_size)
        if pagination_class:
            self._paginator = pagination_class(page_size=page_size)

    @property
    def paginator(self) -> BasePagination:
        """
        The paginator instance associated with the view, or `None`.
        """
        return self._paginator

    def paginate_queryset(self, queryset) -> Page:
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        return self.paginator.paginate_queryset(queryset=queryset, request=self.request)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        url = self.request.build_absolute_uri()
        return self.paginator.get_paginated_response(data=data, base_url=url)

    @classmethod
    def __resolve_api_func_signature(cls, api_func, context_func, pagination_class: BasePagination = None, **options):
        # Override signature
        query_params = inspect.Parameter(
            name='filters',
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=Query(...),
            annotation=pagination_class.get_request_schema(),
        )

        func_parameters = cls.get_required_api_func_signature(api_func)
        api_func_parameters = func_parameters.func_signatures

        if not func_parameters.required_func_signature:
            func_parameters.required_func_signature.append(query_params)
            sig_replaced = api_func_parameters.replace(parameters=func_parameters.required_func_signature)
            context_func.__signature__ = sig_replaced
        return context_func

    @classmethod
    def convert_api_func_to_context_view(
            cls, api_func: TCallable, *, context_view: TCallable, pagination_class: BasePagination = None, **options
    ):
        if not pagination_class:
            raise Exception('pagination_class is required')

        @wraps(api_func)
        def context_func(*args, filters=None, **kwargs):
            return context_view(*args, **kwargs)

        return cls.__resolve_api_func_signature(api_func, context_func, pagination_class=pagination_class)

    @classmethod
    def convert_async_api_func_to_context_view(
            cls, api_func: TCallable, *, context_view: TCallable, pagination_class: BasePagination = None, **options
    ):
        if not pagination_class:
            raise Exception('pagination_class is required')

        @wraps(api_func)
        async def context_func(*args, filters=None, **kwargs):
            return await context_view(*args, **kwargs)

        return cls.__resolve_api_func_signature(api_func, context_func, pagination_class=pagination_class)

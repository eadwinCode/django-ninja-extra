from typing import Any, Dict, Union

from asgiref.sync import sync_to_async
from ninja.constants import NOT_SET
from ninja.types import TCallable
from ninja_extra import GenericAPIView, GenericPaginatedAPIView
from ninja_extra.schemas import PaginatedResponseSchema


class APIContext:
    request: Any
    object: Any
    object_list: PaginatedResponseSchema[Any]
    kwargs: Dict
    view: Union[GenericAPIView]

    def __init__(self, data: Dict):
        self.__dict__ = data


class ObjectBaseAPIView(GenericAPIView):
    def __init__(
            self,
            request,
            *,
            api_func,
            query_set,
            permission_classes=None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            response: Any = NOT_SET,
            **kwargs
    ):
        super(ObjectBaseAPIView, self).__init__(
            request=request,
            queryset=query_set,
            permission_classes=permission_classes,
            lookup_field=lookup_field,
            lookup_url_kwarg=lookup_url_kwarg,
            **kwargs
        )
        self._api_func = api_func
        self.response_scheme = response

    @property
    def api_func(self) -> TCallable:
        return self._api_func


class ObjectAPIView(ObjectBaseAPIView):
    def handle_request(self, *args):
        self.check_permissions(self.request)
        obj = self.database_query.get_object(context_view=self)

        self.check_object_permissions(self.request, obj=obj)
        if self.response_scheme is not NOT_SET:
            obj = self.response_scheme.from_django(obj)
        view_context = APIContext(
            dict(request=self.request, view=self, object=obj, kwargs=self.kwargs)
        )
        return self.api_func(view_context, *args, **self.kwargs)

    async def async_handle_request(self, *args):
        self.check_permissions(self.request)
        obj = await self.database_query.get_object(context_view=self)

        self.check_object_permissions(self.request, obj=obj)
        if self.response_scheme is not NOT_SET:
            obj = await sync_to_async(self.response_scheme.from_django)(obj)

        view_context = APIContext(
            dict(request=self.request, view=self, object=obj, kwargs=self.kwargs)
        )
        return await self.api_func(view_context, *args, **self.kwargs)


class ListBaseAPIView(GenericPaginatedAPIView):
    def __init__(
            self,
            request,
            *,
            api_func,
            query_set,
            permission_classes=None,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            pagination_class=None,
            page_size=50,
            response: Any = NOT_SET,
            **kwargs
    ):
        super(ListBaseAPIView, self).__init__(
            pagination_class=pagination_class,
            page_size=page_size,
            request=request,
            queryset=query_set,
            permission_classes=permission_classes,
            lookup_field=lookup_field,
            lookup_url_kwarg=lookup_url_kwarg,
            **kwargs
        )
        self._api_func = api_func
        self.response_scheme = response

    @property
    def api_func(self) -> TCallable:
        return self._api_func

    async def async_handle_request(self, *args):
        return await self.list_async(*args)

    def handle_request(self, *args):
        return self.list(*args)

    def list(self, *args):
        raise NotImplementedError('')

    def list_async(self, *args):
        raise NotImplementedError('')


class ListAPIView(ListBaseAPIView):

    def list(self, *args):
        self.check_permissions(self.request)
        queryset = self.database_query.get_queryset()
        page = self.paginate_queryset(queryset)

        schema_processed_data = self.response_scheme.from_django(page, many=True)
        response_data = self.get_paginated_response(schema_processed_data)
        response_schema = self.paginator.get_response_schema()
        response_schema_data = response_schema(**response_data)

        view_context = APIContext(
            dict(request=self.request, view=self, object_list=response_schema_data, kwargs=self.kwargs)
        )
        return self.api_func(view_context, *args, **self.kwargs)

    async def list_async(self, *args):
        self.check_permissions(self.request)
        queryset = self.database_query.get_queryset()
        page = await sync_to_async(self.paginate_queryset)(queryset)

        schema_processed_data = await sync_to_async(self.response_scheme.from_django)(page, many=True)
        response_data = self.get_paginated_response(schema_processed_data)
        response_schema = self.paginator.get_response_schema()
        response_schema_data = response_schema(**response_data)

        view_context = APIContext(
            dict(request=self.request, view=self, object_list=response_schema_data, kwargs=self.kwargs)
        )
        return await self.api_func(view_context, *args, **self.kwargs)

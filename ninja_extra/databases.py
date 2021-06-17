import inspect
from typing import Union, Callable, Dict, TYPE_CHECKING
from asgiref.sync import sync_to_async
from django.db.models.query import QuerySet
from ninja_extra.shortcuts import get_object_or_404


class DatabaseQuerySet:
    def __init__(
            self, route_definition,
            queryset: Union[QuerySet, Callable], kwargs: Dict
    ):
        self._queryset = queryset
        self.route_definition = route_definition
        self.kwargs = kwargs

    def get_queryset(self):
        queryset = self._queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset

    def _find_object(self, **filter_kwargs):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, **filter_kwargs)

        return obj

    def get_object(self):
        # Perform the lookup filtering.
        lookup_url_kwarg = self.route_definition.lookup_url_kwarg or self.route_definition.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected api_func to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            lookup_url_kwarg
        )

        filter_kwargs = {self.route_definition.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = self._find_object(**filter_kwargs)
        return obj


class AsyncDatabaseQuerySet(DatabaseQuerySet):
    def __init__(self, *args, **kwargs):
        super(AsyncDatabaseQuerySet, self).__init__(*args, **kwargs)
        self._find_object = sync_to_async(self._find_object)

    async def get_object(self):
        # Perform the lookup filtering.
        lookup_url_kwarg = self.route_definition.lookup_url_kwarg or self.route_definition.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected api_func to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            lookup_url_kwarg
        )

        filter_kwargs = {self.route_definition.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = await self._find_object(**filter_kwargs)
        return obj

import sys
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List, Union, Dict

from django.core.paginator import Paginator, InvalidPage
from django.db.models import QuerySet

from ninja_extra.exceptions import NotFound
from ninja_extra.schemas import PaginatedFilters, PaginatedResponseSchema, get_paginated_response_schema
from ninja_extra.urls import replace_query_param, remove_query_param


def _positive_int(integer_string, strict=False, cutoff=None):
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret < 0 or (ret == 0 and strict):
        raise ValueError()
    if cutoff:
        return min(ret, cutoff)
    return ret


class BasePagination(ABC):
    @abstractmethod
    def paginate_queryset(self, *, queryset: QuerySet, request):  # pragma: no cover
        raise NotImplementedError('paginate_queryset() must be implemented.')

    @abstractmethod
    def get_paginated_response(self, *, data: Union[List, Dict], base_url: str):  # pragma: no cover
        raise NotImplementedError('get_paginated_response() must be implemented.')

    @abstractmethod
    def get_page_size(self, request):
        raise NotImplementedError('get_page_size() must be implemented.')

    @classmethod
    @abstractmethod
    def get_request_schema(cls):
        raise NotImplementedError('get_request_schema() must be implemented.')

    @classmethod
    @abstractmethod
    def get_response_schema(cls):
        raise NotImplementedError('get_response_schema() must be implemented.')


class PageNumberPagination(BasePagination):
    page = None
    paginator_class = Paginator

    # Client can control the page using this query parameter.
    page_query_param = 'page'

    # Client can control the page size using this query parameter.
    # Default is 'None'. Set to eg 'page_size' to enable usage.
    page_size_query_param = 'page_size'

    # Set to an integer to limit the maximum page size the client may request.
    # Only relevant if 'page_size_query_param' has also been set.
    max_page_size = 100

    last_page_strings = ('last',)

    def __init__(self, page_size=20, max_page_size=50, page_query_param='page'):
        self.page_size = page_size
        self.max_page_size = max_page_size
        self.page_query_param = page_query_param

    def paginate_queryset(self, *, queryset, request):
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.paginator_class(queryset, page_size)
        page_number = request.GET.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = 'Invalid page. {page_number} {message}'.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        return self.page

    def get_paginated_response(self, *, data, base_url):
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link(base_url)),
            ('previous', self.get_previous_link(base_url)),
            ('results', data)
        ])

    def get_next_link(self, url: str):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self, url: str):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.GET[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size

    @classmethod
    def get_request_schema(cls):
        return PaginatedFilters

    @classmethod
    def get_response_schema(cls):
        if sys.version_info >= (3, 8):
            return PaginatedResponseSchema
        return get_paginated_response_schema

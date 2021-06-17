from functools import wraps, partial
from typing import Optional, Any, List, Dict
from ninja import Router as NinjaAPIRouter

from ninja.constants import NOT_SET
from ninja.types import Decorator, TCallable

from ninja_extra.pagination import BasePagination, PageNumberPagination
from ninja_extra.views import ObjectAPIView, ObjectBaseAPIView, ListAPIView, ListBaseAPIView

__all__ = ['Router']


class Router(NinjaAPIRouter):
    def __init__(
            self, *, permissions=None, pagination_class=None, query_set=None,
            auth: Any = NOT_SET, tags: Optional[List[str]] = None
    ):
        super().__init__(auth=auth, tags=tags)
        self.permissions = permissions or []
        self.pagination_class = pagination_class
        self.query_set = query_set

    def retrieve(
            self,
            *args,
            permissions=None,
            query_set=None,
            view_class: ObjectBaseAPIView = ObjectAPIView,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            response: Any = NOT_SET,
            **kwargs
    ) -> Decorator:
        router_decorator = super().get(*args, response=response, **kwargs)

        def decorator(api_func: TCallable):
            context_view_dto = view_class.get_context_view(api_func=api_func)
            api_view = partial(
                context_view_dto.context_view,
                api_func=api_func,
                query_set=query_set or self.query_set,
                permission_classes=permissions or self.permissions,
                lookup_field=lookup_field,
                response=response,
                lookup_url_kwarg=lookup_url_kwarg
            )
            context_api_func = context_view_dto.context_conversion_view(api_func, context_view=api_view)
            return router_decorator(context_api_func)

        return decorator

    def update(
            self,
            *args,
            permissions=None,
            query_set=None,
            view_class: ObjectBaseAPIView = ObjectAPIView,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            response: Any = NOT_SET,
            **kwargs
    ) -> Decorator:
        router_decorator = super().put(*args, response=response, **kwargs)

        def decorator(api_func: TCallable):
            context_view_dto = view_class.get_context_view(api_func=api_func)
            api_view = partial(
                context_view_dto.context_view,
                api_func=api_func,
                query_set=query_set or self.query_set,
                permission_classes=permissions or self.permissions,
                lookup_field=lookup_field,
                response=response,
                lookup_url_kwarg=lookup_url_kwarg
            )
            context_api_func = context_view_dto.context_conversion_view(api_func, context_view=api_view)
            return router_decorator(context_api_func)

        return decorator

    def patch_update(
            self,
            *args,
            permissions=None,
            query_set=None,
            view_class: ObjectBaseAPIView = ObjectAPIView,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            response: Any = NOT_SET,
            **kwargs
    ) -> Decorator:
        router_decorator = super().patch(*args, response=response, **kwargs)

        def decorator(api_func: TCallable):
            context_view_dto = view_class.get_context_view(api_func=api_func)
            api_view = partial(
                context_view_dto.context_view,
                api_func=api_func,
                query_set=query_set or self.query_set,
                permission_classes=permissions or self.permissions,
                lookup_field=lookup_field,
                response=response,
                lookup_url_kwarg=lookup_url_kwarg
            )
            context_api_func = context_view_dto.context_conversion_view(api_func, context_view=api_view)
            return router_decorator(context_api_func)

        return decorator

    def delete(
            self,
            *args,
            permissions=None,
            query_set=None,
            view_class: ObjectBaseAPIView = ObjectAPIView,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            response: Any = NOT_SET,
            **kwargs
    ) -> Decorator:
        router_decorator = super().delete(*args, response=response, **kwargs)

        def decorator(api_func: TCallable):
            context_view_dto = view_class.get_context_view(api_func=api_func)
            api_view = partial(
                context_view_dto.context_view,
                api_func=api_func,
                query_set=query_set or self.query_set,
                permission_classes=permissions or self.permissions,
                lookup_field=lookup_field,
                response=response,
                lookup_url_kwarg=lookup_url_kwarg
            )
            context_api_func = context_view_dto.context_conversion_view(api_func, context_view=api_view)
            return router_decorator(context_api_func)

        return decorator

    def list(
            self,
            *args,
            permissions=None,
            query_set=None,
            view_class: ListBaseAPIView = ListAPIView,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            pagination_class: BasePagination = PageNumberPagination,
            page_size=50,
            response: Any = NOT_SET,
            **kwargs
    ) -> Decorator:
        response_schema = pagination_class.get_response_schema()
        router_decorator = super().get(*args, response=response_schema[response], **kwargs)

        def decorator(api_func: TCallable):
            context_view_dto = view_class.get_context_view(api_func=api_func)
            api_view = partial(
                context_view_dto.context_view,
                api_func=api_func,
                query_set=query_set or self.query_set,
                permission_classes=permissions or self.permissions,
                lookup_field=lookup_field,
                lookup_url_kwarg=lookup_url_kwarg,
                response=response,
                pagination_class=pagination_class or self.pagination_class,
                page_size=page_size
            )
            context_api_func = context_view_dto.context_conversion_view(
                api_func, context_view=api_view, pagination_class=PageNumberPagination
            )
            return router_decorator(context_api_func)

        return decorator

    def create(
            self,
            *args,
            permissions=None,
            query_set=None,
            view_class: ObjectBaseAPIView = ObjectAPIView,
            lookup_field: str = 'pk',
            lookup_url_kwarg: Dict = None,
            response: Any = NOT_SET,
            **kwargs
    ) -> Decorator:
        router_decorator = super().post(*args, response=response, **kwargs)

        def decorator(api_func: TCallable):
            context_view_dto = view_class.get_context_view(api_func=api_func)
            api_view = partial(
                context_view_dto.context_view,
                api_func=api_func,
                query_set=query_set or self.query_set,
                permission_classes=permissions or self.permissions,
                lookup_field=lookup_field,
                response=response,
                lookup_url_kwarg=lookup_url_kwarg
            )
            context_api_func = context_view_dto.context_conversion_view(api_func, context_view=api_view)
            return router_decorator(context_api_func)
        return decorator

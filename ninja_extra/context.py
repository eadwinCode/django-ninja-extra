import typing as t

import pydantic
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.http.request import HttpRequest
from ninja.errors import ValidationError
from ninja.types import DictStrAny

from ninja_extra.interfaces.route_context import RouteContextBase
from ninja_extra.lazy import settings_lazy
from ninja_extra.types import PermissionType

if t.TYPE_CHECKING:
    from ninja_extra.details import ViewSignature
    from ninja_extra.main import NinjaExtraAPI


class RouteContext(RouteContextBase):
    """
    APIController Context which will be available to the class instance when handling request
    """

    __slots__ = [
        "permission_classes",
        "request",
        "response",
        "args",
        "kwargs",
        "_api",
        "_view_signature",
        "_has_computed_route_parameters",
    ]

    permission_classes: PermissionType
    request: t.Union[t.Any, HttpRequest, None]
    response: t.Union[t.Any, HttpResponse, None]
    args: t.List[t.Any]
    kwargs: DictStrAny

    def __init__(
        self,
        request: HttpRequest,
        args: t.Optional[t.List[t.Any]] = None,
        permission_classes: t.Optional[PermissionType] = None,
        kwargs: t.Optional[DictStrAny] = None,
        response: t.Optional[HttpResponse] = None,
        api: t.Optional["NinjaExtraAPI"] = None,
        view_signature: t.Optional["ViewSignature"] = None,
    ):
        self.request = request
        self.response = response
        self.args: t.List[t.Any] = args or []
        self.kwargs: DictStrAny = kwargs or {}
        self.kwargs.update({"view_func_kwargs": {}})
        self.permission_classes: PermissionType = permission_classes or []
        self._api = api
        self._view_signature = view_signature
        self._has_computed_route_parameters = False

    @property
    def has_computed_route_parameters(self) -> bool:
        return self._has_computed_route_parameters

    def compute_route_parameters(
        self,
    ) -> None:
        if self._view_signature is None or self._api is None:
            raise ImproperlyConfigured(
                "view_signature and api are required. "
                "Or you are taking an approach that is not supported "
                "RouteContext to compute route parameters."
            )

        if self._has_computed_route_parameters:
            return

        values, errors = {}, []
        for model in self._view_signature.models:
            try:
                data = model.resolve(self.request, self._api, self.kwargs)
                values.update(data)
            except pydantic.ValidationError as e:
                items = []
                for i in e.errors(include_url=False):
                    i["loc"] = (
                        model.__ninja_param_source__,
                    ) + model.__ninja_flatten_map_reverse__.get(i["loc"], i["loc"])
                    # removing pydantic hints
                    del i["input"]  # type: ignore
                    if (
                        "ctx" in i
                        and "error" in i["ctx"]
                        and isinstance(i["ctx"]["error"], Exception)
                    ):
                        i["ctx"]["error"] = str(i["ctx"]["error"])
                    items.append(dict(i))
                errors.extend(items)

        if errors:
            raise ValidationError(errors)

        if self._view_signature.response_arg:
            values[self._view_signature.response_arg] = self.response

        self.kwargs.update({"view_func_kwargs": values}, **values)
        self._has_computed_route_parameters = True


def get_route_execution_context(
    request: HttpRequest,
    temporal_response: t.Optional[HttpResponse] = None,
    permission_classes: t.Optional[PermissionType] = None,
    api: t.Optional["NinjaExtraAPI"] = None,
    view_signature: t.Optional["ViewSignature"] = None,
    *args: t.Any,
    **kwargs: t.Any,
) -> RouteContext:
    init_kwargs = {
        "permission_classes": permission_classes
        if permission_classes is not None
        else [],
        "request": request,
        "kwargs": kwargs,
        "response": temporal_response,
        "args": args,
        "api": api,
        "view_signature": view_signature,
    }
    context_class = t.cast(
        t.Type[RouteContext],
        settings_lazy().ROUTE_CONTEXT_CLASS,
    )
    context = context_class(**init_kwargs)  # type:ignore[arg-type]
    return context

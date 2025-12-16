import typing as t
import warnings
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, URLResolver
from django.utils.module_loading import import_string, module_has_submodule
from ninja import NinjaAPI
from ninja.constants import NOT_SET
from ninja.openapi.docs import DocsBase, Swagger
from ninja.parser import Parser
from ninja.renderers import BaseRenderer
from ninja.throttling import BaseThrottle
from ninja.types import DictStrAny, TCallable

from ninja_extra import exceptions, router
from ninja_extra.compatible import NOT_SET_TYPE
from ninja_extra.constants import API_CONTROLLER_INSTANCE
from ninja_extra.controllers.base import APIController, ControllerBase
from ninja_extra.controllers.registry import controller_registry

__all__ = [
    "NinjaExtraAPI",
]

from ninja_extra.reflect import reflect


class NinjaExtraAPI(NinjaAPI):
    def __init__(
        self,
        *,
        title: str = "NinjaExtraAPI",
        version: str = "1.0.0",
        description: str = "",
        openapi_url: t.Optional[str] = "/openapi.json",
        docs: DocsBase = Swagger(),
        docs_url: t.Optional[str] = "/docs",
        docs_decorator: t.Optional[t.Callable[[TCallable], TCallable]] = None,
        servers: t.Optional[t.List[DictStrAny]] = None,
        urls_namespace: t.Optional[str] = None,
        csrf: bool = False,
        auth: t.Optional[
            t.Union[t.Sequence[t.Callable], t.Callable, NOT_SET_TYPE]
        ] = NOT_SET,
        throttle: t.Union[BaseThrottle, t.List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
        renderer: t.Optional[BaseRenderer] = None,
        parser: t.Optional[Parser] = None,
        openapi_extra: t.Optional[t.Dict[str, t.Any]] = None,
        app_name: str = "ninja",
        **kwargs: t.Any,
    ) -> None:
        # add a warning if there csrf is True
        if csrf:
            (
                warnings.warn(
                    (
                        "CSRF is deprecated and will be removed in a future version"
                        "see https://django-ninja.dev/reference/csrf for more details."
                    ),
                    DeprecationWarning,
                    stacklevel=2,
                ),
            )
        super(NinjaExtraAPI, self).__init__(
            title=title,
            version=version,
            description=description,
            openapi_url=openapi_url,
            docs_url=docs_url,
            urls_namespace=urls_namespace,
            auth=auth,
            renderer=renderer,
            parser=parser,
            openapi_extra=openapi_extra,
            servers=servers,
            docs=docs,
            docs_decorator=docs_decorator,
            throttle=throttle,
            **kwargs,
        )
        self.app_name = app_name
        self.exception_handler(exceptions.APIException)(self.api_exception_handler)
        self._routers: t.List[t.Tuple[str, router.Router]] = []  # type: ignore
        self.default_router = router.Router()
        self.add_router("", self.default_router)

    def api_exception_handler(
        self, request: HttpRequest, exc: exceptions.APIException
    ) -> HttpResponse:
        headers: t.Dict = {}
        if isinstance(exc, exceptions.Throttled):
            headers["Retry-After"] = "%d" % float(exc.wait or 0.0)

        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {"detail": exc.detail}

        response = self.create_response(request, data, status=exc.status_code)
        for k, v in headers.items():
            response.setdefault(k, v)

        return response

    @property
    def urls(self) -> t.Tuple[t.List[t.Union[URLResolver, URLPattern]], str, str]:
        _url_tuple = super().urls
        return (
            _url_tuple[0],
            self.app_name,
            str(_url_tuple[len(_url_tuple) - 1]),
        )

    def register_controllers(
        self, *controllers: t.Union[t.Type[ControllerBase], t.Type, str]
    ) -> None:
        for controller in controllers:
            if isinstance(controller, str):
                controller = t.cast(
                    t.Union[t.Type[ControllerBase], t.Type], import_string(controller)
                )

            if not issubclass(controller, ControllerBase):
                raise ImproperlyConfigured(
                    f"{controller.__class__.__name__} class is not a controller"
                )
            api_controller = t.cast(
                APIController,
                reflect.get_metadata_or_raise_exception(
                    API_CONTROLLER_INSTANCE, controller
                ),
            )
            if not api_controller.is_registered(self):
                self._routers.extend(api_controller.build_routers())  # type: ignore
                api_controller.set_api_instance(self)

    def auto_discover_controllers(self) -> None:
        from django.apps import apps

        installed_apps = [
            v for k, v in apps.app_configs.items() if not v.name.startswith("django.")
        ]
        possible_module_name = ["api", "controllers"]

        for app_module in installed_apps:
            try:
                app_module_ = import_module(app_module.name)
                for module in possible_module_name:
                    if module_has_submodule(app_module_, module):
                        mod_path = "%s.%s" % (app_module.name, module)
                        import_module(mod_path)
                self.register_controllers(
                    *controller_registry.get_controllers().values()
                )
            except ImportError as ex:  # pragma: no cover
                raise ex

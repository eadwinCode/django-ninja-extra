from importlib import import_module
from typing import Callable, List, Optional, Sequence, Tuple, Type, Union

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, URLResolver
from django.utils.module_loading import module_has_submodule
from ninja import NinjaAPI
from ninja.constants import NOT_SET
from ninja.parser import Parser
from ninja.renderers import BaseRenderer

from ninja_extra import exceptions
from ninja_extra.controllers.base import APIController
from ninja_extra.controllers.router import ControllerRegistry, ControllerRouter

__all__ = [
    "NinjaExtraAPI",
]


class NinjaExtraAPI(NinjaAPI):
    def __init__(
        self,
        *,
        title: str = "NinjaExtraAPI",
        version: str = "1.0.0",
        description: str = "",
        openapi_url: Optional[str] = "/openapi.json",
        docs_url: Optional[str] = "/docs",
        urls_namespace: Optional[str] = None,
        csrf: bool = False,
        auth: Union[Sequence[Callable], Callable, object] = NOT_SET,
        renderer: Optional[BaseRenderer] = None,
        parser: Optional[Parser] = None,
        app_name: str = "ninja",
    ) -> None:
        super(NinjaExtraAPI, self).__init__(
            title=title,
            version=version,
            description=description,
            openapi_url=openapi_url,
            docs_url=docs_url,
            urls_namespace=urls_namespace,
            csrf=csrf,
            auth=auth,
            renderer=renderer,
            parser=parser,
        )
        self.app_name = app_name
        self.exception_handler(exceptions.APIException)(self.api_exception_handler)

    def api_exception_handler(
        self, request: HttpRequest, exc: exceptions.APIException
    ) -> HttpResponse:
        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {"detail": exc.detail}

        return self.create_response(request, data, status=exc.status_code)

    @property
    def urls(self) -> Tuple[List[Union[URLResolver, URLPattern]], str, str]:
        _url_tuple = super().urls
        return (
            _url_tuple[0],
            self.app_name,
            str(_url_tuple[len(_url_tuple) - 1]),
        )

    def register_controllers(self, *controllers: Type[APIController]) -> None:
        for controller in controllers:
            if not issubclass(controller, APIController):
                raise ImproperlyConfigured(
                    f"{controller.__class__.__name__} class is not a controller"
                )
            controller_ninja_router = controller.get_router()
            if not controller.registered and controller_ninja_router:
                self._routers.extend(controller_ninja_router.build_routers())  # type: ignore
                controller_ninja_router.set_api_instance(self)
                controller.registered = True

    def add_controller_router(
        self, *routers: Union[ControllerRouter, Type[ControllerRouter]]
    ) -> None:
        for router in routers:
            if not isinstance(router, ControllerRouter):
                raise ImproperlyConfigured(
                    f"{router.__class__.__name__} class is not a ControllerRouter"
                )
            if not router.controller:
                raise ImproperlyConfigured(
                    f"{router.__class__.__name__} has no controller"
                )
            self.register_controllers(router.controller)

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
                    *ControllerRegistry.get_controllers().values()
                )
            except ImportError as ex:
                raise ex

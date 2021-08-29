from importlib import import_module
from typing import Optional, Union, Sequence, Callable
from django.utils.module_loading import module_has_submodule
from ninja import NinjaAPI
from ninja.constants import NOT_SET
from ninja.parser import Parser
from ninja.renderers import BaseRenderer
from ninja_extra.controllers.base import APIController
from ninja_extra.controllers.controller_route.router import ControllerRouter

__all__ = ['NinjaExtraAPI', ]


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
    ):
        super(NinjaExtraAPI, self).__init__(
            title=title, version=version, description=description, openapi_url=openapi_url,
            docs_url=docs_url, urls_namespace=urls_namespace, csrf=csrf, auth=auth,
            renderer=renderer, parser=parser
        )

    def register_controllers(self, *controllers: APIController):
        for controller in controllers:
            if not controller.registered:
                controller_instance = object.__new__(controller)
                self._routers.extend(controller_instance.build_routers())
                controller_instance.set_api_instance(self)
                controller.registered = True

    def auto_discover_controllers(self):
        from django.apps import apps
        installed_apps = [v for k, v in apps.app_configs.items() if not v.name.startswith("django.")]
        possible_module_name = ['api', 'controllers']

        for app_module in installed_apps:
            try:
                app_module_ = import_module(app_module.name)
                for module in possible_module_name:
                    if module_has_submodule(app_module_, module):
                        mod_path = '%s.%s' % (app_module.name, module)
                        import_module(mod_path)
                self.register_controllers(*ControllerRouter.get_controllers().values())
            except ImportError as ex:
                raise ex

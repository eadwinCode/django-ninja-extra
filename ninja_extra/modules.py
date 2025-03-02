import threading
from typing import Optional

from django.conf import Settings, settings
from injector import Binder, Module, singleton

from ninja_extra.context import RouteContext

from .constants import ROUTE_CONTEXT_VAR

# @receiver([route_context_started, route_context_finished], sender=RouteContext)
# def route_context_handler(
#     *args: Any, route_context: Optional[RouteContext] = None, **kwargs: Any
# ) -> None:
#     app = cast(Any, apps.get_app_config("ninja_extra"))
#     app.ninja_extra_module.set_route_context(route_context)


class NinjaExtraModule(Module):
    def __init__(self) -> None:
        self._local = threading.local()

    def set_route_context(self, route_context: RouteContext) -> None:
        ROUTE_CONTEXT_VAR.set(route_context)

    def get_route_context(self) -> Optional[RouteContext]:
        return ROUTE_CONTEXT_VAR.get()

    def configure(self, binder: Binder) -> None:
        binder.bind(Settings, to=settings, scope=singleton)  # type: ignore
        binder.bind(RouteContext, to=lambda: self.get_route_context())  # type: ignore

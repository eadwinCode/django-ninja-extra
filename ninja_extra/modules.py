import threading
from typing import Any, Optional, cast

from django.apps import apps
from django.conf import Settings, settings
from django.dispatch import receiver
from injector import Binder, Module, singleton

from ninja_extra.controllers.route.context import RouteContext

from .signals import route_context_finished, route_context_started


@receiver([route_context_started, route_context_finished], sender=RouteContext)
def route_context_handler(
    *args: Any, route_context: Optional[RouteContext] = None, **kwargs: Any
) -> None:
    app = cast(Any, apps.get_app_config("ninja_extra"))
    app.ninja_extra_module.set_route_context(route_context)


class NinjaExtraModule(Module):
    def __init__(self) -> None:
        self._local = threading.local()

    def set_route_context(self, route_context: RouteContext) -> None:
        self._local.route_context = route_context

    def get_route_context(self) -> Optional[RouteContext]:
        try:
            return self._local.route_context  # type:ignore
        except AttributeError:  # pragma: no cover
            return None

    def configure(self, binder: Binder) -> None:
        binder.bind(Settings, to=settings, scope=singleton)  # type: ignore
        binder.bind(RouteContext, to=lambda: self.get_route_context())  # type: ignore

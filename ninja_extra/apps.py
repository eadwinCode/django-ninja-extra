from typing import Any, cast

from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _
from injector import Injector, Module

from ninja_extra.conf import settings
from ninja_extra.modules import NinjaExtraModule
from ninja_extra.shortcuts import fail_silently


class NinjaExtraConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ninja_extra"
    verbose_name = _("Django Ninja Extra")
    injector: Injector

    def ready(self) -> None:
        self.injector = Injector([NinjaExtraModule])
        # get django_injector is available or registered
        django_injector_app = fail_silently(
            apps.get_app_config, app_label="django_injector"
        )
        app = cast(Any, django_injector_app)
        if app:
            app.ready()
            self.injector = app.injector
        self.register_injector_modules()

    def register_injector_modules(self) -> None:
        for module in settings.INJECTOR_MODULES:
            if isinstance(module, type) and issubclass(module, Module):
                module = module()
            self.injector.binder.install(module)

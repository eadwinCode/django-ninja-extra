from typing import cast, Any
from ninja_extra.shortcuts import fail_silently
from django.apps import AppConfig, apps
from ninja_extra.modules import NinjaExtraModule
from injector import Injector


class NinjaExtraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ninja_extra'
    injector: Injector

    def ready(self) -> None:
        self.injector = Injector([NinjaExtraModule])
        # get django_injector is available and registered
        django_injector_app = fail_silently(apps.get_app_config, app_label='django_injector')
        app = cast(Any, django_injector_app)
        if app:
            app.ready()
            self.injector = app.injector

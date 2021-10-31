from typing import Any, List, Optional, Tuple, Union, cast

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from injector import Injector

from ninja_extra.apps import NinjaExtraConfig
from ninja_extra.shortcuts import fail_silently

__all__ = ["service_resolver", "get_injector"]


def get_injector() -> Injector:
    app = cast(
        Optional[NinjaExtraConfig],
        fail_silently(apps.get_app_config, NinjaExtraConfig.name),
    )
    if not app:
        raise ImproperlyConfigured(
            "ninja_extra app is not installed. Did you forget register `ninja_extra` in `INSTALLED_APPS`"
        )
    injector = app.injector
    return injector


def service_resolver(*services: type) -> Union[Tuple[Any], Any]:
    assert services, "Service can not be empty"

    injector = get_injector()

    if len(services) > 1:
        services_resolved: List[Any] = []
        for service in services:
            services_resolved.append(injector.get(service))
        return tuple(services_resolved)
    return injector.get(services[0])

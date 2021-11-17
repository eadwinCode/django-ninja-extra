from typing import List, Optional, Tuple, Type, TypeVar, Union, cast

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from injector import Injector, Module

from ninja_extra.apps import NinjaExtraConfig
from ninja_extra.shortcuts import fail_silently

__all__ = ["service_resolver", "get_injector", "register_injector_modules"]

T = TypeVar("T")


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


def service_resolver(*interfaces: Type[T]) -> Union[Tuple[T, ...], T]:
    assert interfaces, "Service can not be empty"

    injector = get_injector()

    if len(interfaces) > 1:
        services_resolved: List[T] = []
        for service in interfaces:
            services_resolved.append(injector.get(service))
        return tuple(services_resolved)
    return injector.get(interfaces[0])


def register_injector_modules(*modules: Union[Module, Type[Module]]) -> None:
    for module in modules:
        injector = get_injector()
        if isinstance(module, type) and issubclass(module, Module):
            module = module()
        injector.binder.install(module)

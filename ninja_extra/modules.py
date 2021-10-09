from django.conf import Settings, settings
from injector import Binder, Module, singleton


class NinjaExtraModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(Settings, to=settings, scope=singleton)  # type: ignore

from injector import Module, Binder, singleton
from django.conf import Settings, settings


class NinjaExtraModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(Settings, to=settings, scope=singleton)

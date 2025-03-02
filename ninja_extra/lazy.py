import typing as t

from django.utils.functional import LazyObject, empty
from django.utils.module_loading import import_string

if t.TYPE_CHECKING:
    from ninja_extra.conf.package_settings import NinjaExtraSettings


class LazyStrImport(LazyObject):
    def __init__(self, import_str: str):
        self.__dict__["_import_str"] = import_str
        super(LazyStrImport, self).__init__()

    @t.no_type_check
    def _setup(self):
        if self._wrapped is empty:
            self._wrapped = import_string(self._import_str)
        return self._wrapped

    @t.no_type_check
    def __call__(self, *args, **kwargs):
        if self._wrapped is empty:
            self._setup()
        return self._wrapped(*args, **kwargs)


def settings_lazy() -> "NinjaExtraSettings":
    return t.cast(
        "NinjaExtraSettings", LazyStrImport("ninja_extra.conf.settings")._setup()
    )

from typing import Any, List

from django.conf import settings as django_settings
from django.test.signals import setting_changed
from ninja import Schema
from pydantic import Field, root_validator, validator

from ninja_extra.lazy import LazyStrImport


class UserDefinedSettingsMapper:
    def __init__(self, data: dict) -> None:
        self.__dict__ = data


NinjaExtra_SETTINGS_DEFAULTS = dict(
    INJECTOR_MODULES=[],
    PAGINATION_CLASS="ninja_extra.pagination.LimitOffsetPagination",
)

USER_SETTINGS = UserDefinedSettingsMapper(
    getattr(django_settings, "NINJA_EXTRA", NinjaExtra_SETTINGS_DEFAULTS)
)


class NinjaExtraSettings(Schema):
    class Config:
        orm_mode = True
        validate_assignment = True

    PAGINATION_CLASS: Any = Field(
        "ninja_extra.pagination.PageNumberPaginationExtra",
    )
    PAGINATION_PER_PAGE: int = Field(100)
    INJECTOR_MODULES: List[Any] = []

    @validator("INJECTOR_MODULES", pre=True)
    def pre_injector_module_validate(cls, value: Any) -> Any:
        if not isinstance(value, list):
            raise ValueError("Invalid data type")
        return value

    @validator("PAGINATION_CLASS", pre=True)
    def pre_pagination_class_validate(cls, value: Any) -> Any:
        if isinstance(value, list):
            raise ValueError("Invalid data type")
        return value

    @root_validator
    def validate_ninja_extra_settings(cls, values: Any) -> Any:
        for item in NinjaExtra_SETTINGS_DEFAULTS.keys():
            if (
                isinstance(values[item], (tuple, list))
                and values[item]
                and isinstance(values[item][0], str)
            ):
                values[item] = [LazyStrImport(str(klass)) for klass in values[item]]
            if isinstance(values[item], str):
                values[item] = LazyStrImport(values[item])
        return values


# convert to lazy object
settings = NinjaExtraSettings.from_orm(USER_SETTINGS)


def reload_settings(*args: Any, **kwargs: Any) -> None:
    global settings

    setting, value = kwargs["setting"], kwargs["value"]

    if setting == "NINJA_EXTRA":
        settings = NinjaExtraSettings.from_orm(UserDefinedSettingsMapper(value))


setting_changed.connect(reload_settings)

import typing as t

from django.conf import settings as django_settings
from django.core.signals import setting_changed
from ninja import Schema
from pydantic import Field, field_validator
from pydantic.config import ConfigDict

from ninja_extra.lazy import LazyStrImport


class UserDefinedSettingsMapper:
    def __init__(self, data: dict) -> None:
        self.__dict__ = data


NinjaExtra_SETTINGS_DEFAULTS = {
    "INJECTOR_MODULES": [],
    "PAGINATION_CLASS": "ninja_extra.pagination.LimitOffsetPagination",
    "THROTTLE_CLASSES": [
        "ninja_extra.throttling.AnonRateThrottle",
        "ninja_extra.throttling.UserRateThrottle",
    ],
    "THROTTLE_RATES": {"user": None, "anon": None},
    "ORDERING_CLASS": "ninja_extra.ordering.Ordering",
    "SEARCHING_CLASS": "ninja_extra.searching.Searching",
}

USER_SETTINGS = UserDefinedSettingsMapper(
    getattr(django_settings, "NINJA_EXTRA", NinjaExtra_SETTINGS_DEFAULTS)
)


class NinjaExtraSettings(Schema):
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    PAGINATION_CLASS: t.Any = Field(
        "ninja_extra.pagination.LimitOffsetPagination",
    )
    PAGINATION_PER_PAGE: int = Field(100)
    THROTTLE_RATES: t.Dict[str, t.Optional[str]] = Field(
        {"user": "1000/day", "anon": "100/day"}
    )
    THROTTLE_CLASSES: t.List[t.Any] = []
    NUM_PROXIES: t.Optional[int] = None
    INJECTOR_MODULES: t.List[t.Any] = []
    ORDERING_CLASS: t.Union[str, t.Type] = "ninja_extra.ordering.Ordering"
    SEARCHING_CLASS: t.Any = Field(
        "ninja_extra.searching.Searching",
    )

    @field_validator("INJECTOR_MODULES", mode="before")
    def pre_injector_module_validate(cls, value: t.Any) -> t.Any:
        if not isinstance(value, list):
            raise ValueError("Invalid data type")
        return cls._validate_ninja_extra_settings(value)

    @field_validator("THROTTLE_CLASSES", mode="before")
    def pre_throttling_class_validate(cls, value: t.Any) -> t.Any:
        if not isinstance(value, list):
            raise ValueError("Invalid data type")
        return cls._validate_ninja_extra_settings(value)

    @field_validator("PAGINATION_CLASS", mode="before")
    def pre_pagination_class_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, list):
            raise ValueError("Invalid data type")
        return cls._validate_ninja_extra_settings(value)

    @field_validator("ORDERING_CLASS", mode="before")
    def pre_ordering_class_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, list):
            raise ValueError("Invalid data type")
        return cls._validate_ninja_extra_settings(value)

    @field_validator("SEARCHING_CLASS", mode="before")
    def pre_searching_class_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, list):
            raise ValueError("Invalid data type")
        return cls._validate_ninja_extra_settings(value)

    # @model_validator(mode='after')
    # def validate_after(self):
    #     for item in NinjaExtra_SETTINGS_DEFAULTS.keys():
    #         value = getattr(self, item)
    #         if (
    #             isinstance(value, (tuple, list))
    #             and value
    #             and isinstance(value[0], str)
    #         ):
    #             value = [LazyStrImport(str(klass)) for klass in value]
    #         if isinstance(value, str):
    #             value = LazyStrImport(value)
    #
    #         setattr(self, item, value)
    #     return self
    @classmethod
    def _validate_ninja_extra_settings(cls, value: t.Any) -> t.Any:
        if isinstance(value, (tuple, list)) and value and isinstance(value, str):
            return [LazyStrImport(str(klass)) for klass in value]
        if isinstance(value, str):
            return LazyStrImport(value)
        return value


settings = NinjaExtraSettings.from_orm(USER_SETTINGS)


def reload_settings(*args: t.Any, **kwargs: t.Any) -> None:  # pragma: no cover
    global settings

    setting, value = kwargs["setting"], kwargs["value"]

    if setting == "NINJA_EXTRA":
        settings = NinjaExtraSettings.from_orm(UserDefinedSettingsMapper(value))


setting_changed.connect(reload_settings)  # pragma: no cover

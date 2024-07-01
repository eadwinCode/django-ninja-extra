from typing import Any, Dict, List, Optional

from django.conf import settings as django_settings
from django.core.signals import setting_changed
from pydantic.v1 import BaseModel, Field, root_validator, validator

from ninja_extra.lazy import LazyStrImport


class UserDefinedSettingsMapper:
    def __init__(self, data: dict) -> None:
        self.__dict__ = data


NinjaEXTRA_SETTINGS_DEFAULTS = {
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
    getattr(django_settings, "NINJA_EXTRA", NinjaEXTRA_SETTINGS_DEFAULTS)
)


class NinjaExtraSettings(BaseModel):
    class Config:
        orm_mode = True
        validate_assignment = True

    PAGINATION_CLASS: Any = Field(
        "ninja_extra.pagination.LimitOffsetPagination",
    )
    PAGINATION_PER_PAGE: int = Field(100)
    THROTTLE_RATES: Dict[str, Optional[str]] = Field(
        {"user": "1000/day", "anon": "100/day"}
    )
    THROTTLE_CLASSES: List[Any] = Field(
        [
            "ninja_extra.throttling.AnonRateThrottle",
            "ninja_extra.throttling.UserRateThrottle",
        ]
    )
    NUM_PROXIES: Optional[int] = None
    INJECTOR_MODULES: List[Any] = []
    ORDERING_CLASS: Any = Field(
        "ninja_extra.ordering.Ordering",
    )
    SEARCHING_CLASS: Any = Field(
        "ninja_extra.searching.Searching",
    )

    @validator("INJECTOR_MODULES", pre=True)
    def pre_injector_module_validate(cls, value: Any) -> Any:
        if not isinstance(value, list):
            raise ValueError("Invalid data type")
        return value

    @validator("THROTTLE_CLASSES", pre=True)
    def pre_throttling_class_validate(cls, value: Any) -> Any:
        if not isinstance(value, list):
            raise ValueError("Invalid data type")
        return value

    @validator("PAGINATION_CLASS", pre=True)
    def pre_pagination_class_validate(cls, value: Any) -> Any:
        if isinstance(value, list):
            raise ValueError("Invalid data type")
        return value

    @validator("ORDERING_CLASS", pre=True)
    def pre_ordering_class_validate(cls, value: Any) -> Any:
        if isinstance(value, list):
            raise ValueError("Invalid data type")
        return value

    @validator("SEARCHING_CLASS", pre=True)
    def pre_searching_class_validate(cls, value: Any) -> Any:
        if isinstance(value, list):
            raise ValueError("Invalid data type")
        return value

    @root_validator
    def validate_ninja_extra_settings(cls, values: Any) -> Any:
        for item in NinjaEXTRA_SETTINGS_DEFAULTS.keys():
            if (
                isinstance(values[item], (tuple, list))
                and values[item]
                and isinstance(values[item][0], str)
            ):
                values[item] = [LazyStrImport(str(klass)) for klass in values[item]]
            if isinstance(values[item], str):
                values[item] = LazyStrImport(values[item])
        return values


settings = NinjaExtraSettings.from_orm(USER_SETTINGS)


def reload_settings(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    global settings

    setting, value = kwargs["setting"], kwargs["value"]

    if setting == "NINJA_EXTRA":
        settings = NinjaExtraSettings.from_orm(UserDefinedSettingsMapper(value))


setting_changed.connect(reload_settings)  # pragma: no cover

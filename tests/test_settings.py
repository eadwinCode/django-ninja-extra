import pytest
from pydantic.v1 import ValidationError

from ninja_extra.conf import settings
from ninja_extra.controllers import RouteContext


class CustomPaginationImport:
    pass


class CustomModuleImport:
    pass


class CustomThrottlingClassImport:
    pass


class CustomOrderingClassImport:
    pass


class CustomSearchClassImport:
    pass


class CustomRouteContextClassImport(RouteContext):
    pass


def test_setting_imports_string_works(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(
            settings,
            "INJECTOR_MODULES",
            [
                "tests.test_settings.CustomModuleImport",
            ],
        )
        m.setattr(
            settings, "PAGINATION_CLASS", "tests.test_settings.CustomPaginationImport"
        )
        m.setattr(
            settings,
            "THROTTLE_CLASSES",
            [
                "tests.test_settings.CustomThrottlingClassImport",
            ],
        )
        m.setattr(
            settings, "ORDERING_CLASS", "tests.test_settings.CustomOrderingClassImport"
        )
        m.setattr(
            settings, "SEARCHING_CLASS", "tests.test_settings.CustomSearchClassImport"
        )
        m.setattr(
            settings,
            "ROUTE_CONTEXT_CLASS",
            "tests.test_settings.CustomRouteContextClassImport",
        )

        assert isinstance(settings.INJECTOR_MODULES[0](), CustomModuleImport)
        assert isinstance(settings.PAGINATION_CLASS(), CustomPaginationImport)
        assert isinstance(settings.THROTTLE_CLASSES[0](), CustomThrottlingClassImport)
        assert isinstance(settings.ORDERING_CLASS(), CustomOrderingClassImport)
        assert isinstance(settings.SEARCHING_CLASS(), CustomSearchClassImport)
        assert isinstance(
            settings.ROUTE_CONTEXT_CLASS(request=None), CustomRouteContextClassImport
        )
    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "PAGINATION_CLASS", ["tests.test_settings.CustomModuleImport"]
        )

    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "THROTTLE_CLASSES", "tests.test_settings.CustomModuleImport"
        )

    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "INJECTOR_MODULES", "tests.test_settings.CustomModuleImport"
        )

    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "ORDERING_CLASS", ["tests.test_settings.CustomModuleImport"]
        )

    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "SEARCHING_CLASS", ["tests.test_settings.CustomModuleImport"]
        )

    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "ROUTE_CONTEXT_CLASS", ["tests.test_settings.CustomModuleImport"]
        )

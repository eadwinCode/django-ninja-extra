import pytest

from ninja_extra.conf import settings
from ninja_extra.context import RouteContext
from ninja_extra.interfaces.ordering import OrderingBase
from ninja_extra.interfaces.searching import SearchingBase
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.throttling import BaseThrottle


class CustomPaginationImport(PageNumberPaginationExtra):
    pass


class CustomModuleImport:
    pass


class CustomThrottlingClassImport(BaseThrottle):
    pass


class CustomOrderingClassImport(OrderingBase):
    def ordering_queryset(self, items, ordering_input):
        pass


class CustomSearchClassImport(SearchingBase):
    def searching_queryset(self, items, search_input):
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
        assert settings.PAGINATION_CLASS is CustomPaginationImport
        assert isinstance(settings.THROTTLE_CLASSES[0](), CustomThrottlingClassImport)
        assert settings.ORDERING_CLASS is CustomOrderingClassImport
        assert settings.SEARCHING_CLASS is CustomSearchClassImport
        assert isinstance(
            settings.ROUTE_CONTEXT_CLASS(request=None), CustomRouteContextClassImport
        )

    with pytest.raises(ValueError):
        monkeypatch.setattr(
            settings, "PAGINATION_CLASS", ["tests.test_settings.CustomModuleImport"]
        )

    with pytest.raises(ValueError):
        monkeypatch.setattr(
            settings, "PAGINATION_CLASS", "tests.test_settings.CustomModuleImport"
        )

    with pytest.raises(ValueError):
        monkeypatch.setattr(
            settings, "THROTTLE_CLASSES", "tests.test_settings.CustomModuleImport"
        )

    with pytest.raises(ValueError):
        monkeypatch.setattr(
            settings, "INJECTOR_MODULES", "tests.test_settings.CustomModuleImport"
        )

    with pytest.raises(ValueError):
        monkeypatch.setattr(
            settings, "ORDERING_CLASS", "tests.test_settings.CustomModuleImport"
        )

    with pytest.raises(ValueError):
        monkeypatch.setattr(
            settings, "SEARCHING_CLASS", "tests.test_settings.CustomModuleImport"
        )

    with pytest.raises(ValueError):
        monkeypatch.setattr(
            settings, "ROUTE_CONTEXT_CLASS", "tests.test_settings.CustomModuleImport"
        )
        assert settings.ROUTE_CONTEXT_CLASS

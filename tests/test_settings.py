import pytest
from pydantic import ValidationError

from ninja_extra.conf import settings


class CustomPaginationImport:
    pass


class CustomModuleImport:
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

        assert isinstance(settings.INJECTOR_MODULES[0](), CustomModuleImport)
        assert isinstance(settings.PAGINATION_CLASS(), CustomPaginationImport)

    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "PAGINATION_CLASS", ["tests.test_settings.CustomModuleImport"]
        )
    with pytest.raises(ValidationError):
        monkeypatch.setattr(
            settings, "INJECTOR_MODULES", "tests.test_settings.CustomModuleImport"
        )

import pytest

from ninja_extra.lazy import LazyStrImport


class TestLazyClassImport:
    """Test lazy import"""


def test_lazy_str_import_works():
    lazy_import = LazyStrImport("tests.test_lazy_import.TestLazyClassImport")
    instance = lazy_import()
    assert isinstance(instance, TestLazyClassImport)

    with pytest.raises(ImportError):
        lazy_import = LazyStrImport("tests.test_lazy_import.InvalidLazyClassImport")
        lazy_import()

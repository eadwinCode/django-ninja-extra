import pytest

from ninja_extra.reflect import reflect


def test_define_metadata_creates_attribute_dict(random_type):
    key = "FrameworkName"
    reflect.define_metadata(key, "Ellar", random_type)
    # assert hasattr(random_type, REFLECT_TYPE)
    assert reflect.get_metadata(key, random_type) == "Ellar"
    assert list(reflect.get_metadata_keys(random_type)) == [key]


@pytest.mark.parametrize("immutable_type", ["FrameworkName", 23, (33, 45), {34, 45}])
def test_reflect_works_with_immutable_types(immutable_type, reflect_context):
    key = "FrameworkName"
    reflect.define_metadata(key, "Ellar", immutable_type)
    # assert hasattr(random_type, REFLECT_TYPE)
    assert reflect.get_metadata(key, immutable_type) == "Ellar"
    assert list(reflect.get_metadata_keys(immutable_type)) == [key]


def test_define_metadata_without_default(random_type):
    key = "FrameworkName"

    reflect.define_metadata(key, "Ellar", random_type)
    assert reflect.get_metadata(key, random_type) == "Ellar"
    reflect.define_metadata(key, "Starlette", random_type)
    assert reflect.get_metadata(key, random_type) == "Starlette"


def test_define_metadata_with_existing_tuple(random_type):
    reflect.define_metadata("B", ("EllarB",), random_type)
    assert reflect.get_metadata("B", random_type) == ("EllarB",)

    reflect.define_metadata("B", ("AnotherEllar",), random_type)
    reflect.define_metadata("B", ("AnotherEllarC",), random_type)
    assert reflect.get_metadata("B", random_type) == (
        "EllarB",
        "AnotherEllar",
        "AnotherEllarC",
    )


def test_get_all_metadata(random_type):
    reflect.define_metadata("B", ("EllarB",), random_type)
    assert reflect.get_metadata("B", random_type) == ("EllarB",)

    reflect.define_metadata("B", ("AnotherEllar",), random_type)
    data = reflect.get_all_metadata(random_type)
    assert data == {"B": ("EllarB", "AnotherEllar")}


def test_delete_all_metadata(random_type):
    reflect.define_metadata("D", ("EllarD",), random_type)

    reflect.define_metadata("B", ("AnotherEllar",), random_type)
    data = reflect.get_all_metadata(random_type)
    assert data == {"B": ("AnotherEllar",), "D": ("EllarD",)}

    reflect.delete_all_metadata(random_type)
    assert reflect.get_metadata("D", random_type) is None


def test_define_metadata_with_existing_list(random_type):
    reflect.define_metadata("B", ["Ellar"], random_type)
    assert reflect.get_metadata("B", random_type) == ["Ellar"]

    reflect.define_metadata("B", ["AnotherEllar"], random_type)
    reflect.define_metadata("B", ["AnotherEllarD"], random_type)
    assert reflect.get_metadata("B", random_type) == [
        "Ellar",
        "AnotherEllar",
        "AnotherEllarD",
    ]


def test_define_metadata_with_existing_dict(random_type):
    reflect.define_metadata("C", {"C": "EllarC"}, random_type)
    assert reflect.get_metadata("C", random_type) == {"C": "EllarC"}

    reflect.define_metadata("C", {"D": "EllarD"}, random_type)
    assert reflect.get_metadata("C", random_type) == {
        "D": "EllarD",
        "C": "EllarC",
    }


def test_define_metadata_with_existing_set(random_type):
    reflect.define_metadata("A", {"EllarA"}, random_type)
    reflect.define_metadata("A", {"AnotherEllar"}, random_type)
    assert reflect.get_metadata("A", random_type) == {"AnotherEllar", "EllarA"}


def test_reflect_meta_decorator():
    @reflect.metadata("defined_key", "chioma")
    @reflect.metadata("defined_key_b", "jessy")
    def function_a():
        """ignore"""

    assert reflect.get_metadata("defined_key", function_a) == "chioma"
    assert reflect.get_metadata("defined_key_b", function_a) == "jessy"
    assert list(reflect.get_metadata_keys(function_a)) == [
        "defined_key_b",
        "defined_key",
    ]


def test_reflect_has_metadata_works():
    @reflect.metadata("defined_key", "jessy")
    def function_new():
        """ignore"""

    assert reflect.has_metadata("defined_key", function_new)
    assert reflect.has_metadata("defined_key_b", function_new) is False


def test_reflect_get_metadata_or_raise_exception():
    @reflect.metadata("defined_key_b", "jessy")
    def function_new():
        """ignore"""

    assert (
        reflect.get_metadata_or_raise_exception("defined_key_b", function_new)
        == "jessy"
    )

    with pytest.raises(Exception, match="MetaData Key not Found"):
        reflect.get_metadata_or_raise_exception("defined_key", function_new)


def test_delete_metadata_works():
    @reflect.metadata("defined_key_b", "jessy")
    def function_new():
        """ignore"""

    reflect.delete_metadata("defined_key_b", function_new)
    assert reflect.has_metadata("defined_key_b", function_new) is False


def test_reflect_context_works():
    @reflect.metadata("defined_key_b", "jessy")
    @reflect.metadata("defined_key", "clara")
    def function_new():
        """ignore"""

    with reflect.context():
        reflect.define_metadata("defined_key_c", "Eadwin", function_new)
        reflect.define_metadata("defined_key_d", "Dakolo", function_new)

        assert reflect.has_metadata("defined_key_b", function_new)
        assert reflect.has_metadata("defined_key", function_new)
        assert reflect.has_metadata("defined_key_c", function_new)
        assert reflect.has_metadata("defined_key_d", function_new)

    assert reflect.has_metadata("defined_key_c", function_new) is False
    assert reflect.has_metadata("defined_key_d", function_new) is False


@pytest.mark.asyncio
async def test_reflect_async_context_works():
    @reflect.metadata("defined_key_b", "jessy")
    @reflect.metadata("defined_key", "clara")
    def function_new():
        """ignore"""

    async with reflect.async_context():
        reflect.define_metadata("defined_key_c", "Eadwin", function_new)
        reflect.define_metadata("defined_key_d", "Dakolo", function_new)

        assert reflect.has_metadata("defined_key_b", function_new)
        assert reflect.has_metadata("defined_key", function_new)
        assert reflect.has_metadata("defined_key_c", function_new)
        assert reflect.has_metadata("defined_key_d", function_new)

    assert reflect.has_metadata("defined_key_c", function_new) is False
    assert reflect.has_metadata("defined_key_d", function_new) is False


def test_define_metadata_raise_exception():
    with pytest.raises(Exception, match="`target` is not a valid type"):
        reflect.define_metadata("defined_key_c", "Eadwin", None)


def test_define_metadata_overrides_existing_collection_of_different_type():
    pass

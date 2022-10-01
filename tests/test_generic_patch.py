import sys

import pytest

from ninja_extra.generic import GenericType
from ninja_extra.schemas.response import (
    DetailSchema,
    IdSchema,
    NinjaPaginationResponseSchema,
    OkSchema,
    PaginatedResponseSchema,
)


class A(object):
    wrap_generic: str


class AGenericPatch(GenericType, generic_base_name="A"):
    def get_generic_type(self, wrap_type):
        class _A(A):
            wrap_generic: wrap_type

        return _A


def test_generic_patch_works():
    B = AGenericPatch[int]
    assert str(B.__name__) == "A[int]"
    assert B.__annotations__["wrap_generic"] == int
    assert hasattr(B, "__generic_model__")
    assert B.__generic_model__ == AGenericPatch
    assert B == AGenericPatch[int]


@pytest.mark.skipif(sys.version_info >= (3, 7), reason="requires python < 3.7")
@pytest.mark.parametrize(
    "generic_patch, generic_name",
    [
        (IdSchema, "IdSchema"),
        (OkSchema, "OkSchema"),
        (PaginatedResponseSchema, "PaginatedResponseSchema"),
        (NinjaPaginationResponseSchema, "NinjaPaginationResponseSchema"),
        (DetailSchema, "DetailSchema"),
    ],
)
def test_response_schemas_generic_patch_py36(generic_patch, generic_name):
    new_generic_object = generic_patch[int]
    assert str(new_generic_object.__name__) == f"{generic_name}[int]"
    assert hasattr(new_generic_object, "__generic_model__")
    assert new_generic_object.__generic_model__ == generic_patch
    assert new_generic_object == generic_patch[int]


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python >= 3.7")
@pytest.mark.parametrize(
    "generic_schema",
    [
        IdSchema,
        OkSchema,
        PaginatedResponseSchema,
        NinjaPaginationResponseSchema,
        DetailSchema,
    ],
)
def test_response_schemas_generic_patch_py37(generic_schema):
    new_generic_object = generic_schema[int]
    assert hasattr(new_generic_object, "__generic_model__")
    assert new_generic_object.__generic_model__ == generic_schema
    assert new_generic_object == generic_schema[int]

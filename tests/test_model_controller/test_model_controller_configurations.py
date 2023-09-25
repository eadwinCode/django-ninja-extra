import pytest

from ninja_extra import ModelConfig, ModelPagination
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema, RouteParameter

from ..models import Event


class InvalidTypeORSchema:
    pass


def test_default_model_config():
    model_config = ModelConfig(model=Event)
    assert model_config.dict() == {
        "allowed_routes": ["create", "find_one", "update", "patch", "delete", "list"],
        "create_schema": None,
        "retrieve_schema": None,
        "update_schema": None,
        "patch_schema": None,
        "pagination": {
            "klass": PageNumberPaginationExtra,
            "paginator_kwargs": None,
            "pagination_schema": PaginatedResponseSchema,
        },
        "model": Event,
        "schema_config": {
            "include": "__all__",
            "exclude": set(),
            "optional": None,
            "depth": 0,
            "read_only_fields": None,
            "write_only_fields": None,
        },
    }


def test_invalid_django_model():
    with pytest.raises(ValueError):
        ModelConfig(model=InvalidTypeORSchema)


def test_invalid_allowed_route():
    with pytest.raises(ValueError):
        ModelConfig(model=Event, allowed_routes=["invalid"])


def test_invalid_schema_type():
    with pytest.raises(ValueError):
        ModelConfig(model=Event, create_schema=InvalidTypeORSchema)

    with pytest.raises(ValueError):
        ModelConfig(model=Event, retrieve_schema=InvalidTypeORSchema)

    with pytest.raises(ValueError):
        ModelConfig(model=Event, update_schema=InvalidTypeORSchema)

    with pytest.raises(ValueError):
        ModelConfig(model=Event, patch_schema=InvalidTypeORSchema)


def test_invalid_pagination_klass():
    with pytest.raises(ValueError):
        ModelConfig(model=Event, pagination=ModelPagination(klass=InvalidTypeORSchema))


def test_invalid_pagination_schema():
    with pytest.raises(ValueError):
        ModelConfig(
            model=Event,
            pagination=ModelPagination(pagination_schema=InvalidTypeORSchema),
        )

    with pytest.raises(ValueError):
        ModelConfig(
            model=Event, pagination=ModelPagination(pagination_schema=RouteParameter)
        )

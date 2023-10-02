import pytest
from ninja_schema.errors import ConfigError

from ninja_extra import ModelConfig, ModelPagination, ModelSchemaConfig
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema, RouteParameter

from ..models import Event


class InvalidTypeORSchema:
    pass


def test_default_model_config():
    model_config = ModelConfig(model=Event)
    assert model_config.dict() == {
        "allowed_routes": ["create", "find_one", "update", "patch", "delete", "list"],
        "create_schema": model_config.create_schema,
        "retrieve_schema": model_config.retrieve_schema,
        "update_schema": model_config.update_schema,
        "patch_schema": model_config.patch_schema,
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
        "create_route_info": {},
        "find_one_route_info": {},
        "update_route_info": {},
        "patch_route_info": {},
        "list_route_info": {},
        "delete_route_info": {},
    }


def test_include_gen_schema():
    model_config = ModelConfig(
        model=Event,
        allowed_routes=["list", "find_one"],
        schema_config=ModelSchemaConfig(include=["title", "start_date", "end_date"]),
    )
    assert model_config.create_schema is None
    assert model_config.patch_schema is None
    assert model_config.update_schema is None

    assert model_config.retrieve_schema.schema() == {
        "title": "EventSchema",
        "type": "object",
        "properties": {
            "id": {"title": "Id", "type": "integer"},
            "title": {"title": "Title", "maxLength": 100, "type": "string"},
            "start_date": {"title": "Start Date", "type": "string", "format": "date"},
            "end_date": {"title": "End Date", "type": "string", "format": "date"},
        },
        "required": ["id", "title", "start_date", "end_date"],
    }


def test_exclude_gen_schema():
    model_config = ModelConfig(
        model=Event,
        allowed_routes=["list", "find_one"],
        schema_config=ModelSchemaConfig(exclude=["start_date", "end_date"]),
    )
    assert model_config.create_schema is None
    assert model_config.patch_schema is None
    assert model_config.update_schema is None

    assert model_config.retrieve_schema.schema() == {
        "properties": {
            "category_id": {"title": "Category", "type": "integer"},
            "id": {"title": "Id", "type": "integer"},
            "title": {"maxLength": 100, "title": "Title", "type": "string"},
        },
        "required": ["id", "title"],
        "title": "EventSchema",
        "type": "object",
    }


def test_update_schema_created_in_absence_of_create_schema():
    model_config = ModelConfig(
        model=Event,
        allowed_routes=["update", "patch"],
        schema_config=ModelSchemaConfig(include=["title", "start_date", "end_date"]),
    )
    assert model_config.create_schema is None
    assert model_config.retrieve_schema is not None
    assert model_config.patch_schema is not None
    assert model_config.update_schema is not None


def test_create_schema_invalid_key():
    model_config = ModelConfig(
        model=Event,
        allowed_routes=["create"],
        schema_config=ModelSchemaConfig(include=["title", "start_date", "end_date"]),
    )
    assert model_config.create_schema is not None
    assert model_config.retrieve_schema is not None

    assert model_config.update_schema is None
    assert model_config.patch_schema is None

    with pytest.raises(ConfigError):
        ModelConfig(
            model=Event,
            allowed_routes=["update", "patch"],
            schema_config=ModelSchemaConfig(
                include=["title", "start_date", "end_date"],
                write_only_fields=["invalid"],
            ),
        )


def test_retrieve_schema_invalid_key():
    with pytest.raises(ConfigError):
        ModelConfig(
            model=Event,
            allowed_routes=["update", "patch"],
            schema_config=ModelSchemaConfig(
                include=["title", "start_date", "end_date"],
                read_only_fields=["invalid"],
            ),
        )


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

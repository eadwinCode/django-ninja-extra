import typing as t

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from ninja.pagination import PaginationBase
from pydantic import BaseModel as PydanticModel
from pydantic import Field, field_validator

try:
    from ninja_schema import __version__ as ninja_schema_version
    from ninja_schema.errors import ConfigError
    from ninja_schema.orm.factory import SchemaFactory
    from ninja_schema.orm.model_schema import (
        ModelSchemaConfig as NinjaSchemaModelSchemaConfig,
    )
    from ninja_schema.orm.model_schema import (
        ModelSchemaConfigAdapter,
    )

    NINJA_SCHEMA_VERSION = tuple(map(int, ninja_schema_version.split(".")))
except Exception:  # pragma: no cover
    ConfigError = NinjaSchemaModelSchemaConfig = ModelSchemaConfigAdapter = (
        SchemaFactory
    ) = None
    NINJA_SCHEMA_VERSION = (0, 0, 0)


from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema


def _is_ninja_schema_version_supported() -> bool:
    if NINJA_SCHEMA_VERSION[1] >= 14 and NINJA_SCHEMA_VERSION[2] >= 1:
        return True
    raise ImproperlyConfigured("ninja-schema version 0.14.1 or higher is required")


class ModelPagination(PydanticModel):
    """
    Model Controller Pagination Configuration
    """

    klass: t.Type[PaginationBase] = PageNumberPaginationExtra
    paginator_kwargs: t.Optional[dict] = None
    pagination_schema: t.Type[PydanticModel] = PaginatedResponseSchema

    @field_validator("pagination_schema", mode="before")
    def validate_schema(cls, value: t.Any) -> t.Any:
        if (
            isinstance(value, type)
            and issubclass(value, PydanticModel)
            and issubclass(value, t.Generic)  # type:ignore[arg-type]
        ):
            return value
        raise ValueError(
            f"{value} is not a valid type. Please use a generic pydantic model."
        )


class ModelSchemaConfig(PydanticModel):
    """
    Model Controller Auto Schema Generation Configuration
    """

    include: t.Union[str, t.List[str]] = Field(default="__all__")
    exclude: t.Set[str] = Field(set())
    optional: t.Optional[t.Union[str, t.Set[str]]] = Field(default=None)
    depth: int = 0

    read_only_fields: t.Optional[t.List[str]] = Field(default=None)
    write_only_fields: t.Optional[t.Union[t.List[str]]] = Field(default=None)
    extra_config_dict: t.Optional[t.Dict[str, t.Any]] = Field(default=None)


class ModelConfig(PydanticModel):
    """
    Model Controller Configuration
    """

    allowed_routes: t.List[str] = Field(
        [
            "create",
            "find_one",
            "update",
            "patch",
            "delete",
            "list",
        ]
    )
    async_routes: bool = False
    create_schema: t.Optional[t.Type[PydanticModel]] = None
    retrieve_schema: t.Optional[t.Type[PydanticModel]] = None
    update_schema: t.Optional[t.Type[PydanticModel]] = None
    patch_schema: t.Optional[t.Type[PydanticModel]] = None

    pagination: t.Optional[ModelPagination] = Field(default=ModelPagination())
    model: t.Type[Model]

    schema_config: ModelSchemaConfig = Field(default=ModelSchemaConfig(exclude=set()))

    create_route_info: t.Dict = {}  # extra @post() information
    find_one_route_info: t.Dict = {}  # extra @get('/{id}') information
    update_route_info: t.Dict = {}  # extra @put() information
    patch_route_info: t.Dict = {}  # extra @patch() information
    list_route_info: t.Dict = {}  # extra @get('/') information
    delete_route_info: t.Dict = {}  # extra @delete() information

    @field_validator("allowed_routes", mode="before")
    def validate_allow_routes(cls, value: t.List[t.Any]) -> t.Any:
        defaults = ["create", "find_one", "update", "patch", "delete", "list"]
        for item in value:
            if item not in defaults:
                raise ValueError(f"'{item}' action is not recognized in [{defaults}]")
        return value

    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self.generate_all_schema()

    def generate_all_schema(self) -> None:
        _model_name = self.model.__name__.replace("Model", "")
        model_pk = getattr(
            self.model._meta.pk,
            "name",
            self.model._meta.pk.attname,
        )

        if (
            self.create_schema
            and self.retrieve_schema
            and self.patch_schema
            and self.update_schema
        ):
            # if all schemas have been provided, then we don't need to generate any schema
            return

        if not NinjaSchemaModelSchemaConfig:  # pragma: no cover
            raise RuntimeError(
                "ninja-schema package is required for ModelControllerSchema generation.\n pip install ninja-schema"
            )

        schema_model_config = NinjaSchemaModelSchemaConfig(
            "dummy",
            ModelSchemaConfigAdapter(
                {"model": self.model, "ninja_schema_abstract": True}
            ),
        )
        all_fields = {f.name: f for f in schema_model_config.model_fields()}.keys()
        working_fields = set(all_fields)

        if self.schema_config.include == "__all__":
            working_fields = set(all_fields)

        if self.schema_config.include and self.schema_config.include != "__all__":
            include_fields = set(self.schema_config.include)
            working_fields = include_fields

        elif self.schema_config.exclude:
            exclude_fields = set(self.schema_config.exclude)
            working_fields = working_fields - exclude_fields

        if self.schema_config.extra_config_dict:
            _is_ninja_schema_version_supported()

        if not self.create_schema and "create" in self.allowed_routes:
            create_schema_fields = self._get_create_schema_fields(
                working_fields, model_pk
            )
            self.create_schema = SchemaFactory.create_schema(
                self.model,
                name=f"{_model_name}CreateSchema",
                fields=list(create_schema_fields),
                skip_registry=True,
                depth=self.schema_config.depth,
                **(self.schema_config.extra_config_dict or {}),
            )

        if not self.update_schema and "update" in self.allowed_routes:
            if self.create_schema:
                self.update_schema = self.create_schema
            else:
                create_schema_fields = self._get_create_schema_fields(
                    working_fields, model_pk
                )
                self.update_schema = SchemaFactory.create_schema(
                    self.model,
                    fields=list(create_schema_fields),
                    **(self.schema_config.extra_config_dict or {}),
                )

        if not self.patch_schema and "patch" in self.allowed_routes:
            create_schema_fields = self._get_create_schema_fields(
                working_fields, model_pk
            )
            self.patch_schema = SchemaFactory.create_schema(
                self.model,
                name=f"{_model_name}PatchSchema",
                fields=list(create_schema_fields),
                optional_fields=list(create_schema_fields),
                skip_registry=True,
                depth=self.schema_config.depth,
                **(self.schema_config.extra_config_dict or {}),
            )

        if not self.retrieve_schema:
            retrieve_schema_fields = self._get_retrieve_schema_fields(
                working_fields, model_pk
            )
            self.retrieve_schema = SchemaFactory.create_schema(
                self.model,
                name=f"{_model_name}Schema",
                fields=list(retrieve_schema_fields),
                skip_registry=True,
                depth=self.schema_config.depth,
                **(self.schema_config.extra_config_dict or {}),
            )

    def _get_create_schema_fields(self, working_fields: set, model_pk: str) -> set:
        create_schema_fields = set(working_fields) - set(
            self.schema_config.read_only_fields or []
        )
        if self.schema_config.write_only_fields:
            invalid_key = (
                set(self.schema_config.write_only_fields) - create_schema_fields
            )
            if invalid_key:
                raise ConfigError(f"Field(s) {invalid_key} included to working fields.")
        return create_schema_fields - {model_pk}

    def _get_retrieve_schema_fields(self, working_fields: set, model_pk: str) -> set:
        retrieve_schema_fields = set(working_fields) - set(
            self.schema_config.write_only_fields or []
        )
        if self.schema_config.read_only_fields:
            invalid_key = (
                set(self.schema_config.read_only_fields) - retrieve_schema_fields
            )
            if invalid_key:
                raise ConfigError(f"Field(s) {invalid_key} included to working fields.")
        return set(list(retrieve_schema_fields) + [model_pk])

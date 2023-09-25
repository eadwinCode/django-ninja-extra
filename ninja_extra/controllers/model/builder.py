import typing as t

from ninja.orm.fields import TYPES

from ninja_extra.constants import ROUTE_FUNCTION

from .endpoints import ModelEndpointFactory
from .schemas import ModelConfig

try:
    from ninja_schema.errors import ConfigError
    from ninja_schema.orm.factory import SchemaFactory
    from ninja_schema.orm.model_schema import (
        ModelSchemaConfig,
        ModelSchemaConfigAdapter,
    )
except Exception:  # pragma: no cover
    ConfigError = ModelSchemaConfig = ModelSchemaConfigAdapter = SchemaFactory = None


if t.TYPE_CHECKING:
    from ..base import APIController, ModelControllerBase


class ModelControllerBuilder:
    def __init__(
        self,
        base_cls: t.Type["ModelControllerBase"],
        api_controller_instance: "APIController",
    ) -> None:
        assert base_cls.model_config
        self._config: ModelConfig = base_cls.model_config
        self._base_cls = base_cls
        self._api_controller_instance = api_controller_instance
        model_pk = getattr(
            self._config.model._meta.pk,
            "name",
            self._config.model._meta.pk.attname,  # type:ignore[union-attr]
        )
        internal_type = (
            self._config.model._meta.pk.get_internal_type()  # type:ignore[union-attr]
        )
        self._pk_type: t.Type = TYPES.get(internal_type, str)
        self._model_pk_name = model_pk
        self._model_name = self._config.model.__name__.replace("Model", "")

        self._retrieve_schema = self._config.retrieve_schema
        self._create_schema = self._config.create_schema
        self._update_schema = self._config.update_schema
        self._patch_schema = self._config.patch_schema

        self.generate_all_schema()

    def generate_all_schema(self) -> None:
        if not ModelSchemaConfig:  # pragma: no cover
            raise RuntimeError(
                "ninja-schema package is required for ModelControllerSchema generation.\n pip install ninja-schema"
            )

        model_config = ModelSchemaConfig(
            "dummy",
            ModelSchemaConfigAdapter(
                {"model": self._config.model, "ninja_schema_abstract": True}
            ),
        )
        all_fields = {f.name: f for f in model_config.model_fields()}.keys()
        working_fields = set(all_fields)

        if self._config.schema_config.include == "__all__":
            working_fields = set(all_fields)

        elif (
            self._config.schema_config.include
            and self._config.schema_config.include != "__all__"
        ):
            include_fields = set(self._config.schema_config.include)
            working_fields = include_fields

        elif self._config.schema_config.exclude:
            exclude_fields = set(self._config.schema_config.exclude)
            working_fields = working_fields - exclude_fields

        if not self._create_schema and "create" in self._config.allowed_routes:
            create_schema_fields = self._get_create_schema_fields(working_fields)
            self._create_schema = SchemaFactory.create_schema(
                self._config.model,
                name=f"{self._model_name}CreateSchema",
                fields=list(create_schema_fields),
                skip_registry=True,
                depth=self._config.schema_config.depth,
            )

        if not self._update_schema and "update" in self._config.allowed_routes:
            if self._create_schema:
                self._update_schema = self._create_schema
            else:
                create_schema_fields = self._get_create_schema_fields(working_fields)
                self._update_schema = SchemaFactory.create_schema(
                    self._config.model, fields=list(create_schema_fields)
                )

        if not self._patch_schema and "patch" in self._config.allowed_routes:
            create_schema_fields = self._get_create_schema_fields(working_fields)
            self._patch_schema = SchemaFactory.create_schema(
                self._config.model,
                name=f"{self._model_name}PatchSchema",
                fields=list(create_schema_fields),
                optional_fields=list(create_schema_fields),
                skip_registry=True,
                depth=self._config.schema_config.depth,
            )

        if not self._retrieve_schema:
            retrieve_schema_fields = self._get_retrieve_schema_fields(working_fields)
            self._retrieve_schema = SchemaFactory.create_schema(
                self._config.model,
                name=f"{self._model_name}Schema",
                fields=list(retrieve_schema_fields),
                skip_registry=True,
                depth=self._config.schema_config.depth,
            )

    def _get_create_schema_fields(self, working_fields: set) -> set:
        create_schema_fields = set(working_fields) - set(
            self._config.schema_config.read_only_fields or []
        )
        if self._config.schema_config.write_only_fields:
            invalid_key = (
                set(self._config.schema_config.write_only_fields) - create_schema_fields
            )
            if invalid_key:
                raise ConfigError(f"Field(s) {invalid_key} included to working fields.")
        return create_schema_fields - {self._model_pk_name}

    def _get_retrieve_schema_fields(self, working_fields: set) -> set:
        retrieve_schema_fields = set(working_fields) - set(
            self._config.schema_config.write_only_fields or []
        )
        if self._config.schema_config.read_only_fields:
            invalid_key = (
                set(self._config.schema_config.read_only_fields)
                - retrieve_schema_fields
            )
            if invalid_key:
                raise ConfigError(f"Field(s) {invalid_key} included to working fields.")
        return set(list(retrieve_schema_fields) + [self._model_pk_name])

    def _add_to_controller(self, func: t.Callable) -> None:
        route_function = getattr(func, ROUTE_FUNCTION)
        route_function.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(route_function)

    def _register_create_endpoint(self) -> None:
        create_item = ModelEndpointFactory.create(
            schema_in=self._create_schema,  # type: ignore[arg-type]
            schema_out=self._retrieve_schema,  # type: ignore[arg-type]
            url_name=f"{self._model_name}-create",
            description=f"Create {self._model_name} item",
            summary="Create an item",
        )

        self._add_to_controller(create_item)

    def _register_update_endpoint(self) -> None:
        _path = "/{%s:%s}" % (
            self._pk_type.__name__,
            self._model_pk_name,
        )

        update_item = ModelEndpointFactory.update(
            path=_path,
            lookup_param=self._model_pk_name,
            schema_in=self._update_schema,  # type: ignore[arg-type]
            schema_out=self._retrieve_schema,  # type: ignore[arg-type]
            url_name=f"{self._model_pk_name}-put",
            description=f"""Update {self._model_name} item by {self._model_pk_name}""",
            summary="Update an item",
        )

        self._add_to_controller(update_item)

    def _register_patch_endpoint(self) -> None:
        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_pk_name,
        )

        patch_item = ModelEndpointFactory.patch(
            path=_path,
            lookup_param=self._model_pk_name,
            schema_out=self._retrieve_schema,  # type: ignore[arg-type]
            schema_in=self._patch_schema,  # type: ignore[arg-type]
            url_name=f"{self._model_pk_name}-patch",
            description=f"""Patch {self._model_name} item by {self._model_pk_name}""",
            summary="Patch an item",
        )

        self._add_to_controller(patch_item)

    def _register_find_one_endpoint(self) -> None:
        _path = "/{%s:%s}" % (
            self._pk_type.__name__,
            self._model_pk_name,
        )

        get_item = ModelEndpointFactory.retrieve(
            path=_path,
            lookup_param=self._model_pk_name,
            schema_out=self._retrieve_schema,  # type: ignore[arg-type]
            url_name=f"{self._model_pk_name}-get-item",
            description=f"""Get {self._model_name} item by {self._model_pk_name}""",
            summary="Get a specific item",
        )

        self._add_to_controller(get_item)

    def _register_list_endpoint(self) -> None:
        paginate_kwargs: t.Dict[str, t.Any] = {
            "pagination_class": None,
            "pagination_response_schema": None,
        }
        if self._config.pagination:
            paginate_kwargs.update(
                pagination_class=self._config.pagination.klass,
                pagination_response_schema=self._config.pagination.pagination_schema,
            )
            if self._config.pagination.paginator_kwargs:
                paginate_kwargs.update(self._config.pagination.paginator_kwargs)

        list_items = ModelEndpointFactory.list(
            path="/",
            schema_out=self._retrieve_schema,  # type: ignore[arg-type]
            description=f"List {self._model_name} model items",
            url_name=f"{self._model_pk_name}-list",
            summary="List Items",
            **paginate_kwargs,
        )

        self._add_to_controller(list_items)

    def _register_delete_endpoint(self) -> None:
        _path = "/{%s:%s}" % (
            self._pk_type.__name__,
            self._model_pk_name,
        )

        delete_item = ModelEndpointFactory.delete(
            path=_path,
            lookup_param=self._model_pk_name,
            url_name=f"{self._model_pk_name}-delete",
            description=f"""Delete {self._model_name} item""",
            summary="Delete an item",
        )

        self._add_to_controller(delete_item)

    def register_model_routes(self) -> None:
        for action in self._config.allowed_routes:
            action_registration = getattr(self, f"_register_{action}_endpoint", None)

            if not action_registration:  # pragma: no cover
                raise Exception(
                    f"Route `{action}` action in `class[{self._base_cls.__name__}]` "
                    f"is not recognized as ModelController action"
                )
            action_registration()

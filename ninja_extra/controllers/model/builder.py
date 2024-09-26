import typing as t

from ninja.orm.fields import TYPES

from ninja_extra.constants import ROUTE_FUNCTION

from .endpoints import ModelAsyncEndpointFactory, ModelEndpointFactory
from .schemas import ModelConfig

if t.TYPE_CHECKING:
    from ..base import APIController, ModelControllerBase


class ModelControllerBuilder:
    """
    Model Controller Builder that controls model controller setup.
    """

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
            self._config.model._meta.pk.attname,
        )
        internal_type = self._config.model._meta.pk.get_internal_type()
        self._pk_type: t.Type = TYPES.get(internal_type, str)  # type:ignore[assignment]
        self._model_pk_name = model_pk
        self._model_name = self._config.model.__name__.replace("Model", "")

        self._retrieve_schema = self._config.retrieve_schema
        self._create_schema = self._config.create_schema
        self._update_schema = self._config.update_schema
        self._patch_schema = self._config.patch_schema

        self._route_factory: ModelEndpointFactory = (
            ModelAsyncEndpointFactory()
            if base_cls.model_config.async_routes
            else ModelEndpointFactory()
        )

    def _add_to_controller(self, func: t.Callable) -> None:
        route_function = getattr(func, ROUTE_FUNCTION)
        route_function.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(route_function)

    def _register_create_endpoint(self) -> None:
        kw = {
            "url_name": f"{self._model_name.lower()}-create",
            "description": f"Create {self._model_name} item",
            "summary": "Create an item",
        }
        kw.update(self._config.create_route_info)
        create_item = self._route_factory.create(
            schema_in=self._create_schema,  # type:ignore[arg-type]
            schema_out=self._retrieve_schema,  # type:ignore[arg-type]
            **kw,  # type:ignore[arg-type]
        )

        self._add_to_controller(create_item)

    def _register_update_endpoint(self) -> None:
        _path = "/{%s:%s}" % (
            self._pk_type.__name__.lower(),
            self._model_pk_name,
        )
        kw = {
            "url_name": f"{self._model_name.lower()}-put",
            "description": f"""Update {self._model_name} item by {self._model_pk_name}""",
            "summary": "Update an item",
        }
        kw.update(self._config.update_route_info)

        update_item = self._route_factory.update(
            path=_path,
            lookup_param=self._model_pk_name,
            schema_in=self._update_schema,  # type:ignore[arg-type]
            schema_out=self._retrieve_schema,  # type:ignore[arg-type]
            **kw,  # type:ignore[arg-type]
        )

        self._add_to_controller(update_item)

    def _register_patch_endpoint(self) -> None:
        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__.lower(),
            self._model_pk_name,
        )

        kw = {
            "url_name": f"{self._model_name.lower()}-patch",
            "description": f"""Patch {self._model_name} item by {self._model_pk_name}""",
            "summary": "Patch an item",
        }
        kw.update(self._config.patch_route_info)

        patch_item = self._route_factory.patch(
            path=_path,
            lookup_param=self._model_pk_name,
            schema_out=self._retrieve_schema,  # type:ignore[arg-type]
            schema_in=self._patch_schema,  # type:ignore[arg-type]
            **kw,  # type:ignore[arg-type]
        )

        self._add_to_controller(patch_item)

    def _register_find_one_endpoint(self) -> None:
        _path = "/{%s:%s}" % (
            self._pk_type.__name__.lower(),
            self._model_pk_name,
        )
        kw = {
            "url_name": f"{self._model_name.lower()}-get-item",
            "description": f"""Get {self._model_name} item by {self._model_pk_name}""",
            "summary": "Get a specific item",
        }
        kw.update(self._config.find_one_route_info)

        get_item = self._route_factory.find_one(
            path=_path,
            lookup_param=self._model_pk_name,
            schema_out=self._retrieve_schema,  # type:ignore[arg-type]
            **kw,  # type:ignore[arg-type]
        )

        self._add_to_controller(get_item)

    def _register_list_endpoint(self) -> None:
        kw = {
            "description": f"List {self._model_name} model items",
            "url_name": f"{self._model_name.lower()}-list",
            "summary": "List Items",
        }
        kw.update(self._config.list_route_info)
        paginate_kwargs: t.Dict[str, t.Any] = {
            "pagination_class": None,
            "pagination_response_schema": None,
        }
        if self._config.pagination:
            paginate_kwargs.update(
                pagination_class=self._config.pagination.klass,
                pagination_response_schema=self._config.pagination.pagination_schema,
            )
            if self._config.pagination.paginator_kwargs:  # pragma: no cover
                paginate_kwargs.update(self._config.pagination.paginator_kwargs)

        list_items = self._route_factory.list(
            path="/",
            schema_out=self._retrieve_schema,  # type:ignore[arg-type]
            **kw,  # type:ignore[arg-type]
            **paginate_kwargs,
        )

        self._add_to_controller(list_items)

    def _register_delete_endpoint(self) -> None:
        _path = "/{%s:%s}" % (
            self._pk_type.__name__.lower(),
            self._model_pk_name,
        )
        kw = {
            "url_name": f"{self._model_name.lower()}-delete",
            "description": f"""Delete {self._model_name} item""",
            "summary": "Delete an item",
        }
        kw.update(self._config.delete_route_info)

        delete_item = self._route_factory.delete(
            path=_path,
            lookup_param=self._model_pk_name,
            **kw,  # type:ignore[arg-type]
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

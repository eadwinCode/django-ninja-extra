import typing as t

from ninja.orm.fields import TYPES
from ninja.params import Body, Path

from .. import status
from ..exceptions import NotFound
from ..pagination import paginate
from .route import route

if t.TYPE_CHECKING:
    from .base import APIController, ModelControllerBase


class ModelControllerBuilder:
    model_allowed_routes_actions = [
        "create",
        "read",
        "update",
        "patch",
        "delete",
        "list",
    ]

    def __init__(
        self,
        base_cls: t.Type["ModelControllerBase"],
        api_controller_instance: "APIController",
    ) -> None:
        self._config = base_cls.model_config
        self._base_cls = base_cls
        self._api_controller_instance = api_controller_instance
        model_pk = getattr(
            self._config.model._meta.pk,
            "name",
            self._config.model._meta.pk.attname,
        )
        internal_type = self._config.model._meta.pk.get_internal_type()
        self._pk_type: t.Type = TYPES.get(internal_type, str)
        self._model_name = model_pk

    def _register_create_endpoint(self) -> None:
        create_schema_in = self._config.create_schema
        create_schema_out = self._config.create_schema.get_out_schema()

        @route.post(
            "/",
            response={201: create_schema_out},
            url_name=f"{self._model_name}-create",
        )
        def create_item(
            self: "ModelControllerBase", data: create_schema_in = Body(default=...)
        ):
            instance = self.service.create(data)
            assert instance, "`service.create` must return a value"
            return instance

        create_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(create_item)

    def _register_update_endpoint(self) -> None:
        update_schema_in = self._config.update_schema
        update_schema_out = self._config.update_schema.get_out_schema()

        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_name,
        )

        @route.put(
            _path,
            response={200: update_schema_out},
            url_name=f"{self._model_name}-put",
        )
        def update_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
            data: update_schema_in = Body(default=...),
        ):
            obj = self.service.get_one(pk=pk)
            if not obj:
                raise NotFound()
            self.check_object_permissions(obj)
            instance = self.service.update(instance=obj, schema=data)
            assert instance, "`service.update` must return a value"
            return instance

        update_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(update_item)

    def _register_patch_endpoint(self) -> None:
        update_schema_in = self._config.update_schema
        update_schema_out = self._config.update_schema.get_out_schema()

        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_name,
        )

        @route.patch(
            _path,
            response={200: update_schema_out},
            url_name=f"{self._model_name}-patch",
        )
        def patch_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
            data: update_schema_in = Body(default=...),
        ):
            obj = self.service.get_one(pk=pk)
            if not obj:
                raise NotFound()
            self.check_object_permissions(obj)
            instance = self.service.patch(instance=obj, schema=data)
            assert instance, "`perform_patch()` must return a value"
            return instance

        patch_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(patch_item)

    def _register_get_endpoint(self) -> None:
        retrieve_schema = self._config.retrieve_schema
        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_name,
        )

        @route.get(
            _path,
            response={200: retrieve_schema},
            url_name=f"{self._model_name}-get-item",
        )
        def get_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
        ):
            obj = self.service.get_one(pk=pk)
            if not obj:
                raise NotFound()
            self.check_object_permissions(obj)
            return obj

        get_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(get_item)

    def _register_list_endpoint(self) -> None:
        paginate_kwargs = {}
        pagination_response_schema = self._config.pagination.schema
        pagination_class = self._config.pagination.klass
        retrieve_schema = self._config.retrieve_schema
        if self._config.pagination.paginate_by:
            paginate_kwargs.update(page_size=self._config.pagination.paginate_by)

        @route.get(
            "/",
            response={200: pagination_response_schema[retrieve_schema]},
            url_name=f"{self._model_name}-list",
        )
        @paginate(pagination_class, **paginate_kwargs)
        def list_items(self: "ModelControllerBase"):
            return self.service.get_all()

        list_items.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(list_items)

    def _register_delete_endpoint(self) -> None:
        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_name,
        )

        @route.delete(
            _path,
            url_name=f"{self._model_name}-delete",
            response={204: str},
        )
        def delete_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
        ):
            obj = self.service.get_one(pk=pk)
            if not obj:
                raise NotFound()
            self.check_object_permissions(obj)
            self.service.delete(instance=obj)
            return self.create_response(
                message="", status_code=status.HTTP_204_NO_CONTENT
            )

        delete_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(delete_item)

    def register_model_routes(self) -> None:
        for action in self._config.allowed_routes:
            action_registration = self.__dict__.get(
                f"_register_{action}_endpoint", None
            )
            if not action_registration:
                raise Exception(
                    f"Route `{action}` action in `class[{self._base_cls.__name__}]` "
                    f"is not recognized as ModelController action"
                )
            action_registration()

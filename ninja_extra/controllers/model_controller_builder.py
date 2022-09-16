import typing as t

from ninja.orm.fields import TYPES
from ninja.params import Body, Path
from pydantic import BaseModel as PydanticModel

from .. import status
from ..constants import DELETE, GET, PATCH, POST, PUT
from ..pagination import paginate
from .response import Detail
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
        controller_base_cls: t.Type["ModelControllerBase"],
        api_controller_instance: "APIController",
    ) -> None:
        self._base_cls = controller_base_cls
        self._api_controller_instance = api_controller_instance
        self._pagination_class = controller_base_cls.pagination_class
        self._allowed_routes = (
            self._base_cls.allowed_routes or self.model_allowed_routes_actions
        )
        self._create_schema: t.Type[PydanticModel] = (
            controller_base_cls.create_schema or controller_base_cls.model_schema
        )

        self._update_schema: t.Type[PydanticModel] = (
            controller_base_cls.update_schema or controller_base_cls.model_schema
        )
        self._model_schema = controller_base_cls.model_schema
        model_pk = getattr(
            controller_base_cls.model._meta.pk,
            "name",
            getattr(controller_base_cls.model._meta.pk, "attname"),
        )
        internal_type = controller_base_cls.model._meta.pk.get_internal_type()
        self._pk_type: t.Type = TYPES.get(internal_type, str)
        self._model_name = model_pk

    def _register_create_endpoint(self) -> None:
        create_schema = self._create_schema

        @route.post(
            "/",
            response={201: self._model_schema},
            url_name=f"{self._model_name}-create",
        )
        def create_item(
            self: "ModelControllerBase", data: create_schema = Body(default=...)
        ):
            instance = self.perform_create(data)
            assert instance, "`perform_create()` must return a value"
            return instance

        create_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(create_item)

    def _register_update_endpoint(self) -> None:
        update_schema = self._update_schema
        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_name,
        )

        @route.put(
            _path,
            response={200: self._model_schema},
            url_name=f"{self._model_name}-put",
        )
        def update_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
            data: update_schema = Body(default=...),
        ):
            obj = self.get_object_or_exception(self.model, pk=pk)
            self.check_object_permissions(obj)
            instance = self.perform_update(instance=obj, schema=data)
            assert instance, "`perform_update()` must return a value"
            return instance

        update_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(update_item)

    def _register_patch_endpoint(self) -> None:
        patch_update_schema = self._update_schema
        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_name,
        )

        @route.patch(
            _path,
            response={200: self._model_schema},
            url_name=f"{self._model_name}-patch",
        )
        def patch_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
            data: patch_update_schema = Body(default=...),
        ):
            obj = self.get_object_or_exception(self.model, pk=pk)
            self.check_object_permissions(obj)
            instance = self.perform_patch(instance=obj, schema=data)
            assert instance, "`perform_patch()` must return a value"
            return instance

        patch_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(patch_item)

    def _register_get_endpoint(self) -> None:
        _pk_type = self._pk_type
        _path = "/{%s:%s}" % (
            _pk_type.__name__,
            self._model_name,
        )

        @route.get(
            _path,
            response={200: self._model_schema},
            url_name=f"{self._model_name}-get-item",
        )
        def get_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
        ):
            res = self.get_object_or_exception(self.model, pk=pk)
            self.check_object_permissions(res)
            return res

        get_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(get_item)

    def _register_list_endpoint(self) -> None:
        paginate_kwargs = dict()
        if self._base_cls.paginate_by:
            paginate_kwargs.update(page_size=self._base_cls.paginate_by)

        @route.get(
            "/",
            response={
                200: self._base_cls.pagination_response_schema[self._model_schema]
            },
            url_name=f"{self._model_name}-list",
        )
        @paginate(self._pagination_class, **paginate_kwargs)
        def list_items(self: "ModelControllerBase"):
            return self.get_queryset()

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
            response=Detail(status_code=204),
        )
        def delete_item(
            self: "ModelControllerBase",
            pk: _pk_type = Path(default=..., alias=self._model_name),
        ):
            obj = self.get_object_or_exception(self.model, pk=pk)
            self.check_object_permissions(obj)
            self.perform_delete(instance=obj)
            return self.Detail(message="", status_code=status.HTTP_204_NO_CONTENT)

        delete_item.api_controller = self._api_controller_instance
        self._api_controller_instance.add_controller_route_function(delete_item)

    def register_model_routes(self) -> None:
        assert isinstance(
            self._allowed_routes, list
        ), f"`class[{self._base_cls.__name__}].allowed_routes must be a list of strings`"
        for action in self._allowed_routes:
            action_registration = self.__dict__.get(
                f"_register_{action}_endpoint", None
            )
            if not action_registration:
                raise Exception(
                    f"`{action}` action in `class[{self._base_cls.__name__}]` "
                    f"is not recognized as ModelController action"
                )
            action_registration()

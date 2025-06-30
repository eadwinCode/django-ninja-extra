# core/ninja_mixins.py
"""
Enhanced Django Ninja Extra mixins for programmatic API controller configuration.

This module provides a mixin-based approach to defining API controllers where
routes are automatically created as actual methods with decorators.
"""

from __future__ import annotations

import abc
import re
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Optional, TypeVar, cast

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Choices, IntegerChoices, QuerySet
from django.db.models import Model as DjangoModel
from ninja import Schema
from ninja.orm import create_schema, fields
from pydantic import BaseModel

from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelEndpointFactory,
)
from ninja_extra.controllers.model.endpoints import ModelEndpointFunction
from ninja_extra.ordering import Ordering, ordering


class ModelMixinBase(abc.ABC):
    """
    Abstract base class for route mixins.

    Each mixin defines route generation methods that create actual API endpoints.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Process mixins and create routes when subclass is created."""

        super().__init_subclass__(**kwargs)

        # Only process if this is a final controller class (not intermediate mixin)
        if issubclass(cls, MixinModelControllerBase) and issubclass(
            cls, ModelMixinBase
        ):
            cls._process_mixins()

    def __provides__(
        self,
    ) -> None:
        """
        Don't understand exactly why, but this is needed, otherwise `ninja_extra\\controllers\\model\builder.py", line 201, in register_model_routes` crashes.
        """
        return  # pragma: no cover

    @classmethod
    @abstractmethod
    def create_routes(cls, controller_cls: type[MixinModelControllerBase]) -> None:
        """Create routes for the given controller class."""
        ...

    @classmethod
    def _process_mixins(cls) -> None:
        """Process all mixins and create their routes."""
        mixin_classes = [
            base
            for base in cls.__mro__
            if (
                issubclass(base, ModelMixinBase)
                and base not in (cls, ModelControllerBase, ModelMixinBase)
            )
        ]

        assert issubclass(cls, MixinModelControllerBase), (
            f"{cls} must inherit from MixinModelControllerBase"
        )

        for mixin in mixin_classes:
            mixin.create_routes(cls)


class IntegerChoicesSchema(Schema):
    """
    Schema for IntegerChoices.
    """

    id: int
    label: str


class TextChoicesSchema(Schema):
    """
    Schema for TextChoices.
    """

    id: str
    label: str


class MixinTextChoiceModel(models.Model):
    """
    Dummy model class for TextChoices.
    """

    id = models.CharField(
        max_length=255, primary_key=True, null=False, blank=False, unique=True
    )
    label = models.TextField(max_length=255, null=False, blank=True)

    class Meta:
        managed = False


class MixinIntegerChoiceModel(models.Model):
    """
    Dummy model class for IntegerChoices.
    """

    id = models.IntegerField(primary_key=True, null=False, blank=False, unique=True)
    label = models.TextField(max_length=255, null=False, blank=True)

    class Meta:
        managed = False


class MixinModelControllerBase(ModelControllerBase):
    """
    Enhanced ModelControllerBase that works with programmatic route creation.
    """

    input_schema: ClassVar[type[BaseModel] | None] = None
    output_schema: ClassVar[type[BaseModel] | None] = None
    model_class: ClassVar[type[DjangoModel]]
    auto_operation_ids: ClassVar[bool] = True
    operation_id_prefix: ClassVar[str | None] = None
    filter_schema: ClassVar[type[Schema] | None] = None
    ordering_fields: ClassVar[list[str]] = []
    lookup_field: ClassVar[str | None] = None

    retrieve: ClassVar[Optional[ModelEndpointFunction]]
    list: ClassVar[Optional[ModelEndpointFunction]]
    create: ClassVar[Optional[ModelEndpointFunction]]
    update: ClassVar[Optional[ModelEndpointFunction]]
    patch: ClassVar[Optional[ModelEndpointFunction]]
    delete: ClassVar[Optional[ModelEndpointFunction]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Configure the controller."""

        if not hasattr(cls, "model_class") and not getattr(cls, "model_config", None):
            msg = f"Controller {cls.__name__} must define a model_class attribute"
            raise ImproperlyConfigured(msg)

        if hasattr(cls, "model_config") and cls.model_config and cls.model_config.model:
            cls.model_class = cls.model_config.model

        cls._setup()

        super().__init_subclass__(**kwargs)

    @classmethod
    def _setup(cls) -> None:
        cls._configure_schemas()
        cls._ensure_model_config()

        if cls.lookup_field is None:
            meta = getattr(cls.model_class, "_meta", None)
            pk = getattr(meta, "pk", None)

            pk_name = pk.attname if pk else "id"
            _type = fields.TYPES.get(pk.get_internal_type()) if pk else None
            pk_type = _type.__name__ if _type and hasattr(_type, "__name__") else "int"
            cls.lookup_field = f"{{{pk_type}:{pk_name}}}"

    @classmethod
    def _configure_schemas(cls) -> None:
        """
        Configure `input_schema` and `output_schema` where applicable.
        """

        is_choices = issubclass(cls.model_class, Choices)
        is_integer_choices = is_choices and issubclass(cls.model_class, IntegerChoices)
        if cls.output_schema is None:
            if is_choices:
                cls.output_schema = (
                    IntegerChoicesSchema if is_integer_choices else TextChoicesSchema
                )
            else:
                cls.output_schema = create_schema(cls.model_class)
        if not is_choices and cls.input_schema is None:
            cls.input_schema = create_schema(cls.model_class, exclude=["id"])

        if is_choices:
            model_class = (
                MixinIntegerChoiceModel if is_integer_choices else MixinTextChoiceModel
            )
            cls.model_config = ModelConfig(model=model_class)

    @classmethod
    def _ensure_model_config(cls) -> None:
        """Ensure ModelConfig is properly set up for dependency injection."""
        if not hasattr(cls, "model_config") or not cls.model_config:
            cls.model_config = ModelConfig(model=cls.model_class)
        elif not cls.model_config.model:
            cls.model_config.model = cls.model_class
        cls.model_config.allowed_routes = []

    @classmethod
    def generate_operation_id(cls, operation: str) -> str:
        """Generate operation_id for the given operation."""
        prefix = cls.operation_id_prefix or cls._generate_operation_id_prefix()
        return f"{operation}{_to_pascal_case(prefix)}"

    @classmethod
    def _generate_operation_id_prefix(cls) -> str:
        """Generate operation_id prefix from controller class name."""
        class_name = cls.__name__
        if class_name.endswith("Controller"):
            base_name = class_name[:-10]
        elif class_name.endswith("API"):
            base_name = class_name[:-3]
        else:
            base_name = class_name
        return _to_snake_case(base_name)


T = TypeVar("T", bound=Schema)


class RetrieveModelMixin(ModelMixinBase):
    """Mixin for retrieving a single model instance by ID."""

    @classmethod
    def create_routes(cls, controller_cls: type[MixinModelControllerBase]) -> None:
        """Create the retrieve route."""
        operation_id = (
            controller_cls.generate_operation_id("get")
            if controller_cls.auto_operation_ids
            else None
        )

        assert controller_cls.output_schema

        controller_cls.retrieve = ModelEndpointFactory.find_one(
            path=f"/{controller_cls.lookup_field}",
            operation_id=operation_id,
            schema_out=controller_cls.output_schema,
            lookup_param="id",
        )


class ListModelMixin(ModelMixinBase):
    """
    Enhanced list mixin that allows for custom parameters and queryset manipulation.
    """

    @classmethod
    def create_routes(cls, controller_cls: type[MixinModelControllerBase]) -> None:
        """Create the enhanced list route."""
        # Prevent this basic mixin from overwriting a more specific one.
        if hasattr(controller_cls, "list"):
            return

        if not controller_cls.output_schema:
            msg = f"{controller_cls.__name__} must define an 'output_schema' for the ListModelMixin to work."
            raise ImproperlyConfigured(msg)

        operation_id = (
            controller_cls.generate_operation_id("list")
            if controller_cls.auto_operation_ids
            else None
        )

        # TODO(mbo20): refactor into separate ChoideModelMixin class
        if issubclass(controller_cls.model_class, models.Choices):
            assert hasattr(controller_cls.model_class, "choices")
            choices = controller_cls.model_class.choices
            is_integer_choices = issubclass(controller_cls.model_class, IntegerChoices)
            choice_class = (
                MixinIntegerChoiceModel if is_integer_choices else MixinTextChoiceModel
            )

            # noinspection PyUnusedLocal
            def get_choices(self: MixinModelControllerBase) -> list:  #  noqa: ARG001
                mapped = [(choice[0], str(choice[1])) for choice in choices]
                choices_sorted = sorted(mapped, key=lambda t: t[1])
                return [choice_class(id=k, label=v) for (k, v) in choices_sorted]

            controller_cls.list = ModelEndpointFactory.list(
                path="/",
                operation_id=operation_id,
                tags=[controller_cls.model_class.__name__],
                schema_out=controller_cls.output_schema,
                queryset_getter=get_choices,  # type: ignore[arg-type]
            )

        else:

            @ordering(Ordering)
            def list_all(
                self: MixinModelControllerBase,
            ) -> QuerySet:
                return self.service.get_all()

            def list_ordered(
                self: MixinModelControllerBase,
            ) -> QuerySet:
                ctx = self.context
                ordering_args = (
                    ctx.request.GET.getlist("ordering", [])
                    if ctx and ctx.request and ctx.request.method == "GET"
                    else []
                )
                ordering_input = Ordering().Input(ordering=",".join(ordering_args))
                return cast(
                    QuerySet, list_all(self, ordering=ordering_input)
                )  # todo: why is this cast needed? Without it, mypy is unhappy.

            assert controller_cls.output_schema
            controller_cls.list = ModelEndpointFactory.list(
                path="/",
                operation_id=operation_id,
                tags=[controller_cls.model_class.__name__],
                schema_out=controller_cls.output_schema,
                queryset_getter=list_ordered,
            )


class CreateModelMixin(ModelMixinBase):
    """Mixin for creating new model instances."""

    @classmethod
    def create_routes(cls, controller_cls: type[MixinModelControllerBase]) -> None:
        """Create the create route."""
        operation_id = (
            controller_cls.generate_operation_id("create")
            if controller_cls.auto_operation_ids
            else None
        )

        assert controller_cls.input_schema
        assert controller_cls.output_schema
        controller_cls.create = ModelEndpointFactory.create(
            path="/",
            operation_id=operation_id,
            tags=[controller_cls.model_class.__name__],
            schema_in=controller_cls.input_schema,
            schema_out=controller_cls.output_schema,
        )


class PutModelMixin(ModelMixinBase):
    """Mixin for full updates of model instances (PUT)."""

    @classmethod
    def create_routes(cls, controller_cls: type[MixinModelControllerBase]) -> None:
        """Create the update route."""
        operation_id = (
            controller_cls.generate_operation_id("update")
            if controller_cls.auto_operation_ids
            else None
        )

        assert controller_cls.input_schema
        assert controller_cls.output_schema
        controller_cls.update = ModelEndpointFactory.update(
            path=f"/{controller_cls.lookup_field}",
            operation_id=operation_id,
            tags=[controller_cls.model_class.__name__],
            schema_in=controller_cls.input_schema,
            schema_out=controller_cls.output_schema,
            lookup_param="id",
        )


class PatchModelMixin(ModelMixinBase):
    """Mixin for partial updates of model instances (PATCH)."""

    @classmethod
    def create_routes(cls, controller_cls: type[MixinModelControllerBase]) -> None:
        """Create the patch route."""
        operation_id = (
            controller_cls.generate_operation_id("patch")
            if controller_cls.auto_operation_ids
            else None
        )

        patch_schema = (
            create_schema(  # see: https://github.com/vitalik/django-ninja/issues/1183
                controller_cls.model_class,
                exclude=["id"],
                optional_fields="__all__",  # type: ignore
            )
        )

        assert controller_cls.output_schema
        controller_cls.patch = ModelEndpointFactory.patch(
            path=f"/{controller_cls.lookup_field}",
            operation_id=operation_id,
            tags=[controller_cls.model_class.__name__],
            schema_in=patch_schema,
            schema_out=controller_cls.output_schema,
            lookup_param="id",
        )


class DeleteModelMixin(ModelMixinBase):
    """Mixin for deleting model instances."""

    @classmethod
    def create_routes(cls, controller_cls: type[MixinModelControllerBase]) -> None:
        """Create the delete route."""
        operation_id = (
            controller_cls.generate_operation_id("delete")
            if controller_cls.auto_operation_ids
            else None
        )

        controller_cls.delete = ModelEndpointFactory.delete(
            path=f"/{controller_cls.lookup_field}",
            operation_id=operation_id,
            tags=[controller_cls.model_class.__name__],
            lookup_param="id",
        )


class ReadModelMixin(RetrieveModelMixin, ListModelMixin):
    """Convenience mixin for read-only operations (retrieve + list)."""


class UpdateModelMixin(PatchModelMixin, PutModelMixin):
    """Convenience mixin for update operations."""


class CRUDModelMixin(
    CreateModelMixin, ReadModelMixin, UpdateModelMixin, DeleteModelMixin
):
    """Convenience mixin for CRUD operations (retrieve + update + delete)."""


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))

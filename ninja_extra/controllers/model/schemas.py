from typing import Any, Generic, List, Optional, Set, Type, Union

from django.db.models import Model
from ninja.pagination import PaginationBase
from pydantic import BaseModel as PydanticModel
from pydantic import Field, validator

from ...pagination import PageNumberPaginationExtra, PaginatedResponseSchema


class ModelPagination(PydanticModel):
    klass: Type[PaginationBase] = PageNumberPaginationExtra
    paginator_kwargs: Optional[dict] = None
    pagination_schema: Type[PydanticModel] = PaginatedResponseSchema

    @validator("klass", allow_reuse=True)
    def validate_klass(cls, value: Any) -> Any:
        if isinstance(value, type) and issubclass(value, PaginationBase):
            return value
        raise ValueError(f"{value} is not of type `PaginationBase`")

    @validator("pagination_schema", allow_reuse=True)
    def validate_schema(cls, value: Any) -> Any:
        if (
            isinstance(value, type)
            and issubclass(value, PydanticModel)
            and issubclass(value, Generic)  # type:ignore[arg-type]
        ):
            return value
        raise ValueError(
            f"{value} is not a valid type. Please use a generic pydantic model."
        )


class ModelSchemaConfig(PydanticModel):
    include: Union[str, List[str]] = Field(default="__all__")
    exclude: Set[str] = Field(set())
    optional: Union[str, Set[str]] = Field(default=None)
    depth: int = 0
    #
    read_only_fields: Optional[List[str]] = Field(default=None)
    write_only_fields: Optional[Union[List[str]]] = Field(default=None)


class ModelConfig(PydanticModel):
    allowed_routes: List[str] = Field(
        [
            "create",
            "find_one",
            "update",
            "patch",
            "delete",
            "list",
        ]
    )

    create_schema: Optional[Type[PydanticModel]] = None
    retrieve_schema: Optional[Type[PydanticModel]] = None
    update_schema: Optional[Type[PydanticModel]] = None
    patch_schema: Optional[Type[PydanticModel]] = None

    pagination: Optional[ModelPagination] = Field(default=ModelPagination())
    model: Type[Model]

    schema_config: ModelSchemaConfig = Field(default=ModelSchemaConfig(exclude=set()))

    @validator("allowed_routes", allow_reuse=True)
    def validate_allow_routes(cls, value: List[Any]) -> Any:
        defaults = ["create", "find_one", "update", "patch", "delete", "list"]
        for item in value:
            if item not in defaults:
                raise ValueError(f"'{item}' action is not recognized in [{defaults}]")
        return value

    @validator("model", allow_reuse=True)
    def validate_model(cls, value: Any) -> Any:
        if value and hasattr(value, "objects"):
            return value
        raise ValueError(f"{value} is not a valid Django model.")

    @validator(
        "create_schema",
        "retrieve_schema",
        "update_schema",
        "patch_schema",
        allow_reuse=True,
    )
    def validate_schemas(cls, value: Any) -> Any:
        if value and not issubclass(value, PydanticModel):
            raise ValueError(f"{value} is not a valid pydantic type.")
        return value

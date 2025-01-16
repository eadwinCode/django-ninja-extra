# Model Configuration

The `ModelConfig` class in Ninja Extra provides extensive configuration options for Model Controllers. It allows you to customize schema generation, route behavior, and pagination settings.

## **Basic Configuration**

Here's a comprehensive example of `ModelConfig` usage:

```python
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
)
from .models import Event

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        schema_config=ModelSchemaConfig(
            read_only_fields=["id", "created_at"],
            write_only_fields=["password"],
            include=["title", "start_date", "end_date", "category"],
            exclude=set(),  # Fields to exclude
            depth=1,  # Nesting depth for related fields
        ),
        async_routes=False,  # Enable/disable async routes
        allowed_routes=["create", "find_one", "update", "patch", "delete", "list"],
    )
```

## **Schema Configuration**

The `ModelSchemaConfig` class controls how Pydantic schemas are generated from your Django models:

```python
from ninja_extra import ModelConfig, ModelSchemaConfig

# Detailed schema configuration
schema_config = ModelSchemaConfig(
    # Include specific fields (use "__all__" for all fields)
    include=["title", "description", "start_date"],
    
    # Exclude specific fields
    exclude={"internal_notes", "secret_key"},
    
    # Fields that should be read-only (excluded from create/update schemas)
    read_only_fields=["id", "created_at", "updated_at"],
    
    # Fields that should be write-only (excluded from retrieve schemas)
    write_only_fields=["password"],
    
    # Depth of relationship traversal
    depth=1,
    
    # Additional Pydantic config options
    extra_config_dict={
        "title": "EventSchema",
        "description": "Schema for Event model",
        "populate_by_name": True
    }
)

model_config = ModelConfig(
    model=Event,
    schema_config=schema_config
)
```

## **Custom Schemas**

You can provide your own Pydantic schemas instead of using auto-generated ones:

```python
from datetime import date
from pydantic import BaseModel, Field

class EventCreateSchema(BaseModel):
    title: str = Field(..., max_length=100)
    start_date: date
    end_date: date
    category_id: int | None = None

class EventRetrieveSchema(BaseModel):
    id: int
    title: str
    start_date: date
    end_date: date
    category_id: int | None

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        create_schema=EventCreateSchema,
        retrieve_schema=EventRetrieveSchema,
        update_schema=EventCreateSchema,  # Reuse create schema for updates
    )
```

## **Pagination Configuration**

Model Controllers support customizable pagination for list endpoints:

```python
from ninja.pagination import LimitOffsetPagination
from ninja_extra import (
    ModelConfig,
    ModelPagination
)
from ninja_extra.pagination import NinjaPaginationResponseSchema

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        # Configure pagination
        pagination=ModelPagination(
            klass=LimitOffsetPagination,
            pagination_schema=NinjaPaginationResponseSchema,
            paginator_kwargs={
                "limit": 20,
                "offset": 100
            }
        )
    )
```

## **Route Configuration**

You can customize individual route behavior using route info dictionaries:

```python
@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        # Customize specific route configurations
        create_route_info={
            "summary": "Create a new event",
            "description": "Creates a new event with the provided data",
            "tags": ["events"],
            "deprecated": False,
        },
        list_route_info={
            "summary": "List all events",
            "description": "Retrieves a paginated list of all events",
            "tags": ["events"],
            "schema_out": CustomListSchema,
        },
        find_one_route_info={
            "summary": "Get event details",
            "description": "Retrieves details of a specific event",
            "tags": ["events"],
        }
    )
```

## **Async Routes Configuration**

Enable async routes and configure async behavior:

```python
@api_controller("/events")
class AsyncEventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        # Async-specific configurations
        async_routes=True,
        schema_config=ModelSchemaConfig(
            read_only_fields=["id"],
            depth=1
        )
    )
    
    # Custom async service implementation
    service = AsyncEventModelService(model=Event)
```

## **Configuration Inheritance**

ModelConfig also support configuration inheritance:

```python
from ninja_extra.controllers import ModelConfig

class BaseModelConfig(ModelConfig):
    async_routes = True
    schema_config = ModelSchemaConfig(
        read_only_fields=["id", "created_at", "updated_at"],
        depth=1
    )

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = BaseModelConfig(
        model=Event,
        # Override or extend base configuration
        allowed_routes=["list", "find_one"]
    )
```

## **Best Practices**

1. **Schema Configuration**:
    - Always specify `read_only_fields` for auto-generated fields
    - Use `depth` carefully as it can impact performance
    - Consider using `exclude` for sensitive fields

2. **Route Configuration**:
    - Limit `allowed_routes` to only necessary endpoints
    - Provide meaningful summaries and descriptions
    - Use tags for API organization

3. **Pagination**:
    - Always set reasonable limits
    - Consider your data size when choosing pagination class
    - Use appropriate page sizes for your use case

4. **Async Support**:
    - Enable `async_routes` when using async database operations
    - Implement custom async services for complex operations
    - Consider performance implications of async operations 

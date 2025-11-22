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

You can customize individual route behavior using route info dictionaries. Each route type (`create_route_info`, `list_route_info`, `find_one_route_info`, `update_route_info`, `patch_route_info`, `delete_route_info`) accepts various configuration parameters.

### **Common Route Parameters**

All route types support these common parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | varies by route | Custom path for the route |
| `status_code` | `int` | varies by route | HTTP status code for successful responses |
| `auth` | `Any` | NOT_SET | Authentication class or instance |
| `throttle` | `BaseThrottle \| List[BaseThrottle]` | NOT_SET | Throttle class(es) for rate limiting |
| `response` | `Any` | NOT_SET | Custom response configuration |
| `url_name` | `str \| None` | None | Django URL name for the route |
| `description` | `str \| None` | None | Detailed description for OpenAPI docs |
| `operation_id` | `str \| None` | None | Custom operation ID for OpenAPI |
| `summary` | `str \| None` | varies by route | Short summary for OpenAPI docs |
| `tags` | `List[str] \| None` | None | Tags for grouping in OpenAPI docs |
| `deprecated` | `bool \| None` | None | Mark route as deprecated in OpenAPI |
| `by_alias` | `bool` | False | Use schema field aliases in response |
| `exclude_unset` | `bool` | False | Exclude unset fields from response |
| `exclude_defaults` | `bool` | False | Exclude fields with default values |
| `exclude_none` | `bool` | False | Exclude None fields from response |
| `include_in_schema` | `bool` | True | Include route in OpenAPI schema |
| `permissions` | `List[BasePermission]` | None | Permission classes for the route |
| `openapi_extra` | `Dict[str, Any] \| None` | None | Extra OpenAPI schema properties |

### **Route-Specific Parameters**

#### **Create Route (`create_route_info`)**
- `custom_handler`: Custom handler function to override default create logic

#### **Update/Patch Routes (`update_route_info`, `patch_route_info`)**
- `object_getter`: Custom function to retrieve the object
- `custom_handler`: Custom handler function to override default update/patch logic

#### **Find One Route (`find_one_route_info`)**
- `object_getter`: Custom function to retrieve the object

#### **Delete Route (`delete_route_info`)**
- `object_getter`: Custom function to retrieve the object
- `custom_handler`: Custom handler function to override default delete logic

#### **List Route (`list_route_info`)**
- `queryset_getter`: Custom function to retrieve the queryset
- `pagination_response_schema`: Custom pagination response schema

### **Basic Example**

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
        },
        find_one_route_info={
            "summary": "Get event details",
            "description": "Retrieves details of a specific event",
            "tags": ["events"],
        }
    )
```

### **Advanced Configuration Example**

```python
from ninja_extra import status
from ninja_extra.permissions import IsAuthenticated, IsAdminUser
from ninja_extra.throttling import AnonRateThrottle

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        create_route_info={
            "summary": "Create a new event",
            "description": "Creates a new event with the provided data",
            "tags": ["events", "management"],
            "status_code": status.HTTP_201_CREATED,
            "permissions": [IsAuthenticated],
            "throttle": AnonRateThrottle(),
            "exclude_none": True,
            "openapi_extra": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "examples": {
                                "example1": {
                                    "summary": "Conference event",
                                    "value": {
                                        "title": "Tech Conference 2024",
                                        "start_date": "2024-06-01",
                                        "end_date": "2024-06-03"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        update_route_info={
            "summary": "Update event",
            "permissions": [IsAuthenticated, IsAdminUser],
            "exclude_unset": True,
        },
        delete_route_info={
            "summary": "Delete an event",
            "permissions": [IsAdminUser],
            "status_code": status.HTTP_204_NO_CONTENT,
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

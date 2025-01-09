# Getting Started with Model Controllers

Model Controllers in Ninja Extra provide a powerful way to automatically generate CRUD (Create, Read, Update, Delete) operations for Django ORM models. They simplify API development by handling common database operations while remaining highly customizable.

## **Installation**

First, ensure you have Ninja Extra and ninja-schema installed:

```bash
pip install django-ninja-extra ninja-schema
```

`ninja-schema` package is optional, but it's recommended for generating schemas.

## **Basic Usage**

Let's start with a simple example. Consider this Django model:

```python
from django.db import models

class Category(models.Model):
    title = models.CharField(max_length=100)

class Event(models.Model):
    title = models.CharField(max_length=100)
    category = models.OneToOneField(
        Category, null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='events'
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.title
```

To create a basic Model Controller for the Event model:

```python
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    api_controller,
    NinjaExtraAPI
)
from .models import Event

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
    )

# Register the controller with your API
api = NinjaExtraAPI()
api.register_controllers(EventModelController)
```

This simple setup automatically creates the following endpoints:

- `POST /events/` - Create a new event
- `GET /events/{id}` - Retrieve a specific event
- `PUT /events/{id}` - Update an event
- `PATCH /events/{id}` - Partially update an event
- `DELETE /events/{id}` - Delete an event
- `GET /events/` - List all events (with pagination)

It is important to that if `model_config.model` is not set, the controller becomes a regular NinjaExtra controller.

## **Generated Schemas**

The Model Controller automatically generates Pydantic schemas for your model using `ninja-schema`. These schemas handle:

- Input validation
- Output serialization
- Automatic documentation in the OpenAPI schema

For example, the generated schemas for our `Event` model would look like this:

```python
# Auto-generated create/update schema
class EventCreateSchema(Schema):
    title: str
    start_date: date
    end_date: date
    category: Optional[int] = None

# Auto-generated retrieve schema
class EventSchema(Schema):
    id: int
    title: str
    start_date: date
    end_date: date
    category: Optional[int] = None
```

## **Customizing Routes**

You can control which routes are generated using the `allowed_routes` parameter:

```python
@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        allowed_routes=["list", "find_one"]  # Only generate GET and GET/{id} endpoints
    )
```

## **Async Support**

Model Controllers support `async` operations out of the box. Just set `async_routes=True`:

```python
@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        async_routes=True  # Enable async routes
    )
```

## **Next Steps**

- Learn about [Model Configuration](02_model_configuration.md) for detailed schema and route customization
- Explore [Model Services](03_model_service.md) for customizing CRUD operations
- See how to use [Query and Path Parameters](04_parameters.md) effectively with `ModelEndpointFactory`

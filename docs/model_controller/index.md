# **Model APIController**
!!! Note
    `ModelController` is only available from **v0.19.5**

**Model Controllers** inherit from the `ControllerBase` class and provide two important variables: `model_config` and `model_service`. 
These variables guide the route generation, schema generation, and model operations.

For instance, let's create a ModelController for an Event model defined as follows:

Model Controllers inherits from `ControllerBase` class and provides and provides two important variables `model_config` and `model_service`, 
which guides its route generation, schema generation or model operations.

For example, Let's create `ModelController` for an `Event` model defined below,

```python
from django.db import models

class Category(models.Model):
    title = models.CharField(max_length=100)

class Event(models.Model):
    title = models.CharField(max_length=100)
    category = models.OneToOneField(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='events'
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.title

```
Then, in `api.py`, we create an `EventModelController`:

```python
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    NinjaExtraAPI
)
from .models import Event

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )
    
api = NinjaExtraAPI()
api.register_controllers(EventModelController)

```

Model Controllers require the `ninja-schema` package for auto schema generation, which can be installed with:
```shell
pip install ninja-schema
```

## **Model Configuration**
`ModelConfig` is a Pydantic schema used for validating and configuring Model Controller behaviors. Configuration options include:

- **model**: A required field that holds the Django model type for the Model Controller.
- **allowed_routes**: A list of API actions allowed to be generated in the Model Controller. The default value is `["create", "find_one", "update", "patch", "delete", "list"]`.
- **create_schema**: An optional Pydantic schema that describes the data input types for a `create` or `POST` operation in the Model Controller. The default value is `None`. If not provided, the `ModelController` will create a new schema based on the `schema_config` option.
- **update_schema**: An optional Pydantic schema that describes the data input types for an `update` or `PUT` operation in the Model Controller. The default value is `None`. If not provided, the `create_schema` will be used if available, or a new schema will be generated based on the `schema_config` option.
- **retrieve_schema**: An optional Pydantic schema output that describes the data output types for various operations. The default value is `None`. If not provided, the `ModelController` will generate a schema based on the `schema_config` option.
- **patch_schema**: An optional Pydantic schema output that describes the data input types for `patch/PATCH` operations. The default value is `None`. If not provided, the `ModelController` will generate a schema with all of its fields optional.
- **schema_config**: This is also a required field that describes how schema should be generated as required by Model Controller operations. Configuration options include:
    - `include`: List of Fields to be included. The default is `__all__`.
    - `exclude`: List of Fields to be excluded. The default is `[]`.
    - `optional`: List of Fields to be forced as optional. The default is `[pk]`.
    - `depth`: Depth to nest schema generation.
    - `read_only_fields`: List of fields to be excluded when generating input schemas for create, update, and patch operations.
    - `write_only_fields`: List of fields to be excluded when generating output schemas for find_one and list operations.
- **pagination**: This is required for the model `list/GET` operation to avoid sending `100_000` items at once in a request. The pagination configuration requires a `ModelPagination` Pydantic schema object to be configured. Options include:
    - `klass`: The pagination class of type `PaginationBase`. The default is `PageNumberPaginationExtra`.
    - `paginator_kwargs`: A dictionary value for `PaginationBase` initialization. The default is None.
    - `pagination_schema`: A Pydantic generic schema that will be combined with `retrieve_schema` to generate a response schema for `list/GET `operation.
   
    For example, if you want to use `ninja` pagination like `LimitOffsetPagination`:

    ```python
    from ninja.pagination import LimitOffsetPagination
    from ninja_extra.schemas import NinjaPaginationResponseSchema
    from ninja_extra import (
        ModelConfig,
        ModelControllerBase,
        api_controller,
        ModelPagination
    )
    
    @api_controller("/events")
    class EventModelController(ModelControllerBase):
        model_config = ModelConfig(
            model=Event,
            pagination=ModelPagination(
                klass=LimitOffsetPagination, 
                pagination_schema=NinjaPaginationResponseSchema
            ),
        )
    
    ```  

## **More on Model Controller Operations**
In NinjaExtra Model Controller, the controller's behavior can be controlled by what is provided in the `allowed_routes` list within the `model_config` option.

For example, you can create a read-only controller like this:

```python
from ninja_extra import api_controller, ModelControllerBase, ModelConfig, ModelSchemaConfig
from .models import Event

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        allowed_routes=['find_one', 'list'],
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )

```
This will only create `GET/{id}` and `GET/` routes for listing.

You can also add more endpoints to the existing `EventModelController`. For example:

```python
from ninja_extra import api_controller, http_get, ModelControllerBase, ModelConfig, ModelSchemaConfig
from .models import Event

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        allowed_routes=['find_one', 'list'],
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )

    @http_get('/subtract',)
    def subtract(self, a: int, b: int):
        """Subtracts a from b"""
        return {"result": a - b}

```

## **Model Service**
Every model controller has a `ModelService` instance created during runtime to manage model interaction with the controller. 
Usually, these model service actions would have been part of the model controller, 
but they are abstracted to a service to allow a more dynamic approach.

```python
class ModelService(ModelServiceBase):
    """
    Model Service for Model Controller model CRUD operations with simple logic for simple models.

    It's advised to override this class if you have a complex model.
    """
    def __init__(self, model: Type[DjangoModel]) -> None:
        self.model = model

    # ... (other CRUD methods)

```
These actions are called based on the ongoing action on the model controller or 
based on the request being handled by the model controller.

### **Using Custom Model Service**
Overriding a `ModelService` in a Model Controller is more important than overriding a route operation. 
The default `ModelService` used in the Model Controller is designed for simple Django models. 
It's advised to override the `ModelService` if you have a complex model.

For example, if you want to change the way the `Event` model is being saved:
```python
from ninja_extra import ModelService

class EventModelService(ModelService):
    def create(self, schema: PydanticModel, **kwargs: Any) -> Any:
        data = schema.dict(by_alias=True)
        data.update(kwargs)
        
        instance = self.model._default_manager.create(**data)
        return instance

        
```
And then in `api.py`
```python
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
)
from .service import EventModelService
from .models import Event

@api_controller("/events")
class EventModelController(ModelControllerBase):
    service = EventModelService(model=Event)
    model_config = ModelConfig(
        model=Event,
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )

```
### **ModelController and ModelService Together**
It's also possible to merge the controller and the model service together if needed:

For example, using the `EventModelService` we created
```python
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
)
from .service import EventModelService
from .models import Event

@api_controller("/events")
class EventModelController(ModelControllerBase, EventModelService):
    model_config = ModelConfig(
        model=Event,
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )
    
    def __init__(self):
        EventModelService.__init__(self, model=Event)
        self.service = self  # This will expose the functions to the service attribute

```

## **Model Endpoint Factory**
The `ModelEndpointFactory` is a factory class used by the Model Controller to generate endpoints seamlessly. 
It can also be used directly in any NinjaExtra Controller for the same purpose.

For example, if we want to add an `Event` to a new `Category`, we can do so as follows:
```python
from typing import Any
from pydantic import BaseModel
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    ModelEndpointFactory
)
from .models import Event, Category

class CreateCategorySchema(BaseModel):
    title: str

class CategorySchema(BaseModel):
    id: str
    title: str

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )

    add_event_to_new_category = ModelEndpointFactory.create(
        path="/{int:event_id}/new-category",
        schema_in=CreateCategorySchema,
        schema_out=CategorySchema,
        custom_handler=lambda self, data, **kw: self.handle_add_event_to_new_category(data, **kw)
    )

    def handle_add_event_to_new_category(self, data: CreateCategorySchema, **kw: Any) -> Category:
        event = self.service.get_one(pk=kw['event_id'])
        category = Category.objects.create(title=data.title)
        event.category = category
        event.save()
        return category

```

In the above example, we created an endpoint `POST /{int:event_id}/new-category` using `ModelEndpointFactory.create` 
and passed in input and output schemas along with a custom handler. 
By passing in a `custom_handler`, the generated route function will delegate its handling action to the provided 
`custom_handler` instead of calling `service.create`.

### **QueryGetter and ObjectGetter**
`ModelEndpointFactory` exposes a more flexible way to get a model object or get a queryset filter in the case of 
`ModelEndpointFactory.find_one` and `ModelEndpointFactory.list`, respectively.

For example, to retrieve the category of an event (not practical but for illustration):
```python
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    ModelEndpointFactory
)
from .models import Event, Category

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )

    get_event_category = ModelEndpointFactory.find_one(
        path="/{int:event_id}/category",
        schema_out=CategorySchema,
        lookup_param='event_id',
        object_getter=lambda self, pk, **kw: self.service.get_one(pk=pk).category
    )

```
In the above example, we created a `get_event_category` endpoint using `ModelEndpointFactory.find_one` and 
provided an `object_getter` as a callback for fetching the model based on the `event_id`.

On the other hand, you can have a case where you need to list events by `category_id`:
```python
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    ModelEndpointFactory
)
from .models import Event, Category

@api_controller("/events")
class EventModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Event,
        schema_config=ModelSchemaConfig(read_only_fields=["id", "category"]),
    )

    get_events_by_category = ModelEndpointFactory.list(
        path="/category/{int:category_id}/",
        schema_out=model_config.retrieve_schema,
        lookup_param='category_id',
        queryset_getter=lambda self, **kw: Category.objects.filter(pk=kw['category_id']).first().events.all()
    )

```
By using `ModelEndpointFactory.list` and `queryset_getter`, you can quickly set up a list endpoint that returns events belonging to a category. 
Note that our `queryset_getter` may fail if an invalid ID is supplied, as this is just an illustration.

Also, keep in mind that `model_config` settings like `create_schema`, `retrieve_schema`, `patch_schema`, and `update_schema` 
are all available after ModelConfig instantiation.

### **Path and Query Parameters**

In `ModelEndpointFactory`, path parameters are parsed to identify both `path` and `query` parameters. 
These parameters are then created as fields within the Ninja input schema and resolved during the request, 
passing them as kwargs to the handler.

For example,
```python
list_post_tags = ModelEndpointFactory.list(
    path="/{int:id}/tags/{post_id}?query=int&query1=int",
    schema_out=model_config.retrieve_schema,
    queryset_getter=lambda self, **kw: self.list_post_tags_query(**kw)
)

def list_post_tags_query(self, **kwargs):
    assert kwargs['id']
    assert kwargs['query']
    assert kwargs['query1']
    post_id = kwargs['post_id']
    return Post.objects.filter(id=post_id).first().tags.all()

```

In this example, the path `/{int:id}/tags/{post_id}?query=int&query1=int` generates two path parameters `['id:int', 'post_id:str']` 
and two query parameters `['query:int', 'query1:int']`. 
These parameters are bundled into the Ninja input schema and resolved during the request, passing them as kwargs to the route handler. 

Note that when `path` and `query` parameters are defined they are added to ninja schema input as a required field and, not optional. 
Also, path and query data types must be compatible with Django URL converters.

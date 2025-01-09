# Path and Query Parameters

Model Controllers in Ninja Extra provide flexible ways to handle path and query parameters in your API endpoints when using the `ModelEndpointFactory`. This guide covers how to work with these parameters effectively. 

> **Note:** This guide is only useful if you are using a Custom `ModelService` and you are not interested in adding additional logic to the route handler.

## **Basic Path Parameters**

Path parameters are part of the URL path and are typically used to identify specific resources:

```python
from ninja_extra import ModelEndpointFactory, ModelControllerBase

@api_controller("/events")
class EventModelController(ModelControllerBase):
    # Basic path parameter for event ID
    get_event = ModelEndpointFactory.find_one(
        path="/{int:id}",  # int converter for ID
        lookup_param="id",
        schema_out=EventSchema
    )
```

`lookup_param` is the name of the parameter in the model that will be used to lookup the object.

## **Path Parameter Types**

The following parameter types are supported:

```python
@api_controller("/events")
class EventModelController(ModelControllerBase):
    # Integer parameter
    get_by_id = ModelEndpointFactory.find_one(
        path="/{int:id}",
        lookup_param="id",
        schema_out=EventSchema
    )
    
    # String parameter
    get_by_slug = ModelEndpointFactory.find_one(
        path="/{str:slug}",
        lookup_param="slug",
        schema_out=EventSchema
    )
    
    # UUID parameter
    get_by_uuid = ModelEndpointFactory.find_one(
        path="/{uuid:uuid}",
        lookup_param="uuid",
        schema_out=EventSchema
    )
    
    # Date parameter
    get_by_date = ModelEndpointFactory.find_one(
        path="/{date:event_date}",
        lookup_param="event_date",
        schema_out=EventSchema
    )
```

## **Query Parameters**

Query parameters are added to the URL after the `?` character and are useful for filtering, sorting, and pagination:

```python
from typing import Optional
from ninja_extra import ModelEndpointFactory

@api_controller("/events")
class EventModelController(ModelControllerBase):
    # Endpoint with query parameters
    list_events = ModelEndpointFactory.list(
        path="/?category=int&status=str",  # Define query parameters
        schema_out=EventSchema,
        queryset_getter=lambda self, **kwargs: self.get_filtered_events(**kwargs)
    )
    
    def get_filtered_events(self, category: Optional[int] = None, 
                          status: Optional[str] = None, **kwargs):
        queryset = self.model.objects.all()
        
        if category:
            queryset = queryset.filter(category_id=category)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
```

## **Combining Path and Query Parameters**

You can combine both types of parameters in a single endpoint:

```python
class EventQueryParamsModelService(ModelService):
    def get_category_events(
        self, 
        category_id: int, 
        status: Optional[str] = None, 
        date: Optional[date] = None, 
        **kwargs
    ):
        queryset = self.model.objects.filter(category_id=category_id)
        if status:
            queryset = queryset.filter(status=status)
        if date:
            queryset = queryset.filter(start_date=date)
        return queryset

@api_controller("/events")
class EventModelController(ModelControllerBase):
    service = EventQueryParamsModelService(model=Event)
    # Path and query parameters together
    get_category_events = ModelEndpointFactory.list(
        path="/{int:category_id}/events?status=str&date=date",
        schema_out=EventSchema,
        queryset_getter=lambda self, **kwargs: self.service.get_category_events(**kwargs)
    )
```

## **Custom Parameter Handling**

You can implement custom parameter handling using object getters:

```python
class CustomParamsModelService(ModelService):
    def get_by_slug(self, slug: str) -> Event:
        return self.model.objects.get(slug=slug)


@api_controller("/events")
class EventModelController(ModelControllerBase):
    service = CustomParamsModelService(model=Event)
    get_event = ModelEndpointFactory.find_one(
        path="/{str:slug}",
        lookup_param="slug",
        schema_out=EventSchema,
        object_getter=lambda self, slug, **kwargs: self.service.get_by_slug(slug)
    )
```

## **Async Parameter Handling**

For async controllers, parameter handling works similarly:

```python

class AsyncCustomParamsModelService(ModelService):
    async def get_filtered_events(self, **kwargs):
        @sync_to_async
        def get_events():
            queryset = self.model.objects.all()
            
            if kwargs.get('category'):
                queryset = queryset.filter(category_id=kwargs['category'])
            if kwargs.get('status'):
                queryset = queryset.filter(status=kwargs['status'])
                
            return queryset
            
        return await get_events()

@api_controller("/events")
class AsyncEventModelController(ModelControllerBase):
    service_type = AsyncCustomParamsModelService
    model_config = ModelConfig(
        model=Event,
        async_routes=True
    )
    
    list_events = ModelEndpointFactory.list(
        path="/?category=int&status=str",
        schema_out=EventSchema,
        queryset_getter=lambda self, **kwargs: self.service.get_filtered_events(**kwargs)
    )
    
```

## **Parameter Validation**

You can add validation to your parameters using Pydantic models:

```python
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class EventQueryParams(BaseModel):
    category_id: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|draft)$")
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class EventQueryParamsModelService(ModelService):
    def get_filtered_events(self, params: EventQueryParams):
        queryset = self.model.objects.all()
        
        if params.category_id:
            queryset = queryset.filter(category_id=params.category_id)
        if params.status:
            queryset = queryset.filter(status=params.status)
        if params.date_from:
            queryset = queryset.filter(start_date__gte=params.date_from)
        if params.date_to:
            queryset = queryset.filter(end_date__lte=params.date_to)
            
        return queryset


@api_controller("/events")
class EventModelController(ModelControllerBase):
    service_type = EventQueryParamsModelService
    model_config = ModelConfig(
        model=Event,
        async_routes=True
    )

    list_events = ModelEndpointFactory.list(
        path="/",
        schema_in=EventQueryParams,
        schema_out=EventSchema,
        queryset_getter=lambda self, query: self.service.get_filtered_events(query)
    )
```

# Model Service

The Model Service layer in Ninja Extra handles all CRUD operations for your models. While the default implementation works well for simple cases, you can customize it for more complex scenarios.

## **Default Model Service**

The default `ModelService` implements both synchronous and asynchronous operations:

```python
from ninja_extra.controllers.model.interfaces import ModelServiceBase, AsyncModelServiceBase

class ModelService(ModelServiceBase, AsyncModelServiceBase):
    def __init__(self, model):
        super().__init__(model=model)
    ...
```

This provides the following methods:

### **Synchronous Methods:**
- `get_one(pk, **kwargs)` - Retrieve a single object
- `get_all(**kwargs)` - Retrieve all objects
- `create(schema, **kwargs)` - Create a new object
- `update(instance, schema, **kwargs)` - Update an object
- `patch(instance, schema, **kwargs)` - Partially update an object
- `delete(instance, **kwargs)` - Delete an object

### **Asynchronous Methods:**
- `get_one_async(pk, **kwargs)` - Async retrieve
- `get_all_async(**kwargs)` - Async retrieve all
- `create_async(schema, **kwargs)` - Async create
- `update_async(instance, schema, **kwargs)` - Async update
- `patch_async(instance, schema, **kwargs)` - Async patch
- `delete_async(instance, **kwargs)` - Async delete

## **Custom Model Service**

Here's how to create a custom service with additional business logic:

```python
from typing import Any, List, Union
from django.db.models import QuerySet
from ninja_extra import ModelService
from pydantic import BaseModel

class EventModelService(ModelService):
    def get_one(self, pk: Any, **kwargs: Any) -> Event:
        # Add custom logic for retrieving an event
        event = super().get_one(pk, **kwargs)
        if not event.is_published and not kwargs.get('is_admin'):
            raise PermissionError("Event not published")
        return event
    
    def get_all(self, **kwargs: Any) -> Union[QuerySet, List[Any]]:
        # Filter events based on criteria
        queryset = self.model.objects.all()
        if not kwargs.get('is_admin'):
            queryset = queryset.filter(is_published=True)
        return queryset
    
    def create(self, schema: BaseModel, **kwargs: Any) -> Any:
        # Add custom creation logic
        data = schema.model_dump(by_alias=True)
        data['created_by'] = kwargs.get('user_id')
        
        instance = self.model._default_manager.create(**data)
        return instance
    
    def update(self, instance: Event, schema: BaseModel, **kwargs: Any) -> Any:
        # Add validation before update
        if instance.is_locked:
            raise ValueError("Cannot update locked event")
        return super().update(instance, schema, **kwargs)
```

## **Async Model Service**

For async operations, you can customize the async methods:

```python
from ninja_extra import ModelService
from asgiref.sync import sync_to_async


class AsyncEventModelService(ModelService):
    async def get_all_async(self, **kwargs: Any) -> QuerySet:
        # Custom async implementation
        @sync_to_async
        def get_filtered_events():
            queryset = self.model.objects.all()
            if kwargs.get('category'):
                queryset = queryset.filter(category_id=kwargs['category'])
            return queryset
        
        return await get_filtered_events()
    
    async def create_async(self, schema: BaseModel, **kwargs: Any) -> Any:
        # Custom async creation
        @sync_to_async
        def create_event():
            data = schema.model_dump(by_alias=True)
            data['created_by'] = kwargs.get('user_id')
            return self.model._default_manager.create(**data)
            
        return await create_event()
```

## **Using Custom Services**

Attach your custom service to your Model Controller:

```python
@api_controller("/events")
class EventModelController(ModelControllerBase):
    service_type = EventModelService
    model_config = ModelConfig(model=Event)
```

For async controllers:

```python
@api_controller("/events")
class AsyncEventModelController(ModelControllerBase):
    service_type = AsyncEventModelService
    model_config = ModelConfig(
        model=Event,
        async_routes=True
    )
```

## **Advanced Service Patterns**

### **Service with Dependency Injection**

Model Services support dependency injection, allowing you to inject other services and dependencies when the controller is instantiated. Here's a practical example using email notifications and user tracking:

```python
from datetime import datetime
from typing import Any, Optional
from django.core.mail import send_mail
from ninja_extra import ModelService, api_controller, ModelConfig
from pydantic import BaseModel
from injector import inject


class EmailService:
    """Service for handling email notifications"""
    def send_event_notification(self, event_data: dict, recipient_email: str):
        subject = f"Event Update: {event_data['title']}"
        message = (
            f"Event Details:\n"
            f"Title: {event_data['title']}\n"
            f"Date: {event_data['start_date']} to {event_data['end_date']}\n"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email="events@example.com",
            recipient_list=[recipient_email],
            fail_silently=False,
        )


class UserActivityService:
    """Service for tracking user activities"""
    def track_activity(self, user_id: int, action: str, details: dict):
        UserActivity.objects.create(
            user_id=user_id,
            action=action,
            details=details,
            timestamp=datetime.now()
        )
```
Creating `EventModelService` with `EmailService` and `UserActivityService` as dependencies.
```python
class EventModelService(ModelService):
    """
    Event service with email notifications and activity tracking.
    Dependencies are automatically injected by the framework.
    """
    @inject
    def __init__(
        self, 
        model: Event,
        email_service: EmailService,
        activity_service: UserActivityService
    ):
        super().__init__(model=model)
        self.email_service = email_service
        self.activity_service = activity_service

    def create(self, schema: BaseModel, **kwargs: Any) -> Any:
        # Create the event
        event = super().create(schema, **kwargs)
        
        # Track the creation activity
        if user_id := kwargs.get('user_id'):
            self.activity_service.track_activity(
                user_id=user_id,
                action="event_created",
                details={
                    "event_id": event.id,
                    "title": event.title
                }
            )
        
        # Send notification to organizer
        if organizer_email := kwargs.get('organizer_email'):
            self.email_service.send_event_notification(
                event_data=schema.model_dump(),
                recipient_email=organizer_email
            )
        
        return event

    def update(self, instance: Event, schema: BaseModel, **kwargs: Any) -> Any:
        # Update the event
        updated_event = super().update(instance, schema, **kwargs)
        
        # Track the update activity
        if user_id := kwargs.get('user_id'):
            self.activity_service.track_activity(
                user_id=user_id,
                action="event_updated",
                details={
                    "event_id": updated_event.id,
                    "title": updated_event.title,
                    "changes": schema.model_dump()
                }
            )
        
        # Notify relevant parties about the update
        if notify_participants := kwargs.get('notify_participants'):
            for participant in updated_event.participants.all():
                self.email_service.send_event_notification(
                    event_data=schema.model_dump(),
                    recipient_email=participant.email
                )
        
        return updated_event

    def delete(self, instance: Event, **kwargs: Any) -> Any:
        event_data = {
            "id": instance.id,
            "title": instance.title
        }
        
        # Delete the event
        super().delete(instance, **kwargs)
        
        # Track the deletion
        if user_id := kwargs.get('user_id'):
            self.activity_service.track_activity(
                user_id=user_id,
                action="event_deleted",
                details=event_data
            )
        
        # Notify participants about cancellation
        if notify_participants := kwargs.get('notify_participants'):
            for participant in instance.participants.all():
                self.email_service.send_event_notification(
                    event_data={
                        **event_data,
                        "message": "Event has been cancelled"
                    },
                    recipient_email=participant.email
                )
```

Creating `EventModelController` with `EventModelService` as the service.
```python
from ninja_extra.controllers import ModelEndpointFactory, ModelControllerBase, ModelConfig
from ninja_extra import api_controller

@api_controller("/events")
class EventModelController(ModelControllerBase):
    service_type = EventModelService
    model_config = ModelConfig(model=Event, allowed_routes=['find_one', 'list'])
    
    create_new_event = ModelEndpointFactory.create(
        path="/?organizer_email=str",
        schema_in=model_config.create_schema,
        schema_out=model_config.retrieve_schema,
        custom_handler=lambda self, data, **kw: self.service.create(data, **kw)
    )
    
    update_event = ModelEndpointFactory.update(
        path="/{int:event_id}/?notify_participants=str",
        lookup_param="event_id",
        schema_in=model_config.update_schema,
        schema_out=model_config.retrieve_schema,
        object_getter=lambda self, pk, **kw: self.get_object_or_exception(self.model_config.model, pk=pk),
        custom_handler=lambda self, **kw: self.service.update(**kw),
    )

```
Register the services in the injector module
```python 
from injector import Module, singleton


class EventModule(Module):
    def configure(self, binder):
        binder.bind(EmailService, to=EmailService, scope=singleton)
        binder.bind(UserActivityService, to=UserActivityService, scope=singleton)

## settings.py
```python
NINJA_EXTRA = {
    'INJECTOR_MODULES': [
        'your_app.injector_module.EventModule'
    ]
}
```

The injected services provide several benefits:

- Automatic email notifications when events are created/updated/deleted
- User activity tracking for audit trails
- Clean separation of business logic
- Easy to extend with additional services
- Testable components with clear dependencies

For more information on dependency injection, please refer to the [Dependency Injection](service_module_injector.md) page.

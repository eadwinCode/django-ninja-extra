**Django Ninja Extra** provides the RouteContext object, which is available throughout the request lifecycle. 
This object holds essential properties for the route handler that will handle the request. 
These properties include the Django `HttpRequest` object, a list of permission classes for the route handler, 
a temporary response object used by Django-Ninja to construct the final response, 
and kwargs and args required for calling the route function. 

It's important to note that these properties are not set at the beginning of the request, 
but rather become available as the request progresses through different stages, 
and before it reaches the route function execution.


```python
from pydantic import BaseModel as PydanticModel, Field

class RouteContext(PydanticModel):
    """
    APIController Context which will be available to the class instance when handling request
    """

    class Config:
        arbitrary_types_allowed = True

    permission_classes: PermissionType = Field([])
    request: Union[Any, HttpRequest, None] = None
    response: Union[Any, HttpResponse, None] = None
    args: List[Any] = Field([])
    kwargs: DictStrAny = Field({})
```

## How to Access `RouteContext`

In Django Ninja Extra, the `RouteContext` object can be accessed within the **controller class** by using the `self.context` property. 
This property is available at the instance level of the controller class, making it easy to access the properties and methods of the `RouteContext` object.

For example.
```python
from ninja_extra import ControllerBase, api_controller, route
from django.db import transaction
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth import get_user_model

User = get_user_model()


@api_controller("/books", auth=JWTAuth(), permissions=[IsAuthenticated])
class StoryBookSubscribeController(ControllerBase):
    @route.get(
        "/context",
        url_name="subscribe",
    )
    @transaction.atomic
    def subscribe(self):
        user = self.context.request.user
        return {'message': 'Authenticated User From context', 'email': user.email}
    
    @route.post(
        "/context",
        url_name="subscribe",
    )
    @transaction.atomic
    def subscribe_with_response_change(self):
        res = self.context.response
        res.headers.setdefault('x-custom-header', 'welcome to custom header in response')
        return {'message': 'Authenticated User From context and Response header modified', 'email': self.context.request.user.email}

```

In the example, we can access the authenticated `user` object from the request object in the `self.context` property, which is available in the controller class. 
This allows us to easily access the authenticated user's information

### Modifying Response Header with RouteContext

The `RouteContext` object provides you with the necessary properties and methods to manipulate the response data before it is returned to the client.
With the RouteContext object, you can easily modify header, status, or cookie data for the response returned for a specific request

For example, lets add extra `header` info our new endpoint, `subscribe_with_response_change` as shown below.
```python
from ninja_extra import ControllerBase, api_controller, route
from django.db import transaction
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth import get_user_model

User = get_user_model()


@api_controller("/books", auth=JWTAuth(), permissions=[IsAuthenticated])
class StoryBookSubscribeController(ControllerBase):
    @route.post(
        "/context-response",
        url_name="response",
    )
    @transaction.atomic
    def subscribe_with_response_change(self):
        res = self.context.response
        res.headers['x-custom-header'] = 'welcome to custom header in response'
        return {'message': 'Authenticated User From context and Response header modified', 'email': self.context.request.user.email}

```

## Using `RouteContext` in Schema

There may be situations where you need to access the request object during schema validation. 
Django Ninja Extra makes this easy by providing a way to resolve the `RouteContext` object during the request, 
which can then be used to access the request object and any other necessary properties. 
This allows you to use the context of the request within the validation process, making it more flexible and powerful.

For example:

```python
from typing import Optional
from django.urls import reverse
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja import ModelSchema
from pydantic import AnyHttpUrl, validator


class StoreBookSchema(ModelSchema):
    borrowed_by: Optional[UserRetrieveSchema]
    store: AnyHttpUrl
    book: BookSchema

    class Config:
        model = StoreBook
        model_fields = ['borrowed_by', 'store', 'book']

    @validator("store", pre=True, check_fields=False)
    def store_validate(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        value = reverse("store:detail", kwargs=dict(store_id=value_data.id))
        return context.request.build_absolute_uri(value)
```

In the example above, we used the `service_resolver`, a dependency injection utility function, to resolve the `RouteContext` object. 
This gave us access to the request object, which we used to construct a full URL for our store details. 
By using the `service_resolver` to access the RouteContext, we can easily access the request object, 
and use it to gather any necessary information during the validation process.

# Route Context

The `RouteContext` object is a powerful feature in Django Ninja Extra that provides access to important request-related information throughout the request lifecycle. It acts as a central store for request data and is available within controller methods.

```python
from typing import Any, List, Union
from django.http import HttpRequest, HttpResponse
from ninja.types import DictStrAny
from pydantic import BaseModel, Field

class RouteContext(BaseModel):
    permission_classes: List[Any] = Field([])  # Permission classes for the route
    request: Union[HttpRequest, None] = None   # Django HttpRequest object
    response: Union[HttpResponse, None] = None # Response object being built
    args: List[Any] = Field([])               # Positional arguments
    kwargs: DictStrAny = Field({})            # Keyword arguments
```

## **Accessing RouteContext**

Within a controller class, you can access the `RouteContext` through `self.context`. Here's a complete example:

```python
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.authentication import JWTAuth

@api_controller("/api", auth=JWTAuth(), permissions=[IsAuthenticated])
class UserController(ControllerBase):
    
    @route.get("/me")
    def get_user_info(self):
        # Access the authenticated user from request
        user = self.context.request.user
        return {
            "email": user.email,
            "username": user.username
        }
    
    @route.post("/update-profile")
    def update_profile(self):
        # Access and modify the response headers
        self.context.response.headers["X-Profile-Updated"] = "true"
        return {"status": "profile updated"}

    @route.get("/context-demo")
    def demo_context(self):
        # Access various context properties
        return {
            "request_method": self.context.request.method,
            "route_kwargs": self.context.kwargs,
            "permissions": [p.__class__.__name__ for p in self.context.permission_classes]
        }
```

## **Working with Response Headers**

The `RouteContext` provides access to the response object, allowing you to modify headers, cookies, and other response properties:

```python
@api_controller("/api")
class HeaderController(ControllerBase):
    
    @route.get("/custom-headers")
    def add_custom_headers(self):
        # Add custom headers to the response
        response = self.context.response
        response.headers["X-Custom-Header"] = "custom value"
        response.headers["X-API-Version"] = "1.0"
        
        return {"message": "Response includes custom headers"}
```

## **Using RouteContext in Schema Validation**

You can access the `RouteContext` during schema validation using the `service_resolver`. This is useful when you need request information during validation:

```python
from ninja_extra import service_resolver
from ninja_extra.context import RouteContext
from ninja import ModelSchema
from pydantic import field_validator
from django.urls import reverse

class UserProfileSchema(ModelSchema):
    avatar_url: str
    
    class Config:
        model = UserProfile
        model_fields = ["avatar_url", "bio"]

    @field_validator("avatar_url", mode="before")
    def make_absolute_url(cls, value):
        # Get RouteContext to access request
        context: RouteContext = service_resolver(RouteContext)
        
        # Convert relative URL to absolute using request
        if value and not value.startswith(('http://', 'https://')):
            return context.request.build_absolute_uri(value)
        return value
```

## **Permissions and Authentication**

The `RouteContext` stores permission classes that apply to the current route. This is particularly useful when implementing custom permission logic:

```python
from ninja_extra import api_controller, route
from ninja_extra.permissions import BasePermission

class HasAPIKey(BasePermission):
    def has_permission(self, request, controller):
        return request.headers.get('X-API-Key') == 'valid-key'

@api_controller("/api", permissions=[HasAPIKey])
class SecureController(ControllerBase):
    
    @route.get("/secure")
    def secure_endpoint(self):
        # Access current permissions
        applied_permissions = self.context.permission_classes
        
        return {
            "message": "Access granted",
            "permissions": [p.__class__.__name__ for p in applied_permissions]
        }
```

## **Common Patterns**

### Accessing Request User
Using the `request` property, you can access the authenticated user from the request object.
```python
@route.get("/profile")
def get_profile(self):
    user = self.context.request.user
    return {"username": user.username}
```

### Adding Response Headers
With the `response` property, you can add custom headers to the response.

```python
@route.get("/download")
def download_file(self):
    self.context.response.headers["Content-Disposition"] = "attachment; filename=doc.pdf"
    return {"file_url": "path/to/file"}
```

### Using Route Arguments
The `kwargs` property contains the keyword arguments passed to the route function.

```python
@route.get("/items/{item_id}")
def get_item(self, item_id: int):
    # Access route parameters
    print(self.context.kwargs)  # {'item_id': 123}
    return {"item_id": item_id}
```

The `RouteContext` provides a clean way to access request data and modify responses within your controller methods. By understanding and properly utilizing `RouteContext`, you can write more maintainable and feature-rich APIs.

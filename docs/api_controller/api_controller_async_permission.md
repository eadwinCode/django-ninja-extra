# Async Permissions in Django Ninja Extra

This guide explains how to use the asynchronous permissions system in Django Ninja Extra for efficient permission handling with async views and models.

## Introduction

Django Ninja Extra provides an asynchronous permissions system that builds upon the existing permissions framework, adding support for async/await syntax. This is particularly useful when:

- Working with async views and controllers
- Performing permission checks that involve database queries
- Building efficient APIs that don't block the event loop

The permission system in Django Ninja Extra has been redesigned to seamlessly integrate both synchronous and asynchronous permissions, making it easy to:

- Create async-first permission classes
- Mix sync and async permissions with logical operators
- Use dependency injection with permissions
- Easily migrate from sync to async permissions

## Creating Async Permissions

### Basic Async Permission

To create a custom async permission, inherit from `AsyncBasePermission` and implement the `has_permission_async` method:

```python
from ninja_extra.permissions import AsyncBasePermission

class IsUserPremiumAsync(AsyncBasePermission):
    async def has_permission_async(self, request, controller):
        # You can perform async database operations here
        user = request.user
        
        # Async check (example using Django's async ORM methods)
        subscription = await user.subscription.aget()
        return subscription and subscription.is_premium
        
    # The sync version is automatically handled for you
    # through async_to_sync conversion
```

### Using Built-in Permissions

Django Ninja Extra's permission system automatically handles both sync and async operations for built-in permissions:

```python
from ninja_extra import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated, IsAdminUser

@api_controller(permissions=[IsAuthenticated])
class UserController:
    @http_get("/profile", permissions=[IsAdminUser])
    async def get_admin_profile(self, request):
        # Only accessible to admin users
        # IsAdminUser works with async views automatically
        return {"message": "Admin profile"}
```

## Combining Permissions with Logical Operators

The permission system supports combining permissions using logical operators (`&`, `|`, `~`):

```python
from ninja_extra import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated, IsAdminUser, AsyncBasePermission

# Custom async permission
class HasPremiumSubscriptionAsync(AsyncBasePermission):
    async def has_permission_async(self, request, controller):
        # Async check
        user_profile = await request.user.profile.aget()
        return user_profile.has_premium_subscription

@api_controller("/content")
class ContentController:
    # User must be authenticated AND have premium subscription
    @http_get("/premium", permissions=[IsAuthenticated() & HasPremiumSubscriptionAsync()])
    async def premium_content(self, request):
        return {"content": "Premium content"}
    
    # User must be authenticated OR an admin
    @http_get("/special", permissions=[IsAuthenticated() | IsAdminUser()])
    async def special_content(self, request):
        return {"content": "Special content"}
    
    # User must be authenticated but NOT an admin
    @http_get("/regular", permissions=[IsAuthenticated() & ~IsAdminUser()])
    async def regular_content(self, request):
        return {"content": "Regular user content"}
```

### How Permission Operators Work

When permissions are combined with logical operators, they create instances of `AND`, `OR`, or `NOT` classes that automatically handle both sync and async permissions:

- **AND**: Both permissions must return `True` (short-circuits on first `False`)
- **OR**: At least one permission must return `True` (short-circuits on first `True`)
- **NOT**: Inverts the result of the permission

The operators intelligently dispatch to either `has_permission`/`has_object_permission` or `has_permission_async`/`has_object_permission_async` depending on the context and permission types.

## Mixing Sync and Async Permissions

You can seamlessly mix regular permissions with async permissions:

```python
from ninja_extra import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated, IsAdminUser, AsyncBasePermission

# Custom async permission
class IsProjectMemberAsync(AsyncBasePermission):
    async def has_permission_async(self, request, controller):
        project_id = controller.kwargs.get('project_id')
        if not project_id:
            return False
        
        # Async database query
        return await is_member_of_project(request.user.id, project_id)

@api_controller("/projects")
class ProjectController:
    # Mixing sync and async permissions
    @http_get("/{project_id}/details", permissions=[IsAuthenticated() & IsProjectMemberAsync()])
    async def project_details(self, request, project_id: int):
        # The framework automatically handles the conversion between sync and async
        project = await get_project_by_id(project_id)
        return project
```

The permission system automatically handles conversions between sync and async:

- When an async view calls a sync permission, it's wrapped with `sync_to_async`
- When a sync view calls an async permission, it's wrapped with `async_to_sync`
- Logical operators (`AND`, `OR`, `NOT`) intelligently handle mixed permission types

## Object-Level Permissions

For object-level permissions, implement the `has_object_permission_async` method:

```python
class IsOwnerAsync(AsyncBasePermission):
    async def has_object_permission_async(self, request, controller, obj):
        # Async check on the object
        return obj.owner_id == request.user.id

@api_controller("/posts")
class PostController:
    @http_get("/{post_id}")
    async def get_post(self, request, post_id: int):
        # The async_check_object_permissions method will be called automatically
        # when using aget_object_or_exception or aget_object_or_none
        post = await self.aget_object_or_exception(Post, id=post_id)
        return {"title": post.title, "content": post.content}
```

## Using Dependency Injection with Permissions

Django Ninja Extra's permission system now integrates with dependency injection:

```python
from injector import inject
from ninja_extra import api_controller, http_get, service_resolver
from ninja_extra.permissions import AsyncBasePermission

class FeatureService:
    def has_feature_access(self, user, feature):
        # Check if user has access to a specific feature
        return getattr(user, f'has_{feature}', False)


class FeaturePermission(AsyncBasePermission):
    __features__ = {}

    feature: str = "basic"

    @inject
    def __init__(self, feature_service: FeatureService):
        self.feature_service = feature_service
        self.message = f"Must have access to {self.feature} feature"
        
    # Async version of permission check
    async def has_permission_async(self, request, controller):
        return self.feature_service.has_feature_access(request.user, self.feature)
    
    @classmethod
    def create_as(cls, feature: str) -> Type[FeaturePermission]:
        # Create a new permission class with the same attributes
        if feature in cls.__features__:
            return cls.__features__[feature]
        permission_type =  type(f"{cls.__name__}_{feature}", (cls,), {"feature": feature})
        cls.__features__[feature] = permission_type
        return permission_type


@api_controller('features')
class FeatureController(ControllerBase):
    @http_get('basic/', permissions=[FeaturePermission.create_as("basic")])
    async def basic_feature(self):
        return {"feature": "basic"}
        
    @http_get('premium/', permissions=[FeaturePermission.create_as("premium")])
    async def premium_feature(self):
        return {"feature": "premium"}
        
    # You can even combine injected permissions with operators
    @http_get('both/', permissions=[FeaturePermission.create_as("basic") & FeaturePermission.create_as("premium")])
    async def both_features(self):
        return {"feature": "both"}
```

The permission system automatically resolves the dependencies for injected permissions.

## How the Permission Resolution Works

The permission system uses a sophisticated resolution mechanism:

1. **Class vs Instance**: Permissions can be specified as either classes (`IsAuthenticated`) or instances (`IsAuthenticated()`).
2. **Dependency Injection**: Classes decorated with `@inject` are resolved using the dependency injector.
3. **Operator Handling**: When permissions are combined with operators, the resolution happens lazily, only when the permission is actually checked.

This resolution process is handled by the `_get_permission_object` method in the operation classes (`AND`, `OR`, `NOT`).

## Performance Considerations

- Use `AsyncBasePermission` for async-first permission classes
- For optimal performance with database queries, use async methods like `aget()`, `afilter()`, etc.
- The permission system automatically handles conversion between sync and async contexts using `asgiref.sync`
- Logical operators implement short-circuiting for efficiency

## Complete Example

```python
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from ninja_extra import api_controller, http_get, http_post, ControllerBase
from ninja_extra.permissions import AsyncBasePermission, IsAuthenticated, AllowAny

# Custom async permission
class IsStaffOrOwnerAsync(AsyncBasePermission):
    async def has_permission_async(self, request, controller):
        return request.user.is_authenticated
    
    async def has_object_permission_async(self, request, controller, obj):
        # Either the user is staff or owns the object
        return request.user.is_staff or obj.owner_id == request.user.id

# Controller using mixed permissions
@api_controller("/users", permissions=[IsAuthenticated])
class UserController(ControllerBase):
    @http_get("/", permissions=[AllowAny])
    async def list_users(self, request):
        # Public endpoint
        users = await sync_to_async(list)(User.objects.values('id', 'username')[:10])
        return users
    
    @http_get("/{user_id}")
    async def get_user(self, request, user_id: int):
        # Protected by IsAuthenticated from the controller
        user = await self.aget_object_or_exception(User, id=user_id)
        return {"id": user.id, "username": user.username}
    
    @http_post("/update/{user_id}", permissions=[IsStaffOrOwnerAsync()])
    async def update_user(self, request, user_id: int, data: dict):
        # Protected by custom async permission
        user = await self.aget_object_or_exception(User, id=user_id)
        # Update user data
        return {"status": "success"}
```

## Migrating from Sync Permissions

If you already have sync permission classes that you want to make async, follow these steps:

1. Change the base class from `BasePermission` to `AsyncBasePermission`
2. Implement the async methods (`has_permission_async` and `has_object_permission_async`)
3. Convert any blocking operations to their async equivalents
4. Update your controller to use these permissions

The framework will automatically handle the interoperability between sync and async permissions.

## Testing Async Permissions

Testing async permissions is straightforward using pytest-asyncio:

```python
import pytest
from unittest.mock import Mock
from django.contrib.auth.models import AnonymousUser
from ninja_extra.permissions import AsyncBasePermission, IsAdminUser

# Custom async permission for testing
class CustomAsyncPermission(AsyncBasePermission):
    async def has_permission_async(self, request, controller):
        return request.user.is_authenticated

@pytest.mark.asyncio
async def test_async_permission():
    # Create a mock request
    authenticated_request = Mock(user=Mock(is_authenticated=True))
    anonymous_request = Mock(user=AnonymousUser())
    
    # Test the permission
    permission = CustomAsyncPermission()
    assert await permission.has_permission_async(authenticated_request, None) is True
    assert await permission.has_permission_async(anonymous_request, None) is False
    
    # Test with operators
    combined = CustomAsyncPermission() & IsAdminUser()
    
    admin_request = Mock(user=Mock(is_authenticated=True, is_staff=True))
    assert await combined.has_permission_async(admin_request, None) is True
    assert await combined.has_permission_async(authenticated_request, None) is False

    assert combined.has_permission(admin_request, None) is True
    assert combined.has_permission(authenticated_request, None) is False
```

For controller integration tests:

```python
@pytest.mark.asyncio
async def test_controller_with_permissions():
    @api_controller("/test")
    class TestController(ControllerBase):
        @http_get("/protected", permissions=[CustomAsyncPermission()])
        async def protected_route(self):
            return {"success": True}
    
    # Create async test client
    client = TestAsyncClient(TestController)
    
    # Test with anonymous user
    response = await client.get("/protected", user=AnonymousUser())
    assert response.status_code == 403
    
    # Test with authenticated user
    auth_user = Mock(is_authenticated=True)
    response = await client.get("/protected", user=auth_user)
    assert response.status_code == 200
    assert response.json() == {"success": True}
``` 

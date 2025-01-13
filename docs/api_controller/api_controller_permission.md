# Django Ninja Extra Permissions Guide

Permissions in Django Ninja Extra provide a flexible way to control access to your API endpoints. The permission system is inspired by [Django REST Framework](https://www.django-rest-framework.org/api-guide/permissions/) and allows you to define both global and endpoint-specific access controls.

## **How Permissions Work**

Permissions are checked at the start of each route function execution. They use the authentication information available in `request.user` and `request.auth` to determine if the request should be allowed to proceed.

## **Built-in Permission Classes**

Django Ninja Extra comes with several built-in permission classes:

### **1. AllowAny**
Allows unrestricted access to any endpoint.

```python
from ninja_extra import permissions, api_controller, http_get

@api_controller(permissions=[permissions.AllowAny])
class PublicController:
    @http_get("/public")
    def public_endpoint(self):
        return {"message": "This endpoint is public"}
```

### **2. IsAuthenticated**
Only allows access to authenticated users.

```python
from ninja_extra import permissions, api_controller, http_get

@api_controller(permissions=[permissions.IsAuthenticated])
class PrivateController:
    @http_get("/profile")
    def get_profile(self, request):
        return {
            "username": request.user.username,
            "email": request.user.email
        }
```

### **3. IsAuthenticatedOrReadOnly**
Allows read-only access to unauthenticated users, but requires authentication for write operations.

```python
from ninja_extra import permissions, api_controller, http_get, http_post

@api_controller("/posts", permissions=[permissions.IsAuthenticatedOrReadOnly])
class BlogController:
    @http_get("/")  # Accessible to everyone
    def list_posts(self):
        return {"posts": ["Post 1", "Post 2"]}
    
    @http_post("/")  # Only accessible to authenticated users
    def create_post(self, request, title: str):
        return {"message": f"Post '{title}' created by {request.user.username}"}
```

### **4. IsAdminUser**
Only allows access to admin users (users with `is_staff=True`).

```python
from ninja_extra import permissions, api_controller, http_get

@api_controller("/admin", permissions=[permissions.IsAdminUser])
class AdminController:
    @http_get("/stats")
    def get_stats(self):
        return {"active_users": 100, "total_posts": 500}
```

## **Custom Permissions**

You can create custom permissions by subclassing `BasePermission`:

```python
from ninja_extra import permissions, api_controller, http_get
from django.http import HttpRequest

class HasAPIKey(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller):
        api_key = request.headers.get('X-API-Key')
        return api_key == 'your-secret-key'

@api_controller(permissions=[HasAPIKey])
class APIKeyProtectedController:
    @http_get("/protected")
    def protected_endpoint(self):
        return {"message": "Access granted with valid API key"}
```

### **Object-Level Permissions**

For fine-grained control over individual objects:

```python
from ninja_extra import permissions, api_controller, http_get
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from .models import Post

class IsPostAuthor(permissions.BasePermission):
    def has_object_permission(self, request: HttpRequest, controller, obj: Post):
        return obj.author == request.user

@api_controller("/posts")
class PostController:
    @http_get("/{post_id}", permissions=[permissions.IsAuthenticated & IsPostAuthor()])
    def get_post(self, request, post_id: int):
        # The has_object_permission method will be called automatically
        # when using get_object_or_exception or get_object_or_none
        post = self.get_object_or_exception(Post, id=post_id)
        return {"title": post.title, "content": post.content}
```

## **Combining Permissions**

Django Ninja Extra supports combining permissions using logical operators:

- `&` (AND): Both permissions must pass
- `|` (OR): At least one permission must pass
- `~` (NOT): Inverts the permission

```python
from ninja_extra import permissions, api_controller, http_get

class HasPremiumSubscription(permissions.BasePermission):
    def has_permission(self, request, controller):
        return request.user.has_perm('premium_subscription')

@api_controller("/content")
class ContentController:
    @http_get("/basic", permissions=[permissions.IsAuthenticated | HasPremiumSubscription()])
    def basic_content(self):
        return {"content": "Basic content"}
    
    @http_get("/premium", permissions=[permissions.IsAuthenticated & HasPremiumSubscription()])
    def premium_content(self):
        return {"content": "Premium content"}
    
    @http_get("/non-premium", permissions=[permissions.IsAuthenticated & ~HasPremiumSubscription()])
    def non_premium_content(self):
        return {"content": "Content for non-premium users"}
```

## **Role-Based Permissions**

You can dynamically check different roles or permissions for a user using a single permission class. Here's an example:

```python
from ninja_extra import permissions, api_controller, http_get, http_post, http_delete

class HasRole(permissions.BasePermission):
    def __init__(self, required_role: str):
        self.required_role = required_role
    
    def has_permission(self, request, controller):
        return request.user.has_perm(self.required_role)


@api_controller("/articles", permissions=[permissions.IsAuthenticated])
class ArticleController:
    @http_get("/", permissions=[HasRole("articles.view")])
    def list_articles(self):
        return {"articles": ["Article 1", "Article 2"]}
    
    @http_post("/", permissions=[HasRole("articles.add")])
    def create_article(self, title: str):
        return {"message": f"Article '{title}' created"}
    
    @http_delete("/{id}", permissions=[HasRole("articles.delete")])
    def delete_article(self, id: int):
        return {"message": f"Article {id} deleted"}
```
In the above example, the `HasRole` permission class is used to check if the user has the `articles.view`, `articles.add` or `articles.delete` permission in different routes.

## **Interacting with Route Function Parameters and RouteContext**

Sometimes you need to access route function parameters within your permission class before the actual route function is executed. Django Ninja Extra provides the `RouteContext` class to handle this scenario.

By default, permission checks are performed before route function parameters are resolved. However, you can explicitly trigger parameter resolution using the `RouteContext` class.

### **Basic Route Context Usage**

```python
from ninja_extra import permissions, api_controller, http_get, ControllerBase
from django.http import HttpRequest

class IsOwner(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase):
        # Access route context and compute parameters
        controller.context.compute_route_parameters()
        
        # Now you can access path and query parameters
        user_id = controller.context.kwargs.get('user_id')
        return request.user.id == user_id

@api_controller("/users")
class UserController:
    @http_get("/{user_id}/profile", permissions=[IsOwner()])
    def get_user_profile(self, user_id: int):
        return {"message": f"Access granted to profile {user_id}"}
```

### **Advanced Route Context Examples**

Here are more complex examples showing different ways to use route context:

```python
from ninja_extra import permissions, api_controller, http_get, http_post, ControllerBase
from django.http import HttpRequest
from typing import Optional

class HasTeamAccess(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase):
        # Compute parameters to access both path and query parameters
        controller.context.compute_route_parameters()
        
        team_id = controller.context.kwargs.get('team_id')
        role = controller.context.kwargs.get('role', 'member')  # Default to 'member'
        
        return request.user.has_team_permission(team_id, role)

class HasProjectAccess(permissions.BasePermission):
    def __init__(self, required_role: str):
        self.required_role = required_role

    def has_permission(self, request: HttpRequest, controller: ControllerBase):
        controller.context.compute_route_parameters()
        
        # Access multiple parameters
        project_id = controller.context.kwargs.get('project_id')
        team_id = controller.context.kwargs.get('team_id')
        
        return (
            request.user.is_authenticated and
            request.user.has_project_permission(project_id, team_id, self.required_role)
        )

@api_controller("/teams")
class TeamProjectController:
    @http_get("/{team_id}/projects/{project_id}", permissions=[HasTeamAccess() & HasProjectAccess("viewer")])
    def get_project(self, team_id: int, project_id: int):
        return {"message": f"Access granted to project {project_id} in team {team_id}"}
    
    @http_post("/{team_id}/projects", permissions=[HasTeamAccess() & HasProjectAccess("admin")])
    def create_project(self, team_id: int, name: str, description: Optional[str] = None):
        return {
            "message": f"Created project '{name}' in team {team_id}",
            "description": description
        }
```

### **Working with Query Parameters**

You can also access query parameters in your permission classes:

```python
from ninja_extra import permissions, api_controller, http_get, ControllerBase
from django.http import HttpRequest

class HasFeatureAccess(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase):
        controller.context.compute_route_parameters()
        
        # Access query parameters
        feature_name = controller.context.kwargs.get('feature')
        environment = controller.context.kwargs.get('env', 'production')
        
        return request.user.has_feature_access(feature_name, environment)

@api_controller("/features")
class FeatureController:
    @http_get("/check", permissions=[HasFeatureAccess()])
    def check_feature(self, feature: str, env: str = "production"):
        return {
            "feature": feature,
            "environment": env,
            "status": "enabled"
        }
```

### **Important Notes**

1. Always call `compute_route_parameters()` before accessing route parameters in permission classes
2. Route parameters are available in `controller.context.kwargs` after computation
3. Both path parameters and query parameters are accessible
4. You can combine route context-based permissions with other permission types
5. Route parameters are computed only once, even if accessed by multiple permission classes
6. The computation results are cached for the duration of the request

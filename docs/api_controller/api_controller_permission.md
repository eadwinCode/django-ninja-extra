# **APIController Permissions**

The concept of this permission system came from Django [DRF](https://www.django-rest-framework.org/api-guide/permissions/).

Permission checks are always run at the very start of the route function, before any other code is allowed to proceed. 
Permission checks will typically use the authentication information in the `request.user` and `request.auth` properties to determine if the incoming request should be permitted.

Permissions are used to grant or deny access for different classes of users to different parts of the API.

The simplest style of permission would be to allow access to any authenticated user, and deny access to any unauthenticated user. 
This corresponds to the `IsAuthenticated` class in **Django Ninja Extra**.

A slightly less strict style of permission would be to allow full access to authenticated users, but allow read-only access to unauthenticated users. 
This corresponds to the `IsAuthenticatedOrReadOnly` class in **Django Ninja Extra**.

### **Limitations of object level permissions**
During route function call, we can only `has_permission` in permissions list are called automatic. 
But since we don't have the object, we can only invoke `has_object_permission` if you use `get_object_or_exception` or `get_object_or_none` methods which are available to APIController.

## **Custom permissions**

To implement a custom permission, override `BasePermission` and implement either, or both, of the following methods:

    .has_permission(self, request: HttpRequest, controller: "APIController")
    .has_object_permission(self, request: HttpRequest, controller: "APIController", obj: Any)
Example

```python
from ninja_extra import permissions, api_controller, http_get

class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

@api_controller(permissions=[permissions.IsAuthenticated | ReadOnly])
class PermissionController:
    @http_get('/must_be_authenticated', permissions=[permissions.IsAuthenticated])
    def must_be_authenticated(self, word: str):
        return dict(says=word)
```
!!! Note
    New in **v0.18.7**
    Controller Permission and Route Function `permissions` can now take `BasePermission` instance.
    
    For example, we can pass the `ReadOnly` instance to the `permission` parameter.
    ```python
    from ninja_extra import permissions, api_controller, http_get
    
    class ReadOnly(permissions.BasePermission):
        def has_permission(self, request, view):
            return request.method in permissions.SAFE_METHODS
    
    @api_controller(permissions=[permissions.IsAuthenticated | ReadOnly()])
    ...
    ```
    For example:
    ```python
    from ninja_extra import permissions
    
    class UserWithPermission(permissions.BasePermission):
        def __init__(self, permission: str) -> None:
            self._permission = permission
        
        def has_permission(self, request, view):
            return request.user.has_perm(self._permission)
        
    # in controller or route function
    permissions=[UserWithPermission('blog.add')]
    ```

## **Permissions Supported Operands**
- & (and) eg: `permissions.IsAuthenticated & ReadOnly`
- | (or) eg: `permissions.IsAuthenticated | ReadOnly`
- ~ (not) eg: `~(permissions.IsAuthenticated & ReadOnly)`

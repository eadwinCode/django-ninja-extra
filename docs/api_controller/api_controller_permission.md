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
During the handling of a request, the `has_permission` method is automatically invoked for all the permissions specified 
in the permission list of the route function. However, `has_object_permission` is not triggered since 
it requires an object for permission validation. As a result of that, `has_object_permission` method for permissions are
invoked when attempting to retrieve an object using the `get_object_or_exception` 
or `get_object_or_none` methods within the controller.

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


## **Permissions Supported Operands**
- & (and) eg: `permissions.IsAuthenticated & ReadOnly`
- | (or) eg: `permissions.IsAuthenticated | ReadOnly`
- ~ (not) eg: `~(permissions.IsAuthenticated & ReadOnly)`


## **Using Permission Object in Controllers**

The Ninja-Extra permission system provides flexibility in defining permissions either as an instance of a permission class or as a type.

In the example below, the `ReadOnly` class is defined as a subclass of `permissions.BasePermission` and 
its instance is then passed to the `permissions` parameter within the `api_controller` decorator.

```python
from ninja_extra import permissions, api_controller, ControllerBase

class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

@api_controller(permissions=[permissions.IsAuthenticated | ReadOnly()])
class SampleController(ControllerBase):
    pass
```

In the provided example, the `UserWithPermission` class is utilized to assess different permissions for distinct controllers or route functions.

For instance:
```python
from ninja_extra import permissions, api_controller, ControllerBase, http_post, http_delete

class UserWithPermission(permissions.BasePermission):
    def __init__(self, permission: str) -> None:
        self._permission = permission
    
    def has_permission(self, request, view):
        return request.user.has_perm(self._permission)
    

@api_controller('/blog')
class BlogController(ControllerBase):
    @http_post('/', permissions=[permissions.IsAuthenticated & UserWithPermission('blog.add')])
    def add_blog(self):
        pass
    
    @http_delete('/', permissions=[permissions.IsAuthenticated & UserWithPermission('blog.delete')])
    def delete_blog(self):
        pass
```

In this scenario, the `UserWithPermission` class is employed to verify whether the user possesses the `blog.add` 
permission to access the `add_blog` action and `blog.delete` permission for the `delete_blog` action within the `BlogController`. 
The permissions are explicitly configured for each route function, allowing fine-grained control over user access based on specific permissions.

## **AllowAny**
The `AllowAny` permission class grants unrestricted access, irrespective of whether the request is authenticated or unauthenticated. While not mandatory, using this permission class is optional, as you can achieve the same outcome by employing an empty list or tuple for the permissions setting. 
However, specifying the `AllowAny` class can be beneficial as it explicitly communicates the intention of allowing unrestricted access.

## **IsAuthenticated**
The `IsAuthenticated` permission class denies permission to unauthenticated users and grants permission to authenticated users. 

This permission is appropriate if you intend to restrict API access solely to registered users.

## **IsAdminUser**
The `IsAdminUser` permission class denies permission to any user, except when `user.is_staff` is `True`, 
in which case permission is granted. 

This permission is suitable if you intend to restrict API access to a 
specific subset of trusted administrators.

## **IsAuthenticatedOrReadOnly**
The `IsAuthenticatedOrReadOnly` permission class allows authenticated users to perform any request. 
For unauthenticated users, requests will only be permitted if the method is one of the "safe" methods: GET, HEAD, or OPTIONS. 

This permission is appropriate if you want your API to grant read permissions to anonymous users while restricting write permissions to authenticated users.

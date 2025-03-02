# Dependency Injection in Controllers

Django Ninja Extra provides powerful dependency injection capabilities using [Injector](https://injector.readthedocs.io/en/latest/). This guide will show you how to effectively use dependency injection in your controllers.

## **Basic Example**

Let's start with a simple example of dependency injection in a controller:

```python
from ninja_extra import api_controller, http_get
from injector import inject

class UserService:
    def get_user_count(self) -> int:
        return 42  # Example implementation

@api_controller("/users")
class UserController:
    @inject
    def __init__(self, user_service: UserService):  # Type annotation is required
        self.user_service = user_service
    
    @http_get("/count")
    def get_count(self):
        return {"count": self.user_service.get_user_count()}
```

## **Real-World Example: Todo Application**

Let's create a more practical example with a Todo application that demonstrates dependency injection with multiple services.

### 1. Define the Services

```python
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from injector import inject

# Data Models
class TodoItem(BaseModel):
    id: int
    title: str
    completed: bool = False
    created_at: datetime

# Repository Service
class TodoRepository:
    def __init__(self):
        self._todos: List[TodoItem] = []
        self._counter = 0
    
    def add(self, title: str) -> TodoItem:
        self._counter += 1
        todo = TodoItem(
            id=self._counter,
            title=title,
            created_at=datetime.now()
        )
        self._todos.append(todo)
        return todo
    
    def get_all(self) -> List[TodoItem]:
        return self._todos
    
    def get_by_id(self, todo_id: int) -> Optional[TodoItem]:
        return next((todo for todo in self._todos if todo.id == todo_id), None)
    
    def toggle_complete(self, todo_id: int) -> Optional[TodoItem]:
        todo = self.get_by_id(todo_id)
        if todo:
            todo.completed = not todo.completed
        return todo

# Business Logic Service
class TodoService:
    @inject
    def __init__(self, repository: TodoRepository):
        self.repository = repository
    
    def create_todo(self, title: str) -> TodoItem:
        return self.repository.add(title)
    
    def get_todos(self) -> List[TodoItem]:
        return self.repository.get_all()
    
    def toggle_todo(self, todo_id: int) -> Optional[TodoItem]:
        return self.repository.toggle_complete(todo_id)
```

### 2. Create the Controller

```python
from ninja_extra import api_controller, http_get, http_post, http_put
from ninja import Body

# Request Models
class CreateTodoRequest(BaseModel):
    title: str

@api_controller("/todos")
class TodoController:
    def __init__(self, todo_service: TodoService):
        self.todo_service = todo_service
    
    @http_post("")
    def create_todo(self, request: CreateTodoRequest = Body(...)):
        todo = self.todo_service.create_todo(request.title)
        return todo
    
    @http_get("")
    def list_todos(self):
        return self.todo_service.get_todos()
    
    @http_put("/{todo_id}/toggle")
    def toggle_todo(self, todo_id: int):
        todo = self.todo_service.toggle_todo(todo_id)
        if not todo:
            return {"error": "Todo not found"}, 404
        return todo
```
!!! warning
    You are not allowed to override your APIController constructor with parameters that don't have type annotations.
    The following example demonstrates the correct way to use type annotations in your constructor.
    Read more [**Python Injector** ](https://injector.readthedocs.io/en/latest/)

### 3. Register the Services

Create a module to register your services. When registering services, you can specify their scope:

- `singleton`: The service is created once and reused (default). Best for stateless services or services that maintain application-wide state.
- `noscope` (transient): A new instance is created each time the service is requested. Best for services that maintain request-specific state.

```python
from injector import Module, singleton, noscope, Binder

class TodoModule(Module):
    def configure(self, binder: Binder) -> None:
        # Singleton scope - same instance for entire application
        # TodoRepository maintains application state (the todos list)
        binder.bind(TodoRepository, to=TodoRepository, scope=singleton)
        
        # Singleton scope - stateless service that only contains business logic
        binder.bind(TodoService, to=TodoService, scope=singleton)

        # Example of when to use noscope
        # binder.bind(RequestContextService, to=RequestContextService, scope=noscope)
```

!!! info
    If no scope is specified, services default to `singleton` scope. Choose the appropriate scope based on your service's requirements:

    - Use `singleton` for:
        - Stateless services (like services that only contain business logic)
        - Services that maintain application-wide state
        - Services that are expensive to create
    - Use `noscope` for:
        - Services that maintain request-specific state
        - Services that need to be recreated for each request
        - Services with request-scoped dependencies

### 4. Configure Settings
Add the module to your Django settings:

```python
NINJA_EXTRA = {
    'INJECTOR_MODULES': [
        'your_app.modules.TodoModule'
    ]
}
```
!!! info
    Django-Ninja-Extra supports [**django_injector**](https://github.com/blubber/django_injector). If you're using django_injector, no additional configuration is needed in settings.py.

### 5. Register the API

```python
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI()
api.register_controllers(TodoController)
```

## **Advanced Usage: Multiple Dependencies**

You can inject multiple services into a controller:

```python
from ninja_extra import api_controller, http_get
from injector import inject

class AuthService:
    def is_admin(self) -> bool:
        return True  # Example implementation

class LoggingService:
    def log_access(self, endpoint: str):
        print(f"Accessed: {endpoint}")  # Example implementation

@api_controller("/admin")
class AdminController:
    def __init__(
        self, 
        auth_service: AuthService,
        logging_service: LoggingService,
        todo_service: TodoService
    ):
        self.auth_service = auth_service
        self.logging_service = logging_service
        self.todo_service = todo_service
    
    @http_get("/todos")
    def get_todos(self):
        if not self.auth_service.is_admin():
            return {"error": "Unauthorized"}, 403
        
        self.logging_service.log_access("admin/todos")
        return self.todo_service.get_todos()
```

## **Using Service Resolver**

Sometimes you might need to resolve services outside of controllers. Django Ninja Extra provides a `service_resolver` utility for this:

```python
from ninja_extra import service_resolver

# Resolve a single service
todo_service = service_resolver(TodoService)
todos = todo_service.get_todos()

# Resolve multiple services
todo_service, auth_service = service_resolver(TodoService, AuthService)
```

## **Best Practices**

1. **Single Responsibility**: Keep your services focused on a single responsibility.
2. **Interface Segregation**: Create specific interfaces for your services rather than large, monolithic ones.
3. **Dependency Inversion**: Depend on abstractions rather than concrete implementations.
4. **Scoping**: Use appropriate scopes for your services:
    - Use `singleton` for services that maintain application-wide state
    - Use `noscope` (transient) for services that should be created per request


## **Testing with Dependency Injection**

Testing applications that use dependency injection requires special consideration for mocking services and managing test environments. We have a dedicated guide that covers all aspects of testing, including:

- Setting up separate development and testing environments
- Implementing mock services
- Using different testing frameworks (pytest, NinjaExtra TestClient)
- Best practices for test configuration
- Managing service dependencies in tests

For the complete guide on testing with dependency injection, see [Testing with Dependency Injection](testing_with_dependency_injection.md).

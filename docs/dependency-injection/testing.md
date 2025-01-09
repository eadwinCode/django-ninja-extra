# Testing with Dependency Injection

This guide explains best practices for testing applications that use dependency injection in Django Ninja Extra.

## **Settings Configuration for Testing**

A recommended approach is to maintain separate Django settings files for development and testing. This allows you to swap out real services with mock implementations during testing.

### Project Structure
```
your_project/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── testing.py
├── your_app/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── todo_service.py
│   │   └── mock_todo_service.py
│   └── modules.py
```

### Development Settings (development.py)
```python
from .base import *

NINJA_EXTRA = {
    'INJECTOR_MODULES': [
        'your_app.modules.TodoModule'  # Uses real implementation
    ]
}
```

### Testing Settings (testing.py)
```python
from .base import *

NINJA_EXTRA = {
    'INJECTOR_MODULES': [
        'your_app.modules.MockTodoModule'  # Uses mock implementation
    ]
}
```

## **Implementing Mock Services**

Create your mock services and module:

```python
# your_app/services/mock_todo_service.py
from typing import List, Optional
from datetime import datetime
from .todo_service import TodoItem, TodoService

class MockTodoRepository:
    def __init__(self):
        self._todos = [
            TodoItem(id=1, title="Test Todo", completed=False, created_at=datetime.now())
        ]
    
    def get_all(self) -> List[TodoItem]:
        return self._todos
    
    def get_by_id(self, todo_id: int) -> Optional[TodoItem]:
        return self._todos[0] if todo_id == 1 else None
    
    def add(self, title: str) -> TodoItem:
        return self._todos[0]
    
    def toggle_complete(self, todo_id: int) -> Optional[TodoItem]:
        todo = self.get_by_id(todo_id)
        if todo:
            todo.completed = not todo.completed
        return todo

# your_app/modules.py
from injector import Module, singleton, Binder
from .services.mock_todo_service import MockTodoRepository
from .services.todo_service import TodoService, TodoRepository

class MockTodoModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(TodoRepository, to=MockTodoRepository, scope=singleton)
        binder.bind(TodoService, to=TodoService, scope=singleton)
```

## **Running Tests**

After setting up your mock services and configuring your test environment, you can write tests using for the controller using the `TestClient` from `ninja_extra.testing`. As shown in the example below:

```python
# tests/test_todo_api.py
import pytest
from ninja_extra import testing
from your_app.controllers import TodoController

@pytest.mark.django_db
class TestTodoController:
    def test_list_todos(self):
        client = testing.TestClient(TodoController)
        response = client.get("/api/todos")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["title"] == "Test Todo"

    def test_create_todo(self):
        client = testing.TestClient(TodoController)
        response = client.post("/api/todos", {"title": "New Todo"})

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Test Todo"  # Returns mock data
```

## **Best Practices**

1. **Separate Settings Files**: Maintain separate settings files for different environments (development, testing, production).
2. **Mock Module Design**: 
    - Keep mock implementations simple but sufficient for testing
    - Implement only the methods that are actually used in tests
    - Use predictable, static data in mock responses
3. **Test Data**: 
    - Initialize mock services with known test data
    - Avoid dependencies on external services in tests
4. **Configuration Management**:
    - Use environment variables to switch between settings files
    - Document the required environment setup for running tests

## **Environment Setup**

To use different settings files, set the Django settings module environment variable:

```bash
# For development
export DJANGO_SETTINGS_MODULE=config.settings.development

# For testing
export DJANGO_SETTINGS_MODULE=config.settings.testing
```

Or in pytest.ini:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
```

This approach ensures consistent and isolated testing environments while maintaining the ability to use real implementations in development. 

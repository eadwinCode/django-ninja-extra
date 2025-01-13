![Test](https://github.com/eadwinCode/django-ninja-extra/workflows/Test/badge.svg)
[![PyPI version](https://badge.fury.io/py/django-ninja-extra.svg)](https://badge.fury.io/py/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/v/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/pyversions/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/djversions/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![Codecov](https://img.shields.io/codecov/c/gh/eadwinCode/django-ninja-extra)](https://codecov.io/gh/eadwinCode/django-ninja-extra)
[![Downloads](https://static.pepy.tech/badge/django-ninja-extra)](https://pepy.tech/project/django-ninja-extra)

# Django Ninja Extra

Django Ninja Extra is a powerful extension for [Django Ninja](https://django-ninja.rest-framework.com) that enhances your Django REST API development experience. It introduces class-based views and advanced features while maintaining the high performance and simplicity of Django Ninja. Whether you're building a small API or a large-scale application, Django Ninja Extra provides the tools you need for clean, maintainable, and efficient API development.

## Features

### Core Features (Inherited from Django Ninja)
- ⚡ **High Performance**: Built on Pydantic for lightning-fast validation
- 🔄 **Async Support**: First-class support for async/await operations
- 📝 **Type Safety**: Comprehensive type hints for better development experience
- 🎯 **Django Integration**: Seamless integration with Django's ecosystem
- 📚 **OpenAPI Support**: Automatic API documentation with Swagger/ReDoc
- 🔒 **API Throttling**: Rate limiting for your API

### Extra Features
- 🏗️ **Class-Based Controllers**: 
  - Organize related endpoints in controller classes
  - Inherit common functionality
  - Share dependencies across endpoints

- 🔒 **Advanced Permission System (Similar to Django Rest Framework)**:
  - Controller-level permissions
  - Route-level permission overrides
  - Custom permission classes

- 💉 **Dependency Injection**:
  - Built-in support for [Injector](https://injector.readthedocs.io/en/latest/)
  - Compatible with [django_injector](https://github.com/blubber/django_injector)
  - Automatic dependency resolution

- 🔧 **Service Layer**:
  - Injectable services for business logic
  - Better separation of concerns
  - Reusable components

## Requirements

- Python >= 3.6
- Django >= 2.1
- Pydantic >= 1.6
- Django-Ninja >= 0.16.1

## Installation

1. Install the package:
```bash
pip install django-ninja-extra
```

2. Add to INSTALLED_APPS:
```python
INSTALLED_APPS = [
    ...,
    'ninja_extra',
]
```

## Quick Start Guide

### 1. Basic API Setup

Create `api.py` in your Django project:

```python
from ninja_extra import NinjaExtraAPI, api_controller, http_get

api = NinjaExtraAPI()

# Function-based endpoint example
@api.get("/hello", tags=['Basic'])
def hello(request, name: str = "World"):
    return {"message": f"Hello, {name}!"}

# Class-based controller example
@api_controller('/math', tags=['Math'])
class MathController:
    @http_get('/add')
    def add(self, a: int, b: int):
        """Add two numbers"""
        return {"result": a + b}

    @http_get('/multiply')
    def multiply(self, a: int, b: int):
        """Multiply two numbers"""
        return {"result": a * b}

# Register your controllers
api.register_controllers(MathController)
```

### 2. URL Configuration

In `urls.py`:
```python
from django.urls import path
from .api import api

urlpatterns = [
    path("api/", api.urls),  # This will mount your API at /api/
]
```

## Advanced Features

### Authentication and Permissions

```python
from ninja_extra import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated, PermissionBase

# Custom permission
class IsAdmin(PermissionBase):
    def has_permission(self, context):
        return context.request.user.is_staff

@api_controller('/admin', tags=['Admin'], permissions=[IsAuthenticated, IsAdmin])
class AdminController:
    @http_get('/stats')
    def get_stats(self):
        return {"status": "admin only data"}
    
    @http_get('/public', permissions=[])  # Override to make public
    def public_stats(self):
        return {"status": "public data"}
```

### Dependency Injection with Services

```python
from injector import inject
from ninja_extra import api_controller, http_get


# Service class
class UserService:
    def get_user_details(self, user_id: int):
        return {"user_id": user_id, "status": "active"}


# Controller with dependency injection
@api_controller('/users', tags=['Users'])
class UserController:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    @http_get('/{user_id}')
    def get_user(self, user_id: int):
        return self.user_service.get_user_details(user_id)
```

## API Documentation

Access your API's interactive documentation at `/api/docs`:

![Swagger UI](docs/images/ui_swagger_preview_readme.gif)

## Learning Resources

### Tutorials
- 📺 [Video: Permissions & Controllers](https://www.youtube.com/watch?v=yQqig-c2dd4)
- 💻 [Example: BookStore API](https://github.com/eadwinCode/bookstoreapi)
- 📚 [Official Documentation](https://eadwincode.github.io/django-ninja-extra/)

### Community and Support
- 🌟 [GitHub Repository](https://github.com/eadwinCode/django-ninja-extra)
- 🐛 [Issue Tracker](https://github.com/eadwinCode/django-ninja-extra/issues)
- 💬 [Discussions](https://github.com/eadwinCode/django-ninja-extra/discussions)

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch
3. Write your changes
4. Submit a pull request

Please ensure your code follows our coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support the Project

- ⭐ Star the repository
- 🐛 Report issues
- 📖 Contribute to documentation
- 🤝 Submit pull requests

## DEPRECATION NOTICE
### 0.22.2
The `service` attribute in `ModelController` has been changed from a class object to an **instance** object. When creating a custom `ModelService` for a `ModelController`, you have to specify it as `service_type`. 

This is because services are now injected as dependencies during controller instantiation. Service instantiation is delegated to the injector package, so ensure that any additional dependencies required by your `ModelService` are properly registered in the dependency injection container. 

For more details, please refer to the [documentation](https://eadwincode.github.io/django-ninja-extra/api_controller/model_controller/03_model_service/#advanced-service-patterns)

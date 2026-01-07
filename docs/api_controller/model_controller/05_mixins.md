# Programmatic Controller Mixins

## Core Components

-   **`MixinModelControllerBase`**: The required base class for controllers using this system. It manages route creation and model configuration.
-   **Endpoint Mixins**: Declarative classes that add specific endpoints (e.g., list, create) to the controller.

## Quickstart: Full CRUD API

To create all CRUD endpoints for a Django model, inherit from `MixinModelControllerBase` and `CRUDModelMixin`.

**Model:**
```python
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
```

**Controller:**
```python
from ninja_extra import api_controller
from ninja_extra.mixins import MixinModelControllerBase, CRUDModelMixin
from .models import Project

@api_controller("/projects")
class ProjectController(MixinModelControllerBase, CRUDModelMixin):
    model_class = Project
```
This automatically creates the following endpoints:
-   `POST /projects/`
-   `GET /projects/`
-   `GET /projects/{id}/`
-   `PUT /projects/{id}/`
-   `PATCH /projects/{id}/`
-   `DELETE /projects/{id}/`

## Available Mixins

### CRUD Mixins

| Mixin                | HTTP Method | Path     | Description                        |
|:---------------------|:------------|:---------|:-----------------------------------|
| `ListModelMixin`     | `GET`       | `/`      | List all model instances.          |
| `CreateModelMixin`   | `POST`      | `/`      | Create a new model instance.       |
| `RetrieveModelMixin` | `GET`       | `/{id}/` | Retrieve a single model instance.  |
| `PutModelMixin`      | `PUT`       | `/{id}/` | Fully update a model instance.     |
| `PatchModelMixin`    | `PATCH`     | `/{id}/` | Partially update a model instance. |
| `DeleteModelMixin`   | `DELETE`    | `/{id}/` | Delete a model instance.           |

### Convenience Mixins

| Mixin              | Bundles                                | Purpose                            |
|:-------------------|:---------------------------------------|:-----------------------------------|
| `ReadModelMixin`   | `ListModelMixin`, `RetrieveModelMixin` | Read-only endpoints.               |
| `UpdateModelMixin` | `PutModelMixin`, `PatchModelMixin`     | Write-only update endpoints.       |
| `CRUDModelMixin`   | All mixins                             | Full Create, Read, Update, Delete. |

## Controller Configuration

Override class variables on your controller to customize behavior.

### `model_class` (Required)
The Django model to be exposed via the API.
```python
class MyController(MixinModelControllerBase, ReadModelMixin):
    model_class = MyModel
```

### `input_schema` & `output_schema`
Override the auto-generated Pydantic schemas. `input_schema` is used for `POST`/`PUT`/`PATCH` bodies. `output_schema` is used for all responses.
```python
class MyController(MixinModelControllerBase, CRUDModelMixin):
    model_class = MyModel
    input_schema = MyCustomInputSchema
    output_schema = MyCustomOutputSchema
```

### `lookup_field`
Customize the URL parameter for single-object lookups. Defaults to the model's primary key (e.g., `{int:id}`).
```python
class MyController(MixinModelControllerBase, ReadModelMixin):
    model_class = MyModel
    # Generates path: /my-model/{str:name}/
    lookup_field = "{str:name}"
```

### `ordering_fields`
Enable and constrain query parameter ordering on list endpoints.
```python
class MyController(MixinModelControllerBase, ReadModelMixin):
    model_class = MyModel
    ordering_fields = ["name", "created_at"]
```
Enables requests like `GET /?ordering=name` and `GET /?ordering=-created_at`.

### `auto_operation_ids` & `operation_id_prefix`
Control OpenAPI `operationId` generation.
```python
class MyController(MixinModelControllerBase, ReadModelMixin):
    model_class = MyModel

    # Option 1: Disable completely
    auto_operation_ids = False

    # Option 2: Add a custom prefix
    # Generates: "listCustomPrefix", "getCustomPrefix"
    operation_id_prefix = "CustomPrefix"
```

## API for Django Choices

If `model_class` is set to a Django `Choices` enum, `ListModelMixin` creates a read-only endpoint that lists the available choices.

**Model**

```python
from django.db import models

class TaskStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"
```

**Controller**
```python
from ninja_extra.mixins import MixinModelControllerBase, ReadModelMixin
from .models import TaskStatus

@api_controller("/task-statuses")
class TaskStatusController(MixinModelControllerBase, ReadModelMixin):
    model_class = TaskStatus
```
A `GET /task-statuses/` request returns a (paginated) list of choices:
```json
[
  {
    "id": "COMPLETED",
    "label": "Completed"
  },
  {
    "id": "PENDING",
    "label": "Pending"
  }
]
```
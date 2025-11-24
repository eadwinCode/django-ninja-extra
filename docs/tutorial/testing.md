# **Testing APIController**

**Django Ninja Extra** has a TestClient that provides seamless testing of `ControllerBase` classes with `pytest`

There are two test clients

- `TestClient`: for synchronous route functions
- `TestAsyncClient`: for asynchronous route functions

Both `TestClient` and `TestAsyncClient` inherit from the Django Ninja `TestClient` class which provides the base functionality 
for making requests to the application, and both of them also have similar methods such as `get`, `post`, `put`, `patch`, `delete`, 
and `options` for making requests to the application.

For example, to test a GET request to the `/users` endpoint, you can use the TestClient as follows:

```python
import pytest
from .controllers import UserController
from ninja_extra.testing import TestClient


@pytest.mark.django_db
class TestMyMathController:
    def test_get_users(self):
        client = TestClient(UserController)
        response = client.get('/users')
        assert response.status_code == 200
        assert response.json()[0] == {
            'first_name': 'Ninja Extra',
            'username': 'django_ninja',
            'email': 'john.doe@gmail.com'
        }

```
Similarly, for testing an asynchronous route function, you can use TestAsyncClient as follows:

```python
from ninja_extra import api_controller, route
from ninja_extra.testing import TestAsyncClient


@api_controller('', tags=['Math'])
class MyMathController:
    @route.get('/add',)
    async def add(self, a: int, b: int):
        """add a to b"""
        return {"result": a - b}

    
class TestMyMathController:
    def test_get_users_async(self):
        client = TestAsyncClient(MyMathController)
        response = client.get('/add', query={"a": 3, "b": 5})
        assert response.status_code == 200
        assert response.json() == {"result": -2}

```

### Controllers with a static prefix

When using `TestClient`/`TestAsyncClient` with a controller class that has a static prefix, call endpoints using the route path defined on the method (without the static prefix). The testing client wires the controller under the hood and resolves routes accordingly.

```python
from ninja_extra import api_controller, route
from ninja_extra.testing import TestClient


@api_controller('/api', tags=['Users'])
class UserController:
    @route.get('/users')
    def list_users(self):
        return [
            {
                'first_name': 'Ninja Extra',
                'username': 'django_ninja',
                'email': 'john.doe@gmail.com',
            }
        ]


def test_get_users():
    client = TestClient(UserController)
    # Note: no '/api' here
    response = client.get('/users')
    assert response.status_code == 200
    assert response.json()[0]['username'] == 'django_ninja'
```

### Controllers with a path variable in the prefix

If the controller prefix contains path parameters, include those parameters in the URL when calling the testing client. For example:

```python
import uuid
from ninja import Schema
from ninja_extra import api_controller, route
from ninja_extra.testing import TestClient


class UserIn(Schema):
    username: str
    email: str


@api_controller('/users/{int:org_id}/', tags=['Users'])
class OrgUsersController:
    @route.post('')
    def create_user(self, org_id: int, user: UserIn):
        # simulate created user
        return {'id': str(uuid.uuid4()), 'org_id': org_id, 'username': user.username}


def test_create_user_under_param_prefix():
    client = TestClient(OrgUsersController)
    response = client.post('/users/123/', json={'username': 'jane', 'email': 'jane@example.com'})
    assert response.status_code == 200
    data = response.json()
    assert data['org_id'] == 123
    assert data['username'] == 'jane'
    assert 'id' in data
```

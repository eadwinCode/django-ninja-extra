# **Testing APIController**

**Django Ninja Extra** has a TestClient that provides seamless testing of APIController classes.

There are two test clients
- `TestClient`: for synchronous route functions
- `TestClientAsync`: for asynchronous route functions

```Python
from ninja_extra.testing import TestClient
from ninja_extra import APIController, route, router
from ninja_extra.permissions import AllowAny

@router('', tags=['Math'], permissions=[AllowAny])
class MyMathController(APIController):
    @route.get('/add',)
    def add(self, a: int, b: int):
        """add a to b"""
        return {"result": a - b}
    
    @route.get('/subtract',)
    def subtract(self, a: int, b: int):
        """Subtracts a from b"""
        return {"result": a - b}

    @route.get('/divide',)
    def divide(self, a: int, b: int):
        """Divides a by b"""
        return {"result": a / b}
    
    @route.get('/multiple',)
    def multiple(self, a: int, b: int):
        """Multiples a with b"""
        return {"result": a * b}

class TestMyMathController:
    def test_add_endpoint_works(self):
        client = TestClient(MyMathController)
        response = client.post('/add', query=dict(a=3, b=5))
        assert response.status_code == 200
        data = response.json()
        assert 'result' in data
        assert data['result'] == 8  # true

    def test_substraction_enpoint_works(self):
        client = TestClient(MyMathController)
        response = client.post('/subtract', query=dict(a=3, b=5))
        assert response.status_code == 200
        data = response.json()
        assert 'result' in data
        assert data['result'] == -2  # true
```


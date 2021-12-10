
Django-Ninja assumes function parameters that are not among path parameters as query parameters.

For example:

```python hl_lines="7 10"
from ninja import constants
from ninja_extra import api_controller, route


@api_controller('', tags=['My Operations'], auth=constants.NOT_SET, permissions=[])
class MyAPIController:
    weapons = ["Ninjato", "Shuriken", "Katana", "Kama", "Kunai", "Naginata", "Yari"]
    
    @route.get("/weapons")
    def list_weapons(self, limit: int = 10, offset: int = 0):
        return self.weapons[offset: offset + limit]
```

To query this operation, you use a URL like:
```
    http://localhost:8000/api/weapons?offset=0&limit=10
```

!!! info
    Read [more](https://django-ninja.rest-framework.com/tutorial/query-params/)
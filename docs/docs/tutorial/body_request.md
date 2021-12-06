# **Request Body**

Request bodies are typically used with “create” and “update” operations (POST, PUT, PATCH).
For example, when creating a resource using POST or PUT, the request body usually contains the representation of the resource to be created.

To declare a **request body**, you need to use **Django Ninja `Schema`** or any Pydantic Schema that suits your need.

I recommend [Ninja-Schema](https://pypi.org/project/ninja-schema/)

## **Create your data model**

Then you declare your data model as a class that inherits from `Schema`.

Use standard Python types for all the attributes:

```Python
from ninja import Schema, constants
from ninja_extra import api_controller, route


class Item(Schema):
    name: str
    description: str = None
    price: float
    quantity: int

    
@api_controller(tags=['My Operations'], auth=constants.NOT_SET, permissions=[])
class MyAPIController:
    @route.post("/items")
    def create(self, item: Item):
        return item

```

Note: if you use **`None`** as the default value for an attribute, it will become optional in the request body.
For example, this model above declares a JSON "`object`" (or Python `dict`) like:

```JSON
{
    "name": "Katana",
    "description": "An optional description",
    "price": 299.00,
    "quantity": 10
}
```

...as `description` is optional (with a default value of `None`), this JSON "`object`" would also be valid:

```JSON
{
    "name": "Katana",
    "price": 299.00,
    "quantity": 10
}
```
# **Request Body**

Request bodies are typically used with “create” and “update” operations (POST, PUT, PATCH).
For example, when creating a resource using POST or PUT, the request body usually contains the representation of the resource to be created.

To declare a **request body**, you need to use **Django Ninja `Schema`**.

!!! info
    Read more on django-ninja **[body request](https://django-ninja.rest-framework.com/tutorial/body/)**

## **Create your data model**

Then you declare your data model as a class that inherits from `Schema`.

Use standard Python types for all the attributes:

```Python 
from ninja import Schema
from ninja_extra import APIController, route


class Item(Schema):
    name: str
    description: str = None
    price: float
    quantity: int


class ItemController(APIController):
    @route.post("/items")
    def create(request, item: Item):
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
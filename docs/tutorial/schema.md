
Django-Ninja Pydantic integration is one of the best features of Django-Ninja. 
With Pydantic, you can validate the inflow and outflow of data from your API, and It's very fast. Making a partial replacement of DRF serializers

But if you want complete DRF Serializer replacement then **Ninja-Schema** is what you need.

## Ninja Schema

Ninja Schema converts your Django ORM models to Pydantic schemas with more Pydantic features supported.

**Inspired by**: [django-ninja](https://django-ninja.rest-framework.com/) and [djantic](https://jordaneremieff.github.io/djantic/)

**Key features:**

- **Custom Field Support**: Ninja Schema converts django model to native pydantic types which gives you quick field validation out of the box. eg Enums, email, IPAddress, URLs, JSON, etc
- **Field Validator**: Fields can be validated with **model_validator** just like pydantic **[validator](https://pydantic-docs.helpmanual.io/usage/validators/)** or **[root_validator](https://pydantic-docs.helpmanual.io/usage/validators/)**. 

!!! info
    Visit [Ninja Schema](https://pypi.org/project/ninja-schema/) for More information

## Accessing Request Object in Schema
Django Ninja Extra provides `RouteContext` object which available during request lifecycle. The `RouteContext` holds

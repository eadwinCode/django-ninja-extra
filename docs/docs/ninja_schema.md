# Ninja Schema

Ninja Schema converts your Django ORM models to Pydantic schemas with more Pydantic features supported.

**Inspired by**: [django-ninja](https://django-ninja.rest-framework.com/) and [djantic](https://jordaneremieff.github.io/djantic/)

**Key features:**

- **Custom Field Support**: Ninja Schema converts django model to native pydantic types which gives you quick field validation out of the box. eg Enums, email, IPAddress, URLs, JSON, etc
- **Field Validator**: Fields can be validated with **model_validator** just like pydantic **[validator](https://pydantic-docs.helpmanual.io/usage/validators/)** or **[root_validator](https://pydantic-docs.helpmanual.io/usage/validators/)**. 

!!! info
    Visit [Ninja Schema](https://pypi.org/project/ninja-schema/) for More information
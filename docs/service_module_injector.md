# Dependency Injection

One of the core features of **Django Ninja Extra** APIController is its support dependency injection using [**Injector** ](https://injector.readthedocs.io/en/latest/)

For example, if you have a service called AuthService and you want to use it in your `UsersController` class, 
you can simply add it as a parameter in the constructor of the class and annotate it with its type.

```python
class UsersController(ControllerBase):
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
```

Then in your application config, you can register this service and its scope. 
By default, services are singleton scoped unless specified.

```python
def configure(binder: Binder) -> Binder:
    binder.bind(AuthService, to=AuthServiceImpl, scope=singleton)
```

You can also specify the scope of the service. 
This is useful when you want to use different instances of the same service for different requests.

```python
def configure(binder: Binder) -> Binder:
    binder.bind(AuthService, to=AuthServiceImpl, scope=noscope)

```

In this way, you can easily inject services into your controllers and use them throughout your application. 
This makes it easy to test your controllers as well as to change the implementation of a service without 
affecting the rest of the application.

!!! info
    Django-Ninja-Extra supports [**django_injector**](https://github.com/blubber/django_injector). There is no extra configuration needed.


## Creating a Service
A service refers to a self-contained module or piece of functionality that can be reused across different parts of an application. 
Services are typically used to encapsulate business logic or to provide access to shared resources, such as databases or external APIs.
Services are often implemented as classes, and they can be accessed through an object-oriented interface. 
Services can be used to perform actions, to interact with external systems, and to perform calculations. 
They usually have some public methods and properties, which allows other objects to interact with them. 
Services are usually used to separate the application logic from the infrastructure, this way the application logic can be reused, tested and maintained independently.

Let's create a simple S3 bucket service, create a `service.py` in your project and add the cold below
```python
from ninja import File
from ninja.files import UploadedFile
from ninja_extra import NinjaExtraAPI, api_controller, http_post

class BucketFileUploadService:
    def upload_file_to_s3(self, file, bucket_name=None, acl="public-read", file_key=None):
        pass

    def upload_existing_file_to_s3(
            self, filepath, file_key, bucket_name=None, acl="public-read", delete_file_afterwards=False,
            clean_up_root_limit=None
    ):
        pass


@api_controller('/user_profile')
class UserProfileController:
    def __init__(self, upload_service: BucketFileUploadService):
        self.upload_service = upload_service
    
    @http_post('/upload')
    def upload_profile_pic(self, file: UploadedFile = File(...)):
        self.upload_service.upload_file_to_s3(file=file)
        return {'message', 'uploaded successfully'}

    
api = NinjaExtraAPI(title='Injector Test')
api.register_controllers(UserProfileController)
```

### Create a module
In Python Injector, a module is a class or a function that is used to configure the dependency injection container. 
A module is responsible for binding services to their implementations and for configuring the scope of services.

A module can define a `configure(binder: Binder)` function that is used to configure the dependency injection container. 
The `binder` argument is an instance of the Binder class that is used to bind services to their implementations.

A module can also define one or more provider functions, which are used to create instances of services. 
These functions can be decorated with `@inject` to specify the dependencies that they need to be resolved, 
and they can be decorated with `@provider` to indicate that they should be used to create instances of services.

For example:
```python
from injector import Binder, singleton, inject, provider

class MyModule:
    def configure(self, binder: Binder) -> Binder:
        binder.bind(AuthService, to=AuthServiceImpl, scope=singleton)

    @provider
    @inject
    def provide_user_service(self, auth_service: AuthService) -> UserService:
        return UserService(auth_service)

```
In the example above, `MyModule` class has `configure` method which is used to bind the `AuthService` and set the scope 
as `singleton` and `provide_user_service` which is decorated with `@provider` and `@inject` to provide 
`UserService` and the `AuthService` is injected to it as a dependency.

By registering a module in Ninja Extra settings, all the services, providers and configurations defined in the module 
will be added to the Injector, and these services can be resolved and used throughout the application.

Lets creates a module for the `BucketFileUpload` service we created earlier. Create a `module.py` in your project and add the code below.

```python
import logging
import os

from typing import cast
from django.conf import Settings
from injector import inject, Module, Binder, singleton

logger = logging.getLogger()

class InMemoryBucketFileUpload(BucketFileUpload):
    @inject
    def __init__(self, settings: Settings):
        logger.info(f"===== Using InMemoryBucketFileUpload =======")
        self.settings = settings
        assert isinstance(self.settings, Settings)

    def upload_file_to_s3(self, file, bucket_name=None, acl="public-read", file_key=None):
        logger.info(
            f"InMemoryBucketFileUpload ---- "
            f"upload_file_to_s3(file={file.filename}, bucket_name{bucket_name}, acl={acl}, file_key={file_key})"
        )
        if not file_key:
            return os.path.join(self.settings.UPLOAD_FOLDER, file.filename)
        return os.path.join(self.settings.BASE_DIR, file_key)

    def upload_existing_file_to_s3(self, filepath, file_key, bucket_name=None, acl="public-read",
                                   delete_file_afterwards=False, clean_up_root_limit=None):
        logger.info(f"InMemoryBucketFileUpload ---- upload_existing_file_to_s3("
                    f"filepath={filepath}, file_key={file_key}, "
                    f"bucket_name={bucket_name}, acl={acl}, delete_file_afterwards={delete_file_afterwards})")
        return filepath


class FileServiceModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(BucketFileUpload, to=InMemoryBucketFileUpload, scope=singleton)

```
We have created a `FileServiceModule` that binds `BucketFileUpload` to `InMemoryBucketFileUpload`. 
In our application, when `BucketFileUpload` is resolved we will get an instance of `InMemoryBucketFileUpload` provided for us by the injector.
We also used `inject` decorator from `injector` to inject django settings to `InMemoryBucketFileUpload` service.

The `InMemoryBucketFileUpload` concrete class is a simple class for development. In production time, you meant want to write a better service to saves file to your AWS S3 bucket.

## Service Scope

A scope defines the lifespan of a service created. There are three major scope when working with dependency injection in a web framework

### `singleton` scope
A singleton service is created only once and the same instance is reused for the entire lifetime of the application. 
This is the default scope when no scope is specified.

```python
from injector import Module, Binder, singleton

class FileServiceModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(BucketFileUpload, to=InMemoryBucketFileUpload, scope=singleton)
```

### `transient` scope
A transient service is created each time it's requested. 
A new instance is created for each request. 
This is useful for services that do not maintain state or services that should not be shared across multiple requests.

```python
from injector import Module, Binder, noscope

class FileServiceModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(BucketFileUpload, to=InMemoryBucketFileUpload, scope=noscope)
```

### `scoped`
A scoped service is created once per request. A new instance is created for each incoming request and is shared among 
all components that depend on it within the same request. This is useful for services that maintain request-specific state.

Currently, Ninja extra does not support `scoped` scope service.

It's important to choose the appropriate scope when registering services with the dependency injection container. 
`Singleton` services are suitable for services that maintain application-wide state, 
`transient` services are suitable for services that do not maintain state, and 
`scoped` services are suitable for services that maintain request-specific state.


## Adding Service to Controllers
Ninja Extra controllers constructor (`__init__`) are decorated with `inject` function from `injector` library. 
This makes it possible define parameter in a parameter in the constructor with a type annotation and the annotated type gets injected during object instantiation.

We have created a `BucketFileUpload` contract and some concrete implementations, lets add it to a controller.

Lets create a `controller.py` with the code below

```python
from ninja import File
from ninja.files import UploadedFile
from ninja_extra import NinjaExtraAPI, api_controller, http_post
from .modules import BucketFileUpload, InMemoryBucketFileUpload

@api_controller('/user_profile')
class UserProfileController:
    def __init__(self, upload_service: BucketFileUpload):
        self.upload_service = upload_service
    
    @http_post('/upload')
    def upload_profile_pic(self, file: UploadedFile = File(...)):
        self.upload_service.upload_file_to_s3(file=file)
        assert isinstance(self.upload_service, InMemoryBucketFileUpload) # True
        return {'message', 'uploaded successfully'}

    
api = NinjaExtraAPI(title='Injector Test')
api.register_controllers(UserProfileController)
```

Now, we have defined an `BucketFileUpload` service dependence to our `UserProfileController`. 
We need to register `FileServiceModule` to settings to avoid getting `UnsatisedRequirement` exception from injector when Ninja extra tries to create the object.

## **Module Registration**
There are different ways of registering injector Modules in a Django app. 

- **django_injector**: if you are using django_inject, it has documentation on how to register a module.
- **ninja_extra**: you can provide module string path in `INJECTOR_MODULES` in `NINJA_EXTRA` field as shown below:

### Registering based on Ninja Extra
We register modules to `INJECTOR_MODULES` key in Ninja Extra settings in django settings.py

```python
NinjaExtra = {
    'INJECTOR_MODULES': [
        'myproject.app1.modules.SomeModule',
        'myproject.app2.modules.SomeAppModule',
    ]
}
```

Let's register `FileServiceModule` module to the `NinjaExtra` settings,

```python
# settings.py
...
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

NinjaExtra = {
    'INJECTOR_MODULES': [
        'myproject.modules.FileServiceModule'
    ]
}
...
```

That's it. We have completely wired `BucketFileUpload` service to `UserProfileController`.

!!! warning
    You are not only allowed to override your APIController constructor with **parameter** that don't have **annotations**
    Read more [**Python Injector** ](https://injector.readthedocs.io/en/latest/)


## Using `service_resolver`
The `service_resolver` is a utility class that help resolves types registered in the `injector` instance. I could be in handle when we need a service resolved outside controllers.

For example:
```python
from ninja_extra import service_resolver
from .service import BucketFileUpload


bucket_service = service_resolver(BucketFileUpload)
bucket_service.upload_file_to_s3('/path/to/file')

```

We can also resolve more than one service at a time and a tuple result will be returned.

```python
from ninja_extra import service_resolver
from .service import BucketFileUpload


bucket_service, service_a, service_b = service_resolver(BucketFileUpload, AnotherServiceA, AnotherServiceB)
bucket_service.upload_file_to_s3('/path/to/file')

service_a.do_something()
service_b.do_something()

```

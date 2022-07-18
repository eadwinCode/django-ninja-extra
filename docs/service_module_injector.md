# Dependency Injection

One of the core features of **Django Ninja Extra** APIController is its support dependency injection. 

Having the ability to inject services to the controller is as simple as
overriding your controller constructor and defining a parameter with its type annotation. 

Under the hood, APIController `__init__` is wrapped with python [**Injector** ](https://injector.readthedocs.io/en/latest/) library `inject` function. By so doing, it's easy to resolve APIController dependencies. 

During APIController class initialization, the injector instance is used to resolve the APIController instance, and parameters with annotations will be resolved automatically.

!!! info
    Django-Ninja-Extra supports [**django_injector**](https://github.com/blubber/django_injector). There is no extra configuration needed.

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

## **Module Registration**
There are different ways of registering injector Modules in a Django app. 

- **django_injector**: if you are using django_inject, it has documentation on how to register a module.
- **ninja_extra**: you can provide module string path in `INJECTOR_MODULES` in `NINJA_EXTRA` field as shown below:

```python
NinjaExtra = {
    'INJECTOR_MODULES': [
        'myproject.app1.modules.SomeModule',
        'myproject.app2.modules.SomeAppModule',
    ]
}
```

### Create a module
create a `modules.py` with the code below in your django-project

```python
import logging
import os

from typing import Any, cast
from django.conf import Settings
from injector import inject, Module, Binder, singleton

logger = logging.getLogger()


class BucketFileUpload:
    def upload_file_to_s3(self, file, bucket_name=None, acl="public-read", file_key=None):
        raise NotImplementedError()

    def upload_existing_file_to_s3(
            self, filepath, file_key, bucket_name=None, acl="public-read", delete_file_afterwards=False,
            clean_up_root_limit=None
    ):
        raise NotImplementedError()
    

class InMemoryBucketFileUpload(BucketFileUpload):
    @inject
    def __init__(self, settings: Settings):
        logger.info(f"===== Using InMemoryBucketFileUpload =======")
        self.settings = cast(Any, settings)

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

Create a `controller.py` with the code below
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
### Register your Module
In your django `settings.py`, add your `FileServiceModule` module to the `NinjaExtra` settings

```python
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

!!! warning
    You are not only allowed to override your APIController constructor with **parameter** that don't have **annotations**
    Read more [**Python Injector** ](https://injector.readthedocs.io/en/latest/)

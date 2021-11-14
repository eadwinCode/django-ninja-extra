# **Custom Exception**
**Django-Ninja** provide a flask way of handling custom exceptions by registering its exception handlers.

**Django-Ninja-Extra** creates an `APIException` class which provides similar functionalities, for those use to DRF `APIException`.

For Example: 
```python
from ninja_extra.exceptions import APIException
from ninja_extra import status
from ninja_extra import router, APIController, route, NinjaExtraAPI


class CustomAPIException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = 'UnAuthorized'

    
@router('/users', tags=["exception"])
class MyController(APIController):
    @route.get('/exception')
    def custom_exception(self):
        raise CustomAPIException()

    
api = NinjaExtraAPI(title='Exception Test')
api.register_controllers(MyController)
```
![Preview](../images/custom_exception.gif)
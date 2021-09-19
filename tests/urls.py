from django.contrib import admin
from django.urls import path

from ninja_extra import NinjaExtraAPI

from .controllers import EventController

api = NinjaExtraAPI()
api.register_controllers(EventController)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

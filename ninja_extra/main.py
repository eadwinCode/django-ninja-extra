from typing import List
from ninja import NinjaAPI
from ninja_extra.controllers.base import APIController

__all__ = ['NinjaExtraAPI', ]


class NinjaExtraAPI(NinjaAPI):
    def register_controllers(self, *controllers: List[APIController]):
        for controller in controllers:
            controller_instance = object.__new__(controller)
            self._routers.extend(controller_instance.build_routers())
            controller_instance.set_api_instance(self)

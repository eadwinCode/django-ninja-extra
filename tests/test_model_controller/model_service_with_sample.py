from typing import Any

from injector import inject
from pydantic import BaseModel

from ninja_extra import ModelService
from ninja_extra.controllers.base import ModelControllerBase, api_controller
from ninja_extra.controllers.model.schemas import ModelConfig

from ..models import Event


class LoggingService:
    def __init__(self):
        pass

    def log(self, message: str):
        print(message)


class EventModelService(ModelService):
    """
    EventModelService is a custom model service that allows for logging of events.
    """

    @inject
    def __init__(self, model: Event, logging_service: LoggingService):
        super().__init__(model=model)
        self.logging_service = logging_service

    def create(self, schema: BaseModel, **kwargs: Any) -> Any:
        self.logging_service.log("Creating event")
        return super().create(schema, **kwargs)


@api_controller("/events")
class EventModelController(ModelControllerBase):
    service_type = EventModelService
    model_config = ModelConfig(model=Event)

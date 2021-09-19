from datetime import date
from typing import List

from django.shortcuts import get_object_or_404
from pydantic import BaseModel

from ninja_extra import APIController, route, router

from .models import Event


class EventSchema(BaseModel):
    title: str
    start_date: date
    end_date: date

    class Config:
        orm_mode = True


@router("events")
class EventController(APIController):
    @route.post("/create", url_name="event-create-url-name")
    def create_event(self, event: EventSchema):
        Event.objects.create(**event.dict())
        return event

    @route.get("", response=List[EventSchema])
    def list_events(self):
        return list(Event.objects.all())

    @route.get("/{id}", response=EventSchema)
    def get_event(self, id: int):
        event = get_object_or_404(Event, id=id)
        return event

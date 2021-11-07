from datetime import date
from typing import List

from django.shortcuts import get_object_or_404
from ninja import Schema

from ninja_extra import APIController, route, router

from .models import Event


class EventSchema(Schema):
    title: str
    start_date: date
    end_date: date

    class Config:
        orm_mode = True


class EventSchemaOut(Schema):
    id: int


@router("events")
class EventController(APIController):
    @route.post(
        "/create", url_name="event-create-url-name", response={201: EventSchemaOut}
    )
    def create_event(self, event: EventSchema):
        event = Event.objects.create(**event.dict())
        return 201, event

    @route.get("", response=List[EventSchema])
    def list_events(self):
        return list(Event.objects.all())

    @route.get("/{int:id}", response=EventSchema)
    def get_event(self, id: int):
        event = get_object_or_404(Event, id=id)
        return event

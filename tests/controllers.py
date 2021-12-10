from datetime import date
from typing import List

from django.shortcuts import get_object_or_404
from ninja import Schema

from ninja_extra import api_controller, http_get, http_post

from .models import Event


class EventSchema(Schema):
    title: str
    start_date: date
    end_date: date

    class Config:
        orm_mode = True


class EventSchemaOut(Schema):
    id: int


@api_controller("events")
class EventController:
    @http_post("", url_name="event-create-url-name", response={201: EventSchemaOut})
    def create_event(self, event: EventSchema):
        event = Event.objects.create(**event.dict())
        return 201, event

    @http_get(
        "",
        response=List[EventSchema],
        url_name="event-list",
    )
    def list_events(self):
        return list(Event.objects.all())

    @http_get(
        "/list",
        response=List[EventSchema],
        url_name="event-list-2",
    )
    def list_events_example_2(self):
        return list(Event.objects.all())

    @http_get("/{int:id}", response=EventSchema)
    def get_event(self, id: int):
        event = get_object_or_404(Event, id=id)
        return event

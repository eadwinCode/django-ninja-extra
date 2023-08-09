import json
from datetime import datetime, timedelta

import pytest

from ninja_extra.testing import TestClient

from .controllers import EventController, EventSchema
from .models import Event


@pytest.mark.django_db
class TestEventController:
    dummy_data = {
        "title": "TestEvent1Title",
        "start_date": str(datetime.now().date()),
        "end_date": str((datetime.now() + timedelta(days=5)).date()),
    }

    def test_create_event_works(self):
        client = TestClient(EventController)
        response = client.post(
            "",
            json={
                "title": "TestEvent1Title",
                "start_date": str(datetime.now().date()),
                "end_date": str((datetime.now() + timedelta(days=5)).date()),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert Event.objects.filter(pk=data.get("id")).exists()

    def test_list_events_works(self):
        for i in range(3):
            object_data = self.dummy_data.copy()
            object_data.update(title=f"{object_data['title']}_{i+1}")
            Event.objects.create(**object_data)

        client = TestClient(EventController)
        response = client.get("")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        event_schema = [
            json.loads(EventSchema.from_orm(item).json())
            for item in Event.objects.all()
        ]
        assert event_schema == data

    @pytest.mark.parametrize(
        "path",
        [
            "/{event_id}",
            "/{event_id}/from-orm",
        ],
    )
    def test_get_event_works(self, path):
        object_data = self.dummy_data.copy()
        object_data.update(title=f"{object_data['title']}_get")

        event = Event.objects.create(**object_data)
        client = TestClient(EventController)
        response = client.get(path.format(event_id=event.id))
        assert response.status_code == 200
        data = response.json()
        event_schema = json.loads(EventSchema.from_orm(event).json())
        assert event_schema == data

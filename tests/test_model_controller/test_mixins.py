import pytest

from ninja_extra import api_controller
from ninja_extra.mixins import (
    DeleteModelMixin,
    ListModelMixin,
    MixinModelControllerBase,
    PatchModelMixin,
    PutModelMixin,
    RetrieveModelMixin,
)
from ninja_extra.testing import TestClient

from ..models import Event


def test_controller_without_model_class():
    with pytest.raises(Exception):

        @api_controller("/mixin-case-1")
        class EventMixinModelControllerBase(MixinModelControllerBase):
            pass


def test_empty_controller():
    @api_controller("/mixin-case-1")
    class EventMixinModelControllerBase(MixinModelControllerBase):
        model_class = Event

    TestClient(EventMixinModelControllerBase)

    # todo: how to test???


@pytest.mark.django_db
def test_list_controller():
    @api_controller("/mixin-list", tags=["Events"])
    class EventMixinModelControllerBase(MixinModelControllerBase, ListModelMixin):
        model_class = Event

    client = TestClient(EventMixinModelControllerBase)

    events = [
        Event.objects.create(
            title="Testing", end_date="2020-01-02", start_date="2020-01-01"
        ),
        Event.objects.create(
            title="Testing", end_date="2020-01-02", start_date="2020-01-01"
        ),
    ]

    resp = client.get(
        "/",
    )
    assert resp.json()["count"] == len(events)

    for event in events:
        event.delete()


@pytest.mark.django_db
def test_retrieve_controller():
    @api_controller("/mixin-retrieve", tags=["Events"])
    class EventMixinModelControllerBase(MixinModelControllerBase, RetrieveModelMixin):
        model_class = Event

    client = TestClient(EventMixinModelControllerBase)
    event1 = Event.objects.create(
        title="Testing", end_date="2020-01-02", start_date="2020-01-01"
    )

    resp = client.get(
        f"/{event1.pk}",
    )
    assert resp.json()["title"] == event1.title

    event1.delete()


@pytest.mark.django_db
def test_patch_controller():
    @api_controller("/mixin-patch", tags=["Events"])
    class EventMixinModelControllerBase(MixinModelControllerBase, PatchModelMixin):
        model_class = Event

    client = TestClient(EventMixinModelControllerBase)
    event1 = Event.objects.create(
        title="Testing", end_date="2020-01-02", start_date="2020-01-01"
    )

    new_title = "Updated!"
    resp = client.patch(f"/{event1.pk}", json={"title": new_title})
    assert resp.json()["title"] == new_title

    event1.delete()


@pytest.mark.django_db
def test_put_controller():
    @api_controller("/mixin-put")
    class EventMixinModelControllerBase(MixinModelControllerBase, PutModelMixin):
        model_class = Event

    client = TestClient(EventMixinModelControllerBase)
    event1 = Event.objects.create(
        title="Testing", end_date="2020-01-02", start_date="2020-01-01"
    )

    new_title = "Updated!"
    new_start = "2025-01-01"
    new_end = "2025-12-31"
    resp = client.put(
        f"/{event1.pk}",
        json={"title": new_title, "start_date": new_start, "end_date": new_end},
    )
    assert resp.json()["title"] == new_title
    assert resp.json()["start_date"] == new_start
    assert resp.json()["end_date"] == new_end

    event1.delete()


@pytest.mark.django_db
def test_delete_controller():
    @api_controller()
    class EventMixinModelControllerBase(MixinModelControllerBase, DeleteModelMixin):
        model_class = Event

    client = TestClient(EventMixinModelControllerBase)
    event1 = Event.objects.create(
        title="Testing", end_date="2020-01-02", start_date="2020-01-01"
    )

    resp = client.delete(f"/{event1.pk}")
    assert resp.status_code == 204
    assert not Event.objects.filter(id=event1.pk).exists()

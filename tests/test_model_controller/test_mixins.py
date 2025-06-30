import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from ninja_extra import ModelConfig, api_controller
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


@pytest.fixture
def controller_client_factory():
    def _factory(*mixins):
        # Dynamically create a controller class with the given mixins
        @api_controller
        class DynamicControllerClass(MixinModelControllerBase, *mixins):
            model_class = Event

        return TestClient(DynamicControllerClass)

    return _factory


@pytest.fixture
def event_obj(db):
    """Provides a single, clean Event object for tests that need one."""
    return Event.objects.create(
        title="Initial Title", end_date="2025-01-02", start_date="2025-01-01"
    )


def test_controller_without_model_class_raises_specific_error():
    """
    Test that a mixincontroller without `model_class` attribute raises specific error.
    """
    with pytest.raises(
        ImproperlyConfigured, match="must define a model_class attribute"
    ):

        @api_controller
        class FaultyController(MixinModelControllerBase):
            pass


def test_empty_controller_returns_404(controller_client_factory):
    """
    Test an empty controller without any mixins.
    """
    client = controller_client_factory()
    with pytest.raises(Exception, match='Cannot resolve "/"'):
        client.get("/")


@pytest.mark.django_db
def test_list_controller(controller_client_factory):
    """
    Test retrieving a paginated list of objects.
    """
    client = controller_client_factory(ListModelMixin)
    Event.objects.create(
        title="Event 1", end_date="2025-01-02", start_date="2025-01-01"
    )
    Event.objects.create(
        title="Event 2", end_date="2025-01-03", start_date="2025-01-04"
    )

    response = client.get("/")

    assert response.status_code == 200
    assert response.json().get("count", 0) == 2


@pytest.mark.django_db
def test_modelconfig_controller(controller_client_factory):
    """
    Test retrieving a paginated list of objects fro.
    """

    @api_controller
    class EventController(MixinModelControllerBase, ListModelMixin):
        model_config = ModelConfig(model=Event)

    client = TestClient(EventController)
    Event.objects.create(
        title="Event 11", end_date="2025-01-02", start_date="2025-01-01"
    )
    Event.objects.create(
        title="Event 22", end_date="2025-01-03", start_date="2025-01-04"
    )

    response = client.get("/")

    assert response.status_code == 200
    assert response.json().get("count", 0) == 2


@pytest.mark.django_db
def test_retrieve_controller(controller_client_factory, event_obj):
    """Test retrieving a single, existing item."""
    client = controller_client_factory(RetrieveModelMixin)
    response = client.get(f"/{event_obj.pk}")

    assert response.status_code == 200
    assert response.json()["title"] == event_obj.title


@pytest.mark.django_db
def test_retrieve_not_found(controller_client_factory):
    """
    Test that requesting a non-existent object returns a 404.
    """
    client = controller_client_factory(RetrieveModelMixin)
    response = client.get("/9999")
    assert response.status_code == 404


@pytest.mark.django_db
def test_patch_controller(controller_client_factory, event_obj):
    """
    Verify database persistence for PATCH.
    """
    client = controller_client_factory(PatchModelMixin)
    new_title = "Updated!"

    response = client.patch(f"/{event_obj.pk}", json={"title": new_title})

    assert response.status_code == 200
    assert response.json()["title"] == new_title

    # Verify the change was actually saved
    event_obj.refresh_from_db()
    assert event_obj.title == new_title


@pytest.mark.django_db
def test_put_controller(controller_client_factory, event_obj):
    """
    Verify database persistence for PUT.
    """
    client = controller_client_factory(PutModelMixin)
    payload = {
        "title": "Full Update Title",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
    }
    response = client.put(f"/{event_obj.pk}", json=payload)

    assert response.status_code == 200

    # Verify the change was saved
    event_obj.refresh_from_db()
    assert event_obj.title == payload["title"]
    assert str(event_obj.start_date) == payload["start_date"]


@pytest.mark.django_db
def test_put_fails_with_partial_data(controller_client_factory, event_obj):
    """
    Ensure that a request with missing data fails with a 422 Unprocessable Entity error.
    """
    client = controller_client_factory(PutModelMixin)
    payload = {"title": "Partial Update"}  # Missing start_date and end_date

    response = client.put(f"/{event_obj.pk}", json=payload)
    assert response.status_code == 422


@pytest.mark.django_db
def test_delete_controller(controller_client_factory, event_obj):
    """
    Ensure that the specified object is deleted from the database.
    """

    client = controller_client_factory(DeleteModelMixin)
    response = client.delete(f"/{event_obj.pk}")

    assert response.status_code == 204
    assert not Event.objects.filter(id=event_obj.pk).exists()


@pytest.mark.django_db
def test_text_choices_controller(controller_client_factory, event_obj):
    """
    Ensure that the specified object is deleted from the database.
    """

    class CoffeeCycle(models.TextChoices):
        # The moment of creation.
        INIT = "__init__", "Instantiated: The Cup is Full"

        # The representation of the coffee.
        REPR = "__repr__", "Official String Representation: 'Hot, Black Coffee'"

        # What happens when you add milk.
        ADD = "__add__", "Overloaded: Now with Milk"

        # The end of the coffee's life.
        DEL = "__del__", "Garbage Collected: The Cup is Empty"

    @api_controller
    class CoffeeControllerAPI(MixinModelControllerBase, ListModelMixin):
        model_class = CoffeeCycle

    client = TestClient(CoffeeControllerAPI)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "count": 4,
        "next": None,
        "previous": None,
        "results": [
            {"id": "__del__", "label": "Garbage Collected: The Cup is Empty"},
            {"id": "__init__", "label": "Instantiated: The Cup is Full"},
            {
                "id": "__repr__",
                "label": "Official String Representation: 'Hot, Black Coffee'",
            },
            {"id": "__add__", "label": "Overloaded: Now with Milk"},
        ],
    }


@pytest.mark.django_db
def test_integer_choices_controller():
    """
    Tests that the ListModelMixin correctly serves a Django IntegerChoices enum,
    with integer IDs and labels sorted alphabetically.
    """

    # 1. Define an IntegerChoices class for the test
    class PythonRelease(models.IntegerChoices):
        LEGACY = 2, "Legacy Python"
        MODERN = 3, "Modern Python"
        THE_FUTURE = 4, "The Future (Maybe)"

    # 2. Create a controller that uses the IntegerChoices class
    @api_controller
    class PythonReleaseController(MixinModelControllerBase, ListModelMixin):
        model_class = PythonRelease

    # 3. Instantiate the client and make the request
    client = TestClient(PythonReleaseController)
    response = client.get("/")

    # 4. Assert the response is correct
    assert response.status_code == 200

    # The expected JSON response. IDs are integers, and the list is
    # sorted by the label text.
    expected_data = {
        "count": 3,
        "next": None,
        "previous": None,
        "results": [
            {"id": 2, "label": "Legacy Python"},
            {"id": 3, "label": "Modern Python"},
            {"id": 4, "label": "The Future (Maybe)"},
        ],
    }

    assert response.json() == expected_data

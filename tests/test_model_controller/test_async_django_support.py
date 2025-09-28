from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel

from ninja_extra.controllers.model.service import ModelService, _async_django_support
from ninja_extra.exceptions import NotFound

from ..models import Event


class EventTestSchema(BaseModel):
    title: str
    start_date: str
    end_date: str


class TestAsyncDjangoSupport:
    """Test the _async_django_support decorator functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = ModelService(Event)
        self.test_schema = EventTestSchema(
            title="Test Event", start_date="2020-01-01", end_date="2020-01-02"
        )

    @pytest.mark.asyncio
    @patch(
        "ninja_extra.controllers.model.service.django_version_greater_than_4_2", False
    )
    @patch("ninja_extra.controllers.model.service.sync_to_async")
    async def test_async_django_support_with_exception_in_sync_method(
        self, mock_sync_to_async
    ):
        """Test decorator behavior when sync method raises an exception in Django < 4.2"""

        # Mock sync method that raises an exception
        sync_method = Mock(side_effect=NotFound("Test error"))
        mock_async_wrapper = AsyncMock(side_effect=NotFound("Test error"))
        mock_sync_to_async.return_value = mock_async_wrapper

        # Add the sync method to the service instance
        self.service.test_sync_method = sync_method

        # Create a dummy async method
        async_method = AsyncMock()

        # Apply the decorator
        decorated_method = _async_django_support("test_sync_method")(async_method)

        # Verify the exception is propagated
        with pytest.raises(NotFound, match="Test error"):
            await decorated_method(self.service, "test_arg")

    @pytest.mark.asyncio
    @patch(
        "ninja_extra.controllers.model.service.django_version_greater_than_4_2", True
    )
    async def test_async_django_support_with_exception_in_async_method(self):
        """Test decorator behavior when async method raises an exception in Django >= 4.2"""

        # Mock an async method that raises an exception
        original_async_method = AsyncMock(side_effect=NotFound("Async test error"))

        # Apply the decorator
        decorated_method = _async_django_support("sync_method_name")(
            original_async_method
        )

        # Verify the exception is propagated
        with pytest.raises(NotFound, match="Async test error"):
            await decorated_method(self.service, "test_arg")

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_actual_model_service_methods_with_django_4_2_true(self):
        """Integration test with actual ModelService methods when Django >= 4.2"""

        with patch(
            "ninja_extra.controllers.model.service.django_version_greater_than_4_2",
            True,
        ):
            # Test create_async
            event = await self.service.create_async(self.test_schema)
            assert event.title == "Test Event"
            assert str(event.start_date) == "2020-01-01"

            # Test get_one_async
            retrieved_event = await self.service.get_one_async(event.pk)
            assert retrieved_event.id == event.id
            assert retrieved_event.title == "Test Event"

            # Test update_async
            update_schema = EventTestSchema(
                title="Updated Event", start_date="2020-01-01", end_date="2020-01-02"
            )
            updated_event = await self.service.update_async(event, update_schema)
            assert updated_event.title == "Updated Event"

            # Test delete_async
            await self.service.delete_async(event)

            # Verify event is deleted
            with pytest.raises(NotFound):
                await self.service.get_one_async(event.pk)

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_actual_model_service_methods_with_django_4_2_false(self):
        """Integration test with actual ModelService methods when Django < 4.2"""

        with patch(
            "ninja_extra.controllers.model.service.django_version_greater_than_4_2",
            False,
        ):
            # Test create_async (should fall back to sync method)
            event = await self.service.create_async(self.test_schema)
            assert event.title == "Test Event"
            assert str(event.start_date) == "2020-01-01"

            # Test get_one_async (should fall back to sync method)
            retrieved_event = await self.service.get_one_async(event.pk)
            assert retrieved_event.id == event.id
            assert retrieved_event.title == "Test Event"

            # Test update_async (should fall back to sync method)
            update_schema = EventTestSchema(
                title="Updated Event Sync",
                start_date="2020-01-01",
                end_date="2020-01-02",
            )
            updated_event = await self.service.update_async(event, update_schema)
            assert updated_event.title == "Updated Event Sync"

            # Test delete_async (should fall back to sync method)
            await self.service.delete_async(event)

            # Verify event is deleted
            with pytest.raises(NotFound):
                await self.service.get_one_async(event.pk)

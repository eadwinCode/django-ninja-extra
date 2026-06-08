import json

import pytest
from ninja import JSONL, SSE, Schema

from ninja_extra import NinjaExtraAPI, api_controller, http_get
from ninja_extra.testing import TestAsyncClient, TestClient


class StreamItem(Schema):
    name: str
    price: float


@api_controller("/streaming-sync")
class StreamingSyncController:
    @http_get("/jsonl", response=JSONL[StreamItem])
    def stream_jsonl(self):
        for i in range(3):
            yield {"name": f"item-{i}", "price": float(i)}

    @http_get("/sse", response=SSE[StreamItem])
    def stream_sse(self):
        for i in range(3):
            yield {"name": f"item-{i}", "price": float(i)}


@api_controller("/streaming-async")
class StreamingAsyncController:
    @http_get("/jsonl", response=JSONL[StreamItem])
    async def stream_jsonl_async(self):
        for i in range(3):
            yield {"name": f"item-{i}", "price": float(i)}

    @http_get("/sse", response=SSE[StreamItem])
    async def stream_sse_async(self):
        for i in range(3):
            yield {"name": f"item-{i}", "price": float(i)}


class TestNinjaExtraStreamingSync:
    def test_jsonl_controller_sync(self):
        api = NinjaExtraAPI()
        api.register_controllers(StreamingSyncController)
        client = TestClient(api)

        response = client.get("/streaming-sync/jsonl")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/jsonl"

        lines = response.content.decode().strip().split("\n")
        assert len(lines) == 3
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data == {"name": f"item-{i}", "price": float(i)}

    def test_sse_controller_sync(self):
        api = NinjaExtraAPI()
        api.register_controllers(StreamingSyncController)
        client = TestClient(api)

        response = client.get("/streaming-sync/sse")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"

        content = response.content.decode()
        events = content.strip().split("\n\n")
        assert len(events) == 3


@pytest.mark.asyncio
class TestNinjaExtraStreamingAsync:
    async def test_jsonl_controller_async(self):
        api = NinjaExtraAPI()
        api.register_controllers(StreamingAsyncController)
        async_client = TestAsyncClient(api)

        response = await async_client.get("/streaming-async/jsonl")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/jsonl"

        lines = response.content.decode().strip().split("\n")
        assert len(lines) == 3
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data == {"name": f"item-{i}", "price": float(i)}

    async def test_sse_controller_async(self):
        api = NinjaExtraAPI()
        api.register_controllers(StreamingAsyncController)
        async_client = TestAsyncClient(api)

        response = await async_client.get("/streaming-async/sse")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"

        content = response.content.decode()
        events = content.strip().split("\n\n")
        assert len(events) == 3

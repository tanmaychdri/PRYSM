import pytest

from prysm.core.events import EventBus


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []
    
    async def handler(data: str):
        received.append(data)
        
    bus.subscribe("test_event", handler)
    await bus.publish("test_event", "hello")
    
    assert received == ["hello"]

@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []
    
    async def handler(data: str):
        received.append(data)
        
    bus.subscribe("test_event", handler)
    bus.unsubscribe("test_event", handler)
    await bus.publish("test_event", "hello")
    
    assert received == []

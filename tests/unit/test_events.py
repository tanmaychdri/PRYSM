import pytest

from prysm.core.events import EventBus, StateChanged


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []

    async def handler(event: StateChanged):
        received.append(event)

    bus.subscribe(StateChanged, handler)
    event = StateChanged(previous_state="IDLE", new_state="LISTENING")
    await bus.publish(event)

    assert len(received) == 1
    assert received[0] is event


@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []

    async def handler(event: StateChanged):
        received.append(event)

    bus.subscribe(StateChanged, handler)
    bus.unsubscribe(StateChanged, handler)
    event = StateChanged(previous_state="IDLE", new_state="LISTENING")
    await bus.publish(event)

    assert received == []

import asyncio
import logging

from prysm.core.events import EventBus, MobileEvent
from prysm.mobile.models import EventMessage
from prysm.mobile.registry import DeviceRegistry
from prysm.mobile.server import MobileServer

logger = logging.getLogger(__name__)


class MobileService:
    """
    Main PRYSM integration point for mobile devices.
    Wraps the MobileServer and bridges Android events to the PRYSM EventBus.
    """

    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.registry = DeviceRegistry()
        self.server = MobileServer(self.registry)

        self.server.on_event_received = self._handle_event
        self.server.on_device_connected = self._handle_connect
        self.server.on_device_disconnected = self._handle_disconnect

    async def start(self):
        """Start the mobile service in the background."""
        asyncio.create_task(self.server.start())
        logger.info("Mobile Service started.")

    def begin_pairing(self) -> str:
        """Starts the pairing process and returns the 6-digit code."""
        return self.server.begin_pairing()

    def get_connected_devices(self) -> list[str]:
        return list(self.server.active_connections.keys())

    async def send_device_request(
        self, device_id: str, action: str, payload: dict
    ) -> dict:
        """Send a request to a device and get the result payload."""
        response = await self.server.send_request(device_id, action, payload)
        if response and response.success:
            return response.payload
        raise RuntimeError(
            f"Request failed: {response.error if response else 'Timeout'}"
        )

    def _handle_event(self, msg: EventMessage):
        """Route Android events into PRYSM."""
        logger.debug(f"Received mobile event: {msg.event} from {msg.device_id}")
        asyncio.create_task(self.bus.publish(
            MobileEvent(
                event_type=f"mobile.{msg.event}",
                payload={"device_id": msg.device_id, **msg.payload},
            )
        ))

    def _handle_connect(self, device_id: str):
        dev = self.registry.get_device(device_id)
        name = dev.name if dev else device_id
        asyncio.create_task(self.bus.publish(
            MobileEvent(
                event_type="mobile.device.connected",
                payload={"device_id": device_id, "name": name},
            )
        ))

    def _handle_disconnect(self, device_id: str):
        dev = self.registry.get_device(device_id)
        name = dev.name if dev else device_id
        asyncio.create_task(self.bus.publish(
            MobileEvent(
                event_type="mobile.device.disconnected",
                payload={"device_id": device_id, "name": name},
            )
        ))

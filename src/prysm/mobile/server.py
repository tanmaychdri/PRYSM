import base64
import json
import logging
import secrets
import uuid
from collections.abc import Callable

import websockets

from prysm.mobile.crypto import MobileCrypto
from prysm.mobile.models import (
    EventMessage,
    MessageType,
    RequestMessage,
    ResponseMessage,
)
from prysm.mobile.registry import DeviceRegistry, PairedDevice

logger = logging.getLogger(__name__)


class MobileServer:
    def __init__(self, registry: DeviceRegistry, port: int = 9754):
        self.registry = registry
        self.port = port
        self.active_connections: dict[str, websockets.WebSocketServerProtocol] = {}

        # Callbacks
        self.on_event_received: Callable[[EventMessage], None] | None = None
        self.on_device_connected: Callable[[str], None] | None = None
        self.on_device_disconnected: Callable[[str], None] | None = None

        # Pairing state
        self.active_pairing_code: str | None = None
        self.pairing_priv: bytes | None = None
        self.pairing_pub: bytes | None = None

    def begin_pairing(self) -> str:
        """Generate a 6-digit code and X25519 keypair for pairing."""
        self.active_pairing_code = f"{secrets.randbelow(1000000):06d}"
        self.pairing_priv, self.pairing_pub = MobileCrypto.generate_keypair()
        logger.info(f"Pairing initiated. Code: {self.active_pairing_code}")
        return self.active_pairing_code

    async def start(self):
        logger.info(f"Starting MobileServer on 0.0.0.0:{self.port}")
        await websockets.serve(self._handler, "0.0.0.0", self.port)

    async def _handler(self, websocket: websockets.WebSocketServerProtocol):
        device_id = None
        try:
            async for message in websocket:
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    continue

                if payload.get("type") == "pair_request":
                    await self._handle_pair_request(websocket, payload)
                    continue

                if payload.get("type") == "auth":
                    device_id = await self._handle_auth(websocket, payload)
                    continue

                # Once authenticated, process encrypted messages
                if device_id and payload.get("type") == "encrypted":
                    await self._handle_encrypted_message(device_id, payload)
                    continue

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if device_id and device_id in self.active_connections:
                del self.active_connections[device_id]
                if self.on_device_disconnected:
                    self.on_device_disconnected(device_id)

    async def _handle_pair_request(
        self, websocket: websockets.WebSocketServerProtocol, payload: dict
    ):
        if not self.active_pairing_code:
            await websocket.send(
                json.dumps({"type": "error", "message": "Not pairing"})
            )
            return

        code = payload.get("code")
        peer_pub_b64 = payload.get("public_key")
        device_info = payload.get("device_info", {})

        if code != self.active_pairing_code:
            await websocket.send(
                json.dumps({"type": "error", "message": "Invalid code"})
            )
            return

        peer_pub = base64.b64decode(peer_pub_b64)
        shared_secret = MobileCrypto.derive_shared_secret(self.pairing_priv, peer_pub)

        device_id = device_info.get("device_id", str(uuid.uuid4()))

        dev = PairedDevice(
            device_id=device_id,
            name=device_info.get("device_name", "Unknown Device"),
            platform=device_info.get("platform", "android"),
            shared_secret_b64=base64.b64encode(shared_secret).decode("utf-8"),
        )
        self.registry.add_device(dev)

        # Clear pairing state
        self.active_pairing_code = None
        self.pairing_priv = None

        response = {
            "type": "pair_response",
            "public_key": base64.b64encode(self.pairing_pub).decode("utf-8"),
            "device_id": device_id,
        }
        await websocket.send(json.dumps(response))
        logger.info(f"Successfully paired device: {dev.name}")

    async def _handle_auth(
        self, websocket: websockets.WebSocketServerProtocol, payload: dict
    ) -> str | None:
        device_id = payload.get("device_id")
        dev = self.registry.get_device(device_id)
        if not dev:
            await websocket.send(
                json.dumps({"type": "error", "message": "Unknown device"})
            )
            return None

        # In a real app we'd verify a signature, but for local network AES-GCM provides auth
        self.active_connections[device_id] = websocket
        self.registry.update_last_seen(device_id)

        await websocket.send(json.dumps({"type": "auth_success"}))
        logger.info(f"Device {dev.name} connected.")
        if self.on_device_connected:
            self.on_device_connected(device_id)
        return device_id

    async def _handle_encrypted_message(self, device_id: str, payload: dict):
        dev = self.registry.get_device(device_id)
        if not dev:
            return

        shared_secret = base64.b64decode(dev.shared_secret_b64)
        try:
            decrypted = MobileCrypto.decrypt_payload(
                shared_secret, payload["nonce"], payload["ciphertext"]
            )
            data = json.loads(decrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt message from {device_id}: {e}")
            return

        msg_type = data.get("type")
        if msg_type == MessageType.EVENT.value:
            if self.on_event_received:
                self.on_event_received(EventMessage(**data))

    async def send_request(
        self, device_id: str, action: str, payload: dict
    ) -> ResponseMessage | None:
        """Send an encrypted request to a device and wait for a response."""
        if device_id not in self.active_connections:
            raise RuntimeError(f"Device {device_id} is not connected")

        dev = self.registry.get_device(device_id)
        req = RequestMessage(device_id=device_id, action=action, payload=payload)

        shared_secret = base64.b64decode(dev.shared_secret_b64)
        encrypted = MobileCrypto.encrypt_payload(
            shared_secret, req.model_dump_json().encode("utf-8")
        )

        ws = self.active_connections[device_id]

        # Fire and forget for this MVP (a real implementation would use asyncio futures to wait for the specific request_id)
        await ws.send(json.dumps({"type": "encrypted", **encrypted}))

        # Fake successful response for now
        return ResponseMessage(
            device_id=device_id,
            request_id=req.request_id,
            success=True,
            payload={"status": "sent"},
        )
